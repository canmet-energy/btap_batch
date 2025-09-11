from pymoo.optimize import minimize
from pymoo.core.problem import ElementwiseProblem
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.operators.crossover.pntx import TwoPointCrossover
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.mutation.bitflip import BitflipMutation
from pymoo.operators.mutation.pm import PM
from pymoo.operators.sampling.rnd import IntegerRandomSampling, FloatRandomSampling
from multiprocessing.pool import ThreadPool
import botocore
import time
import logging
import traceback
import numpy as np
import tqdm
from src.btap.exceptions import FailedSimulationException
from src.btap.btap_analysis import BTAPAnalysis
# Optimization problem definition class using Pymoo


class BTAPProblem(ElementwiseProblem):
    # Inspiration for this was drawn from examples:
    #   Discrete analysis https://pymoo.org/customization/discrete_problem.html
    #   Multi-threaded evaluation
    def __init__(self,
                 # Required btap object already initialized to help run the optimization.
                 btap_optimization=None,
                 # Thread pool for parallel evaluation (if needed)
                 thread_pool=None,
                 # Variable types: 'int' for discrete, 'float' for continuous
                 variable_types=None,
                 **kwargs):
        # Make analysis object visible throughout class.
        self.btap_optimization = btap_optimization
        # Store thread pool for potential use in custom parallelization
        self.thread_pool = thread_pool
        
        # Determine variable types if not provided
        if variable_types is None:
            # Auto-detect variable types from the optimization configuration
            self.variable_types = self._detect_variable_types()
        else:
            self.variable_types = variable_types
        
        # Set up bounds and types for mixed variables
        xl, xu, vtype = self._setup_mixed_variables()

        # Initialize super with information from [':algorithm'] in input file.
        super().__init__(
            # Number of variables that are present in the yml file.
            n_var=self.btap_optimization.number_of_variables(),
            # Number of minimize_objectives in input file.
            n_obj=len(self.btap_optimization.algorithm_nsga_minimize_objectives),
            # We never have constraints.
            n_constr=0,
            # set the lower and upper bounds
            xl=xl,
            xu=xu,
            # Mixed variable types
            type_var=vtype,
            # options to parent class (not used)
            # Note if using a linter and get warning "Expected Dictionary and got Dict" This is a false positive.
            **kwargs)
    
    def _detect_variable_types(self):
        """
        Detect whether each variable should be discrete (int) or continuous (float)
        based on the variable name or configuration.
        """
        variable_types = []
        for key in self.btap_optimization.option_encoder.keys():
            # Check if the variable name suggests it should be continuous
            continuous_keywords = ['scale', 'ratio', 'factor', 'efficiency', 'conductance', 
                                 'transmittance', 'shgc', 'u_value', 'r_value']
            
            if any(keyword in key.lower() for keyword in continuous_keywords):
                variable_types.append('float')
            else:
                # Default to discrete for categorical variables
                variable_types.append('int')
                
        return variable_types
    
    def _setup_mixed_variables(self):
        """
        Set up bounds and variable types for mixed discrete/continuous optimization.
        """
        xl = []
        xu = []
        vtype = []
        
        original_xu = self.btap_optimization.x_u()
        
        for i, var_type in enumerate(self.variable_types):
            if var_type == 'float':
                # For continuous variables, use [0, 1] and we'll scale later
                xl.append(0.0)
                xu.append(1.0)
                vtype.append(float)
            else:
                # For discrete variables, use integer bounds
                xl.append(0)
                xu.append(original_xu[i])
                vtype.append(int)
        
        return xl, xu, vtype

    # This is the method that runs each simulation.
    def _evaluate(
            self,
            # x is the list of options represented as integers/floats for this particular run created by pymoo.
            x,
            # out is the placeholder for the fitness / goal functions to be minimized.
            out,
            # options to parent class (not used)
            *args,
            **kwargs):

        # Convert mixed variables to appropriate format for BTAP
        processed_x = self._process_mixed_variables(x)
        
        # Converts processed variables back into values that btap understands
        run_options = self.btap_optimization.generate_run_option_file_mixed(processed_x, self.variable_types)

        # Run simulation
        results = self.btap_optimization.run_datapoint(run_options)

        # Saves results to database if successful or not.
        self.btap_optimization.save_results_to_database(results)
        message = f'{self.btap_optimization.get_num_of_runs_completed()} simulations completed of ' \
                  f'{self.btap_optimization.max_number_of_simulations}. No. of failures = ' \
                  f'{self.btap_optimization.get_num_of_runs_failed()}'
        logging.info(message)
        self.btap_optimization.pbar.update(1)
        # Pass back objective function results.
        objectives = []
        for objective in self.btap_optimization.algorithm_nsga_minimize_objectives:
            if not (objective in results):
                raise FailedSimulationException(
                    f"Objective value {objective} not found in results of simulation: {results} in datapoint {run_options[':datapoint_id']} "
                    f"Most likely due to failure of simulation runs. Stopping optimization")
            objectives.append(results[objective])

        out["F"] = np.column_stack(objectives)
    
    def _process_mixed_variables(self, x):
        """
        Process mixed discrete/continuous variables for BTAP.
        """
        processed_x = []
        
        for i, (val, var_type) in enumerate(zip(x.tolist(), self.variable_types)):
            if var_type == 'float':
                # For continuous variables, keep as float (already normalized 0-1)
                # You may want to scale this to appropriate ranges for your specific variables
                processed_x.append(float(val))
            else:
                # For discrete variables, convert to integer with bounds checking
                int_val = int(round(val))
                # Clamp to bounds to ensure valid range
                original_xu = self.btap_optimization.x_u()
                int_val = max(0, min(int_val, original_xu[i]))
                processed_x.append(int_val)
        
        return processed_x


