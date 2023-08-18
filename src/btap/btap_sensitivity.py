import copy
import logging
from src.btap.btap_parametric import BTAPParametric
from src.btap.btap_packages import BTAPPackages
from src.btap.btap_analysis import BTAPAnalysis
import os

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

        # Reduce columns to the ones below to make pandas processing faster
        ranked_df = ranked_df[[
            ':scenario',
            'scenario_value',
            'baseline_energy_percent_better',
            'baseline_ghg_percent_better',
            'baseline_peak_electric_percent_better',
            'baseline_difference_cost_equipment_total_cost_per_m_sq',
            'cost_utility_ghg_total_kg_per_m_sq',
            'energy_eui_electricity_gj_per_m_sq',
            'energy_eui_natural_gas_gj_per_m_sq',
            'energy_eui_total_gj_per_m_sq',
            'energy_peak_electric_w_per_m_sq'
        ]].copy()

        # Normalize incremental cost difference.
        ranked_df["baseline_difference_cost_equipment_total_cost_per_m_sq_normalized"] = (ranked_df[
                                                                                              'baseline_difference_cost_equipment_total_cost_per_m_sq'] -
                                                                                          ranked_df[
                                                                                              'baseline_difference_cost_equipment_total_cost_per_m_sq'].min()) / (
                                                                                                 ranked_df[
                                                                                                     'baseline_difference_cost_equipment_total_cost_per_m_sq'].max() -
                                                                                                 ranked_df[
                                                                                                     'baseline_difference_cost_equipment_total_cost_per_m_sq'].min())
        # Normalizing Energy Savings, GHG and Peak Elec. and save in new columns.
        columns = ['energy_eui_total_gj_per_m_sq',
                   'energy_peak_electric_w_per_m_sq',
                   'cost_utility_ghg_total_kg_per_m_sq']
        for column in columns:
            # Save normalized values
            ranked_df[column + "_normalized"] = (ranked_df[column] - ranked_df[column].min()) / (
                    ranked_df[column].max() - ranked_df[column].min())
            # Save cost effectiveness
            ranked_df[column + "_cost_eff"] = ranked_df[column + "_normalized"] / \
                                              ranked_df[
                                                  "baseline_difference_cost_equipment_total_cost_per_m_sq_normalized"]

        # Create scale to be able to rank cost effectiveness for each target
        ranked_df["ghg_savings_cost_eff"] = ranked_df['cost_utility_ghg_total_kg_per_m_sq_normalized'] / ranked_df[
            "baseline_difference_cost_equipment_total_cost_per_m_sq_normalized"]
        ranked_df["peak_shaving_cost_eff"] = ranked_df['energy_peak_electric_w_per_m_sq_normalized'] / \
                                             ranked_df[
                                                 "baseline_difference_cost_equipment_total_cost_per_m_sq_normalized"]
        # Rank ecms.
        ranked_df['energy_savings_rank'] = ranked_df['energy_eui_total_gj_per_m_sq_normalized'].rank(ascending=True)
        ranked_df['ghg_savings_rank'] = ranked_df['cost_utility_ghg_total_kg_per_m_sq_normalized'].rank(ascending=True)
        ranked_df['peak_shaving_rank'] = ranked_df['energy_peak_electric_w_per_m_sq_normalized'].rank(ascending=True)
        ranked_df['energy_savings_cost_eff_rank'] = ranked_df['energy_eui_total_gj_per_m_sq_cost_eff'].rank(
            ascending=True)
        ranked_df['ghg_savings_cost_eff_rank'] = ranked_df['cost_utility_ghg_total_kg_per_m_sq_cost_eff'].rank(
            ascending=True)
        ranked_df['peak_shaving_cost_eff_rank'] = ranked_df['energy_peak_electric_w_per_m_sq_cost_eff'].rank(
            ascending=True)
        return ranked_df

    @staticmethod
    def run_sensitivity_best_packages(output_folder=os.path.abspath(r"..\..\output"),
                                      project_input_folder=os.path.abspath(r"..\..\examples\sensitivity"),
                                      reference_run_data_path=os.path.abspath(r"..\..\output\sensitivity_example\reference\results\output.xlsx"),
                                      sensitivity_run_data_path=os.path.abspath(r"..\..\output\sensitivity_example\sensitivity\results\output.xlsx"),
                                      compute_environment='local_docker'):
        import pandas as pd
        import os



        df = pd.read_excel(open(sensitivity_run_data_path, 'rb'), sheet_name='btap_data')
        # Rank the results.
        ranked_df = BTAPSensitivity.rank_sensitivity_ecms(df)
        # Create packages
        package_names = [
            'energy_savings_rank',
            'ghg_savings_rank',
            'peak_shaving_rank',
            'energy_savings_cost_eff_rank',
            'ghg_savings_cost_eff_rank',
            'peak_shaving_cost_eff_rank'
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

        if compute_environment == 'local_docker' or compute_environment == 'aws_batch':
            analysis_config[':compute_environment'] = compute_environment

        analysis_config[':algorithm_type'] = 'sensitivity_best_packages'

        print(analysis_config[':compute_environment'])

        # python ./bin/btap_batch.py run-analysis-project -p C:\Users\plopez\btap_batch\examples\sensitivity --reference_run
        bp = BTAPPackages(analysis_config=analysis_config,
                          analysis_input_folder=analysis_input_folder,
                          output_folder=output_folder,
                          reference_run_data_path=reference_run_data_path)
        bp.add_packages(best_packages)
        return bp

