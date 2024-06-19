from pymoo.optimize import minimize
from pymoo.core.problem import ElementwiseProblem
from pymoo.core.problem import starmap_parallelized_eval
from pymoo.factory import get_algorithm, get_crossover, get_mutation, get_sampling
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
    #   Stapmap Multi-threaded https://pymoo.org/problems/parallelization.html
    def __init__(self,
                 # Required btap object already initialized to help run the optimization.
                 btap_optimization=None,
                 **kwargs):
        # Make analysis object visible throughout class.
        self.btap_optimization = btap_optimization

        # Initialize super with information from [':algorithm'] in input file.
        super().__init__(
            # Number of variables that are present in the yml file.
            n_var=self.btap_optimization.number_of_variables(),
            # Number of minimize_objectives in input file.
            n_obj=len(self.btap_optimization.algorithm_nsga_minimize_objectives),
            # We never have constraints.
            n_constr=0,
            # set the lower bound array of variable options.. all start a zero. So an array of zeros.
            xl=[0] * self.btap_optimization.number_of_variables(),
            # the upper bound for each variable option as an integer.. We are dealing only with discrete integers in
            # this optimization.
            xu=self.btap_optimization.x_u(),
            # Tell pymoo that the variables are discrete integers and not floats as is usually the default.
            type_var=int,
            # options to parent class (not used)
            # Note if using a linter and get warning "Expected Dictionary and got Dict" This is a false positive.
            **kwargs)

    # This is the method that runs each simulation.
    def _evaluate(
            self,
            # x is the list of options represented as integers for this particular run created by pymoo.
            x,
            # out is the placeholder for the fitness / goal functions to be minimized.
            out,
            # options to parent class (not used)
            *args,
            **kwargs):

        # Converts discrete integers contains in x argument back into values that btap understands. So for example.,if
        # x was a list of zeros, it would convert this to the dict of the first item in each list of the variables in
        # the building_options section of the input yml file.
        run_options = self.btap_optimization.generate_run_option_file(x.tolist())

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


# Class to manage optimization analysis
class BTAPOptimization(BTAPAnalysis):
    def __init__(self,
                 analysis_config=None,
                 output_folder=None,
                 analysis_input_folder=None,
                 reference_run_df=None,
                 include_files=None
                 ):
        # Run super initializer to set up default variables.
        super().__init__(analysis_config=analysis_config,
                         output_folder=output_folder,
                         analysis_input_folder=analysis_input_folder,
                         reference_run_df=reference_run_df,
                         include_files=include_files
                         )
        self.max_number_of_simulations = None

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
                    # Create pymoo problem. Pass self for helper methods and set up a starmap multithread pool.
                    problem = BTAPProblem(btap_optimization=self, runner=pool.starmap,
                                          func_eval=starmap_parallelized_eval)
                    # configure the algorithm.
                    method = get_algorithm("nsga2",
                                           pop_size=pop_size,
                                           sampling=get_sampling("int_random"),
                                           crossover=get_crossover("int_sbx", prob=prob, eta=eta),
                                           mutation=get_mutation("int_pm", eta=eta),
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