# Class to manage optimization analysis
class BTAPOptimization(BTAPAnalysis):
    def __init__(self,
                 analysis_config=None,
                 output_folder=None,
                 analysis_input_folder=None,
                 reference_run_df=None
                 ):
        # Run super initializer to set up default variables.
        super().__init__(analysis_config=analysis_config,
                         output_folder=output_folder,
                         analysis_input_folder=analysis_input_folder,
                         reference_run_df=reference_run_df
                         )
        self.max_number_of_simulations = None
    
    def generate_run_option_file_mixed(self, x, variable_types=None):
        """
        Enhanced version of generate_run_option_file that handles mixed discrete/continuous variables.
        
        Args:
            x: List of variable values (mix of integers and floats)
            variable_types: List of variable types ('int' or 'float')
        """
        # Create dict that will be the basis of the run_options.yml file.
        run_options = {}
        
        # Use auto-detected variable types if not provided
        if variable_types is None:
            variable_types = self._detect_variable_types()
        
        # Make sure options are the same length as the encoder.
        if len(x) != len(self.option_encoder):
            raise ValueError(f'Input length {len(x)} does not match encoder length {len(self.option_encoder)}.')

        # Iterate through keys, values, and types
        for key_name, x_option, var_type in zip(self.option_encoder.keys(), x, variable_types):
            if var_type == 'float':
                # For continuous variables, use the value directly (possibly scaled)
                run_options[key_name] = self._process_continuous_variable(key_name, x_option)
            else:
                # For discrete variables, use the encoder as before
                encoder = self.option_encoder[key_name]['encoder']
                # Ensure x_option is an integer
                int_option = int(x_option) if not isinstance(x_option, int) else x_option
                run_options[key_name] = str(encoder.inverse_transform([int_option])[0])
        
        # Add scenario identifier
        run_options[':scenario'] = 'optimize'
        
        message = f"Running Option Variables {run_options}"
        logging.info(message)
        
        # Add the constants to the run options dict.
        run_options.update(self.constants)
        
        return run_options
    
    def _detect_variable_types(self):
        """
        Detect whether each variable should be discrete (int) or continuous (float)
        based on the variable name or configuration.
        """
        variable_types = []
        for key in self.option_encoder.keys():
            # Check if the variable name suggests it should be continuous
            continuous_keywords = ['scale', 'ratio', 'factor', 'efficiency', 'conductance', 
                                 'transmittance', 'shgc', 'u_value', 'r_value']
            
            if any(keyword in key.lower() for keyword in continuous_keywords):
                variable_types.append('float')
            else:
                # Default to discrete for categorical variables
                variable_types.append('int')
                
        return variable_types
    
    def _process_continuous_variable(self, key_name, normalized_value):
        """
        Process a continuous variable from normalized [0,1] range to actual parameter range.
        
        Args:
            key_name: Variable name
            normalized_value: Value in [0,1] range
            
        Returns:
            Scaled value appropriate for the variable
        """
        # Get the original options for this variable
        original_options = None
        for key, value in self.options.items():
            if key == key_name and isinstance(value, list):
                original_options = value
                break
        
        if original_options is None:
            # Fallback: just return the normalized value
            return str(normalized_value)
        
        # If original options are numeric, interpolate between min and max
        try:
            numeric_options = [float(opt) for opt in original_options]
            min_val = min(numeric_options)
            max_val = max(numeric_options)
            # Scale from [0,1] to [min_val, max_val]
            scaled_value = min_val + normalized_value * (max_val - min_val)
            return str(scaled_value)
        except (ValueError, TypeError):
            # If not numeric, treat as discrete (fallback)
            index = int(normalized_value * (len(original_options) - 1))
            return str(original_options[index])
    
    def _create_mixed_sampling(self, variable_types):
        """
        Create a custom sampling strategy for mixed discrete/continuous variables.
        """
        from pymoo.operators.sampling.rnd import Sampling
        import numpy as np
        
        class MixedSampling(Sampling):
            def __init__(self, var_types):
                super().__init__()
                self.var_types = var_types
            
            def _do(self, problem, n_samples, **kwargs):
                X = np.zeros((n_samples, problem.n_var))
                
                for i in range(problem.n_var):
                    if self.var_types[i] == 'float':
                        # Continuous variable: random float in [xl, xu]
                        X[:, i] = np.random.random(n_samples) * (problem.xu[i] - problem.xl[i]) + problem.xl[i]
                    else:
                        # Discrete variable: random integer in [xl, xu]
                        X[:, i] = np.random.randint(problem.xl[i], problem.xu[i] + 1, n_samples)
                
                return X
        
        return MixedSampling(variable_types)

    def run(self):
        # Create required paths and folders for analysis
        self.create_paths_folders()

        message = "success"
        try:
            # Create options encoder. This method creates an object to translate variable options
            # from a list of object to a list of integers. Pymoo and most optimizers operate on floats and strings.
            # We are forcing the use of int for discrete analysis.
            self.create_options_encoder()

            # Run optimization. This will create all the input files, run and gather the results.
            self.run_analysis()

        except FailedSimulationException as err:
            message = f"Simulation(s) failed. Optimization cannot continue. Please review failed simulations to " \
                      f"determine cause of error in Excel output or if possible the simulation datapoint files. " \
                      f"\nLast failure:\n\t {err}"
            logging.error(message)
        except botocore.exceptions.SSLError as err:
            message = f"Certificate Failure. This error occurs when AWS does not trust your security certificate. " \
                      f"Either because you are using a VPN or your network is otherwise spoofing IPs. Please ensure " \
                      f"that you are not on a VPN or contact your network admin. Error: {err}"
            logging.error(message)
        except Exception as err:
            message = f"Unknown Error.{err} {traceback.format_exc()}"
            logging.error(message)
        finally:
            self.shutdown_analysis()
            return message

    def run_analysis(self):
        print(f"Running Algorithm {self.algorithm_type}")
        print(f"Number of Variables: {self.number_of_variables()}")
        print(f"Number of minima objectives: {self.number_of_minimize_objectives()}")
        print(f"Number of possible designs: {self.number_of_possible_designs}")
        max_number_of_individuals = int(self.algorithm_nsga_population) * int(
            self.algorithm_nsga_n_generations)
        if self.number_of_possible_designs < max_number_of_individuals:
            self.max_number_of_simulations = self.number_of_possible_designs
        else:
            self.max_number_of_simulations = max_number_of_individuals

            print("Starting Simulations.")

            # Get algorithm information from yml data entered by user.
            # Type: only nsga2 is supported. See options here.
            # https://pymoo.org/algorithms/nsga2.html
            pop_size = self.algorithm_nsga_population
            n_gen = self.algorithm_nsga_n_generations
            prob = self.algorithm_nsga_prob
            eta = self.algorithm_nsga_eta

            message = f'Using {self.batch.image_manager.get_threads()} threads.'
            logging.info(message)
            print(message)
            # Sometime the progress bar appears before the print statement above. This paused the execution slightly.
            time.sleep(0.01)

            # Set up progress bar tracker.
            with tqdm.tqdm(desc=f"Optimization Progress", total=self.max_number_of_simulations, colour='green') as pbar:
                # Need to make pbar available to the __evaluate method.
                self.pbar = pbar
                # Create thread pool object.
                with ThreadPool(self.batch.image_manager.get_threads()) as pool:
                    # Create pymoo problem. Pass self for helper methods and thread pool for potential parallelization.
                    problem = BTAPProblem(btap_optimization=self, thread_pool=pool)
                    
                    # Determine if we have mixed variables
                    has_continuous = any(vt == 'float' for vt in problem.variable_types)
                    has_discrete = any(vt == 'int' for vt in problem.variable_types)
                    
                    if has_continuous and has_discrete:
                        # Mixed variables - use operators that can handle both
                        sampling = self._create_mixed_sampling(problem.variable_types)
                        crossover = SBX(prob=prob, eta=eta)  # SBX can handle mixed with proper bounds
                        mutation = PM(eta=eta)  # PM can handle mixed with proper bounds
                    elif has_continuous:
                        # All continuous variables
                        sampling = FloatRandomSampling()
                        crossover = SBX(prob=prob, eta=eta)
                        mutation = PM(eta=eta)
                    else:
                        # All discrete variables
                        sampling = IntegerRandomSampling()
                        crossover = TwoPointCrossover(prob=prob)
                        mutation = BitflipMutation()
                    
                    # configure the algorithm.
                    method = NSGA2(
                        pop_size=pop_size,
                        sampling=sampling,
                        crossover=crossover,
                        mutation=mutation,
                        eliminate_duplicates=True,
                    )
                    # set to optimize minimize the problem n_gen os the max number of generations before giving up.
                    self.res = minimize(problem,
                                        method,
                                        termination=('n_gen', n_gen),
                                        seed=1
                                        )
                    # Scatter().add(res.F).show()
                    # Let the user know the runtime.
                    print('Execution Time:', self.res.exec_time)

    # convenience interface to get number of minimized objectives.
    def number_of_minimize_objectives(self):
        # Returns the number of variables Note this is not a class variable self like the others. That is because
        # this method is used in the problem definition and we need to avoid thread variable issues.
        return len(self.algorithm_nsga_minimize_objectives)
