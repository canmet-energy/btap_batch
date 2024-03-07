from src.btap.btap_analysis import BTAPAnalysis
import copy
import logging
from src.btap.btap_parametric import BTAPParametric
class BTAPPackages(BTAPParametric):

    def add_packages(self, packages = None):
        # Create default options scenario. Uses first value of all arrays.
        for run_option in packages:
            run_option[':algorithm_type'] = 'sensitivity_best_packages'
            self.scenarios.append(run_option)

    def compute_scenarios(self):
        message = f'Number of Scenarios {len(self.scenarios)}'
        logging.info(message)
        return self.scenarios


# Class to manage Sensitivity analysis
class BTAPSensitivity(BTAPParametric):
    def compute_scenarios(self):
        # Create default options scenario. Uses first value of all arrays.
        default_options = copy.deepcopy(self.options)
        for key, value in self.options.items():
            default_options[key] = value[0]
        # Create scenario
        for key, value in self.options.items():
            # If more than one option. Iterate, create run_option for each one.
            if isinstance(value, list) and len(value) > 1:
                for item in value:
                    run_option = copy.deepcopy(default_options)
                    run_option[':algorithm_type'] = self.algorithm_type
                    run_option[key] = item
                    run_option[':scenario'] = key
                    # append scenario to list.
                    self.scenarios.append(run_option)
        message = f'Number of Scenarios {len(self.scenarios)}'
        logging.info(message)
        return self.scenarios

    @staticmethod
    def rank_sensitivity_ecms(df):

        # Create copy of dataframe.
        ranked_df = df.copy()

        # Get the value used for each sensitivity scenario and store it in a new column.
        ranked_df["scenario_value"] = ranked_df.values[
            ranked_df.index.get_indexer(ranked_df[':scenario'].index), ranked_df.columns.get_indexer(
                ranked_df[':scenario'])]

        # Rank ecms.
        ranked_df['energy_savings_rank'] = ranked_df['energy_eui_total_gj_per_m_sq'].rank(ascending=True)
        ranked_df['ghg_savings_rank'] = ranked_df['cost_utility_ghg_total_kg_per_m_sq'].rank(ascending=True)
        ranked_df['peak_shaving_rank'] = ranked_df['energy_peak_electric_w_per_m_sq'].rank(ascending=True)

        return ranked_df

    @staticmethod
    def run_sensitivity_best_packages(
                                      output_folder=None,
                                      project_input_folder=None,
                                      df = None,
                                      compute_environment='local'):
        import pandas as pd
        import os

        # Filter by sensitivity type.
        sensitivity_df = df.query("`:algorithm_type` == 'sensitivity'").copy().reset_index(drop=True)

        reference_run_df = df.query("`:algorithm_type` == 'reference'").copy().reset_index(drop=True)

        # Rank the results.
        ranked_df = BTAPSensitivity.rank_sensitivity_ecms(sensitivity_df)
        # Create packages
        package_names = [
            'energy_savings_rank',
            'ghg_savings_rank',
            'peak_shaving_rank',
        ]
        # Get information from sensitivity input.yml
        analysis_config, analysis_input_folder, analyses_folder = BTAPAnalysis.load_analysis_input_file(
            analysis_config_file=os.path.join(project_input_folder, 'input.yml'))

        baseline_options_list = analysis_config[':options']
        baseline_options = dict()
        for item in baseline_options_list.items():
            baseline_options[item[0]] = item[1][0]

        best_packages = list()
        for package_name in package_names:
            package_df = ranked_df.sort_values([package_name], ascending=True).groupby(
                ':scenario').head(1)
            package = baseline_options.copy()
            package[':scenario'] = package_name
            for row in package_df[[':scenario', 'scenario_value']].values:
                package[row[0]] = row[1]
            best_packages.append(package)

        analysis_config, analysis_input_folder, analyses_folder = BTAPAnalysis.load_analysis_input_file(
            analysis_config_file=os.path.join(project_input_folder, 'input.yml'))

        if compute_environment == 'local' or compute_environment == 'local_managed_aws_workers':
            analysis_config[':compute_environment'] = compute_environment

        analysis_config[':algorithm_type'] = 'sensitivity_best_packages'

        print(analysis_config[':compute_environment'])

        bp = BTAPPackages(analysis_config=analysis_config,
                          analysis_input_folder=analysis_input_folder,
                          output_folder=output_folder,
                          reference_run_df=reference_run_df)
        bp.add_packages(best_packages)
        return bp

