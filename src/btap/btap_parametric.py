import logging
import time
import botocore
import tqdm
import itertools
import concurrent.futures
import datetime
from src.btap.exceptions import FailedSimulationException
from src.btap.btap_analysis import BTAPAnalysis

# Class to Manage parametric runs.
class BTAPParametric(BTAPAnalysis):
    def __init__(self,
                 analysis_config=None,
                 output_folder=None,
                 analysis_input_folder=None,
                 reference_run_data_path=None
                 ):
        # Run super initializer to set up default variables.
        super().__init__(analysis_config=analysis_config,
                         output_folder=output_folder,
                         analysis_input_folder=analysis_input_folder,
                         reference_run_data_path=reference_run_data_path
                         )
        self.scenarios = []
        self.file_number = None




    def run(self):
        # Compute all the scenarios for parametric run.
        self.compute_scenarios()
        try:
            # Run parametric analysis
            self.run_all_scenarios()

        except FailedSimulationException as err:
            message = f"Simulation(s) failed. Analysis can't continue. Please review failed simulations to determine " \
                      f"cause of error in Excel output or if possible the simulation datapoint files. " \
                      f"\nLast failure had these inputs:\n\t {err}"
            print(message)
            logging.error(message)

        except botocore.exceptions.SSLError as err:
            message = f"Certificate Failure. This error occurs when AWS does not trust your security certificate. " \
                      f"Either because you are using a VPN or your network is otherwise spoofing IPs. Please ensure " \
                      f"that you are not on a VPN or contact your network admin. Error: {err}"
            print(message)
            logging.error(message)
        finally:
            self.shutdown_analysis()

    # This method will compute all the possible scenarios from the input file for a parametric run.
    # This will return a list of scenario lists.
    def compute_scenarios(self):

        # Set up storage lists
        l_of_l_of_values = []
        keys = []

        # Iterate through each option set in yml file.
        for key, value in self.options.items():
            # Check to see if the value is a list.
            # In other words are there more than one option for that characteristic.
            if isinstance(value, list):

                # Create new array to list
                new_list = []
                for item in value:
                    # Create an individual item for the option as a keyword/value array.
                    new_list.append([str(key), item])

                # Append list to the lists of options
                l_of_l_of_values.append(new_list)

                # append key to keys
                keys.append(key)

        # to compute all possible permutations done by a python package called itertools.
        scenarios = list(itertools.product(*l_of_l_of_values))
        # go through each option scenario
        for items in scenarios:
            # Create an options hash to store the options
            run_options = {}

            # Go through each item
            for item in items:
                # Save that characteristics to the options hash
                run_options[item[0]] = item[1]
            self.scenarios.append(run_options)
            message = f'Number of Scenarios {len(self.scenarios)}'
            logging.info(message)

        return self.scenarios

    def run_all_scenarios(self):
        # Failed runs counter.
        failed_datapoints = 0

        # Total number of runs.
        self.file_number = len(self.scenarios)

        # Keep track of simulation time.
        threaded_start = time.time()
        # Using all your processors minus 1.
        print(f'Using {self.batch.image_manager.get_threads()} threads.')
        time.sleep(0.01)
        with tqdm.tqdm(desc=f"Failed:{self.get_num_of_runs_failed()}: Progress Bar", total=len(self.scenarios),
                       colour='green') as pbar:
            with concurrent.futures.ThreadPoolExecutor(self.batch.image_manager.get_threads()) as executor:
                futures = []
                # go through each option scenario
                for run_options in self.scenarios:
                    # Create an options hash to store the options

                    # Executes docker simulation in a thread
                    futures.append(executor.submit(self.run_datapoint, run_options=run_options))
                # Bring simulation thread back to main thread
                for future in concurrent.futures.as_completed(futures):
                    # Save results to database.
                    job_data = future.result()
                    self.save_results_to_database(job_data)

                    # Track failures.
                    if not job_data['status'] != 'SUCCESS':
                        failed_datapoints += 1

                    # Update user.
                    message = f'TotalRuns:{self.file_number}\tCompleted:{self.get_num_of_runs_completed()}' \
                              f'\tFailed:{self.get_num_of_runs_failed()}' \
                              f'\tElapsed Time: {str(datetime.timedelta(seconds=round(time.time() - threaded_start)))}'
                    logging.info(message)
                    pbar.update(1)

        # At end of runs update for users.
        message = f'{self.file_number} Simulations completed. No. of failures = {self.get_num_of_runs_failed()} ' \
                  f'Total Time: {str(datetime.timedelta(seconds=round(time.time() - threaded_start)))}'
        logging.info(message)
        print(message)
