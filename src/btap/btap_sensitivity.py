import copy
import logging
from src.btap.btap_parametric import BTAPParametric
from src.btap.btap_packages import BTAPPackages
from src.btap.btap_analysis import BTAPAnalysis
import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from icecream import ic
import dataframe_image as dfi
from fpdf import FPDF
import numpy as np
from io import BytesIO
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
                                      reference_run_data_path=os.path.abspath(
                                          r"..\..\output\sensitivity_example\reference\results\output.xlsx"),
                                      sensitivity_run_data_path=os.path.abspath(
                                          r"..\..\output\sensitivity_example\sensitivity\results\output.xlsx"),
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

    @staticmethod
    def generate_pdf_report(df):

        # Set up Excel output
        writer = pd.ExcelWriter("dataframe.xlsx", engine='xlsxwriter')
        # Set up FPDF Object.
        pdf = FPDF()
        # Add Page
        pdf.add_page()
        # First Section
        pdf.start_section(name="Sensitivity", level=0, strict=True)

        # Apply styling to dataframe and save
        pdf.start_section(name="Immediate Payback", level=1, strict=True)
        print(f"Plotting Immediate Payback ")

        # Remove ECMs that have no effect on model at all.
        df = df.query(
            "baseline_ghg_percent_better != 0 and baseline_peak_electric_percent_better != 0 and baseline_energy_percent_better != 0 ")

        # Filter by sensitivity runs.
        sensitivity_df = BTAPSensitivity.rank_sensitivity_ecms(
            df.query("`:algorithm_type` == 'sensitivity'").copy().reset_index())
        sensitivity_df = sensitivity_df[[
            ':scenario',
            'scenario_value',
            'energy_savings_rank',
            'energy_savings_cost_eff_rank',
            'baseline_energy_percent_better',
            'ghg_savings_rank',
            'ghg_savings_cost_eff_rank',
            'baseline_ghg_percent_better',
            'peak_shaving_rank',
            'peak_shaving_cost_eff_rank',
            'baseline_peak_electric_percent_better',
            'baseline_difference_cost_equipment_total_cost_per_m_sq'
        ]].copy()
        sensitivity_df = sensitivity_df.sort_values(by=['energy_savings_rank'])

        # Energy Table
        energy_df = sensitivity_df[[':scenario',
                                    'scenario_value',
                                    'energy_savings_rank',
                                    'energy_savings_cost_eff_rank',
                                    'baseline_energy_percent_better',
                                    'baseline_difference_cost_equipment_total_cost_per_m_sq'
                                    ]].copy()
        energy_df = energy_df.sort_values(by=['energy_savings_rank'])
        energy_df.to_excel(writer, sheet_name='energy_rankings', index=False)

        # GHG Table
        ghg_df = sensitivity_df[[':scenario',
                                 'scenario_value',
                                 'ghg_savings_rank',
                                 'ghg_savings_cost_eff_rank',
                                 'baseline_ghg_percent_better',
                                 'baseline_difference_cost_equipment_total_cost_per_m_sq'

                                 ]].copy()
        ghg_df = ghg_df.sort_values(by=['ghg_savings_rank'])
        ghg_df.to_excel(writer, sheet_name='ghg_rankings', index=False)

        # Peak Table
        peak_df = sensitivity_df[[':scenario',
                                  'scenario_value',
                                  'peak_shaving_rank',
                                  'peak_shaving_cost_eff_rank',
                                  'baseline_peak_electric_percent_better',
                                  'baseline_difference_cost_equipment_total_cost_per_m_sq'
                                  ]].copy()
        peak_df = peak_df.sort_values(by=['peak_shaving_rank'])
        peak_df.to_excel(writer, sheet_name='peak_rankings', index=False)

        reference_df = df.query("`:algorithm_type` == 'reference'").copy().reset_index()
        sensitivity_best_packages_df = df.query("`:algorithm_type` == 'sensitivity_best_packages'").copy().reset_index()

        reference_df.to_excel(writer, sheet_name='reference', index=False)
        sensitivity_best_packages_df.to_excel(writer, sheet_name='packages', index=False)
        writer.close()

        exit(1)

        immediate_payback_df.rename(columns={
            'baseline_difference_cost_equipment_total_cost_per_m_sq': 'ECM Net Capital Savings ($/m2)',
            ':scenario': 'Measure Name',
            'scenario_value': 'Measure Value',
            'baseline_energy_percent_better': 'Energy Reduction (%)',
            'cost_utility_ghg_total_kg_per_m_sq': 'Carbon (kg/m2)',
            'energy_eui_electricity_gj_per_m_sq': 'Electricity (GJ/m2)',
            'energy_eui_natural_gas_gj_per_m_sq': 'Natural Gas (GJ/m2)'

        }, inplace=True)

        # Sort by energy savings ranks and keep the first one of each ecm type.
        # immediate_payback_df = immediate_payback_df.sort_values(['energy_savings_rank'], ascending=True).groupby('Measure Name').head(1)
        immediate_payback_df = immediate_payback_df.sort_values(by=['Energy Reduction (%)'], ascending=False)

        immediate_payback_df.to_excel("panda.xlsx")
        styled_df = immediate_payback_df.style.format({
            'ECM Net Capital Savings ($/m2)': "{:.2f}",
            'Energy Reduction (%)': "{:.1f}",
            'Carbon (kg/m2)': "{:.2f}",
            'Electricity (GJ/m2)': "{:.2f}",
            'Natural Gas (GJ/m2)': "{:.2f}"

        }).hide(axis="index").bar(subset=["Energy Reduction (%)", ], color='lightgreen')
        img_buf = BytesIO()  # Create image object
        dfi.export(styled_df, img_buf, dpi=200)
        pdf.image(img_buf, w=pdf.epw / 2)
        img_buf.close()

        # ECM Ranked Styled Table.
        pdf.start_section(name="Ranked ECMs", level=1, strict=True)
        print(f"Plotting Ranked ECMs ")
        payback_df = ranked_df.loc[(ranked_df['energy_savings_cost_eff'] < 0.0)].copy()
        # Remove rows where energy savings are negative.
        payback_df.drop(payback_df[payback_df['baseline_energy_percent_better'] <= 0].index, inplace=True)

        payback_df.rename(columns={
            'baseline_difference_cost_equipment_total_cost_per_m_sq': 'ECM Net Capital Cost ($/m2)',
            ':scenario': 'Measure Name',
            'scenario_value': 'Measure Value',
            'baseline_energy_percent_better': 'Energy Reduction (%)',
            'cost_utility_ghg_total_kg_per_m_sq': 'Carbon (kg/m2)',
            'energy_eui_electricity_gj_per_m_sq': 'Electricity (GJ/m2)',
            'energy_eui_natural_gas_gj_per_m_sq': 'Natural Gas (GJ/m2)'

        }, inplace=True)

        payback_df['energy_savings_cost_eff'] = payback_df[
            'energy_savings_cost_eff'].apply(lambda x: x * -1.0)
        payback_df['ECM Net Capital Cost ($/m2)'] = payback_df['ECM Net Capital Cost ($/m2)'].apply(
            lambda x: x * -1.0)
        payback_df = payback_df.sort_values(by=['energy_savings_cost_eff'], ascending=False)
        styled_df = payback_df.style.format({
            'energy_savings_cost_eff': "{:.2f}",
            'ECM Net Capital Cost ($/m2)': "{:.2f}",
            'Energy Reduction (%)': "{:.1f}",
            'Carbon (kg/m2)': "{:.2f}",
            'Electricity (GJ/m2)': "{:.2f}",
            'Natural Gas (GJ/m2)': "{:.2f}"

        }).hide(axis="index").bar(subset=["energy_savings_cost_eff", ], color='lightgreen')
        img_buf = BytesIO()  # Create image object
        dfi.export(styled_df, img_buf, dpi=400)
        pdf.image(img_buf, w=pdf.epw / 2)
        img_buf.close()

        pdf.start_section(name="Appendix A: ECM Results", level=0, strict=True)

        # Iterate through all scenarios.
        # for scenario in scenarios:
        #     print(f"Plotting scenario: {scenario} ")
        #     pdf.start_section(name=f"Appendix A: ECM {scenario}", level=1, strict=True)
        #
        #     # Scatter plot
        #
        #     sns.scatterplot(
        #                     x="baseline_energy_percent_better",
        #                     y="cost_equipment_total_cost_per_m_sq",
        #                     hue=scenario,
        #                     data=df.loc[df[':scenario'] == scenario].reset_index())
        #
        #     img_buf = BytesIO()  # Create image object
        #     plt.savefig(img_buf, format="svg")
        #     pdf.image(img_buf, w=pdf.epw / 2)
        #     img_buf.close()
        #     plt.close('all')
        #
        #
        #
        #
        #     ## Stacked EUI chart.
        #     # Filter Table rows by scenario. Save it to a new df named filtered_df.
        #     filtered_df = df.loc[df[':scenario'] == scenario].reset_index()
        #     # Filter the table to contain only these columns.
        #     # List of columns to use for EUI sensitivity.
        #     columns_to_use = [
        #         scenario,
        #         'energy_eui_cooling_gj_per_m_sq',
        #         'energy_eui_heating_gj_per_m_sq',
        #         'energy_eui_fans_gj_per_m_sq',
        #         'energy_eui_heat recovery_gj_per_m_sq',
        #         'energy_eui_interior lighting_gj_per_m_sq',
        #         'energy_eui_interior equipment_gj_per_m_sq',
        #         'energy_eui_water systems_gj_per_m_sq',
        #         'energy_eui_pumps_gj_per_m_sq'
        #     ]
        #     filtered_df = filtered_df[columns_to_use]
        #     # Set Scenario Col as String. This makes it easier to plot on the x-axis of the stacked bar chart.
        #     filtered_df[scenario] = filtered_df[scenario].astype(str)
        #     # Sort order of Scenarios in accending order.
        #     filtered_df = filtered_df.sort_values(scenario)
        #     # Plot EUI stacked chart.
        #     ax = filtered_df.plot(
        #         x=scenario,  # The column name used as the x component of the chart.
        #         kind='bar',
        #         stacked=True,
        #         title=f"Sensitivity of {scenario} by EUI ",
        #         figsize=(16, 12),
        #         rot=0,
        #         xlabel=scenario,  # Use the column name as the X label.
        #         ylabel='GJ/M2')
        #     # Have the amount for each stack in chart.
        #     for c in ax.containers:
        #         # if the segment is small or 0, do not report zero.remove the labels parameter if it's not needed for customized labels
        #         labels = [round(v.get_height(), 3) if v.get_height() > 0 else '' for v in c]
        #         ax.bar_label(c, labels=labels, label_type='center')
        #
        #
        #
        #     img_buf = BytesIO()  # Create image object
        #     plt.savefig(img_buf, format="svg")
        #     pdf.image(img_buf, w=pdf.epw / 2)
        #     img_buf.close()
        #     plt.close('all')
        #
        #     ## Stacked Costing Chart.
        #     # Filter Table rows by scenario. Save it to a new df named filtered_df.
        #     filtered_df = df.loc[df[':scenario'] == scenario].reset_index()
        #     # Filter the table to contain only these columns.
        #     # List of columns that make up costing stacked totals.
        #     columns_to_use = [
        #         scenario,
        #         'cost_equipment_heating_and_cooling_total_cost_per_m_sq',
        #         'cost_equipment_lighting_total_cost_per_m_sq',
        #         'cost_equipment_shw_total_cost_per_m_sq',
        #         'cost_equipment_ventilation_total_cost_per_m_sq',
        #         'cost_equipment_thermal_bridging_total_cost_per_m_sq',
        #         'cost_equipment_envelope_total_cost_per_m_sq'
        #
        #     ]
        #     filtered_df = filtered_df[columns_to_use]
        #     # Set Scenario Col as String. This makes it easier to plot on the x-axis of the stacked bar.
        #     filtered_df[scenario] = filtered_df[scenario].astype(str)
        #     # Sort order of Scenarios in accending order.
        #     filtered_df = filtered_df.sort_values(scenario)
        #     # Plot chart.
        #     ax = filtered_df.plot(
        #         x=scenario,
        #         kind='bar',
        #         stacked=True,
        #         title=f"Sensitivity of {scenario} by Costing ",
        #         figsize=(16, 12),
        #         rot=0,
        #         xlabel=scenario,
        #         ylabel='$/M2')
        #     # Have the amount for each stack in chart.
        #     for c in ax.containers:
        #         # if the segment is small or 0, do not report zero.remove the labels parameter if it's not needed for customized labels
        #         labels = [round(v.get_height(), 3) if v.get_height() > 0 else '' for v in c]
        #         ax.bar_label(c, labels=labels, label_type='center')
        #     img_buf = BytesIO()  # Create image object
        #     plt.savefig(img_buf, format="svg")
        #     pdf.image(img_buf, w=pdf.epw / 2)
        #     img_buf.close()
        #     plt.close('all')
        #
        #
        pdf.output("panda.pdf")


df = pd.read_excel(r'C:\Users\plopez\btap_batch\output\sensitivity_example\output.xlsx', index_col=0)
BTAPSensitivity.generate_pdf_report(df)
