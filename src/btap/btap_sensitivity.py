import copy
import logging
from src.btap.btap_parametric import BTAPParametric
#from src.btap.btap_packages import BTAPPackages
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
            print(key)
            print(value)
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
                                      compute_environment='local_docker'):
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

        if compute_environment == 'local_docker' or compute_environment == 'aws_batch':
            analysis_config[':compute_environment'] = compute_environment

        analysis_config[':algorithm_type'] = 'sensitivity_best_packages'

        print(analysis_config[':compute_environment'])

        # python ./bin/btap_batch.py run-analysis-project -p C:\Users\plopez\btap_batch\examples\sensitivity --reference_run
        bp = BTAPPackages(analysis_config=analysis_config,
                          analysis_input_folder=analysis_input_folder,
                          output_folder=output_folder,
                          reference_run_df=reference_run_df)
        bp.add_packages(best_packages)
        return bp

    @staticmethod
    def generate_pdf_report(df = None,
                            pdf_output = None,
                            ):

        # Filter by sensitivity type.
        df = df.query("`:algorithm_type` == 'sensitivity'").copy().reset_index(drop=True)

        # Set up FPDF Object.
        pdf = FPDF()

        # Set up Excel output
        writer = pd.ExcelWriter(r'C:\Users\plopez\btap_batch\dataframe.xlsx', engine='xlsxwriter')

        # Add Page
        pdf.add_page()
        # First Section
        pdf.start_section(name="Sensitivity Analysis Summary", level=0, strict=True)

        # Filter by sensitivity runs.
        ranked_df = BTAPSensitivity.rank_sensitivity_ecms(
            df.query("`:algorithm_type` == 'sensitivity'").copy().reset_index(drop=True))


        # Costing Table
        costing_df = ranked_df[[':scenario',
                               'scenario_value',
                                'baseline_energy_percent_better',
                                'baseline_ghg_percent_better',
                                'baseline_peak_electric_percent_better',
                                'npv_total_per_m_sq',
                                'bc_step_code_tedi_kwh_per_m_sq',
                                'baseline_difference_cost_equipment_envelope_total_cost_per_m_sq',
                                'baseline_difference_cost_equipment_heating_and_cooling_total_cost_per_m_sq',
                                'baseline_difference_cost_equipment_lighting_total_cost_per_m_sq',
                                'baseline_difference_cost_equipment_renewables_total_cost_per_m_sq',
                                'baseline_difference_cost_equipment_shw_total_cost_per_m_sq',
                                'baseline_difference_cost_equipment_thermal_bridging_total_cost_per_m_sq',
                                'baseline_difference_cost_equipment_ventilation_total_cost_per_m_sq',
                                'baseline_difference_cost_equipment_total_cost_per_m_sq'
                               ]].copy()

        costing_df.to_excel(writer, sheet_name='costing', index=False)


        #costing_df = costing_df.query("scenario_value != 'NECB_Default'").copy().reset_index(drop=True)
        # Remove ECMs that have no effect on model at all.
        costing_df = costing_df[(costing_df['baseline_energy_percent_better'] != 0.0) ]
        costing_df.to_excel(writer, sheet_name='costing2', index=False)


        costing_df = costing_df.sort_values(by=['baseline_energy_percent_better'],ascending=False).reset_index(drop=True)
        costing_df = costing_df.rename(columns=
                       {
                        ':scenario': 'Measure Name',
                        'scenario_value': 'Measure Value',
                        'baseline_energy_percent_better': '% Energy Savings',
                        'baseline_ghg_percent_better': '% GHG Savings',
                        'baseline_peak_electric_percent_better': '% Peak Savings',
                        'npv_total_per_m2': 'NPV ($/m2)',
                        'baseline_difference_cost_equipment_envelope_total_cost_per_m_sq': 'Envelope ($/m2)',
                        'baseline_difference_cost_equipment_thermal_bridging_total_cost_per_m_sq': 'Thermal Bridging ($/m2)',
                        'baseline_difference_cost_equipment_heating_and_cooling_total_cost_per_m_sq': 'Heating & Cooling ($/m2)',
                        'baseline_difference_cost_equipment_lighting_total_cost_per_m_sq': 'Lighting ($/m2)',
                        'baseline_difference_cost_equipment_renewables_total_cost_per_m_sq': 'Renewables ($/m2)',
                        'baseline_difference_cost_equipment_shw_total_cost_per_m_sq': 'SHW ($/m2)',
                        'baseline_difference_cost_equipment_ventilation_total_cost_per_m_sq': 'Ventilation & Ductwork ($/m2)',
                        'baseline_difference_cost_equipment_total_cost_per_m_sq': 'Total ($/m2)',
                        })
        # Remove empty columns
        columns_removed = []
        for column in costing_df:  # iterates by-name
            if costing_df[column].isna().all() or (costing_df[column] == 0).all():
                columns_removed.append(column)
        costing_df = costing_df.replace(0, np.nan).dropna(axis=1, how="all").fillna(0)




        styled_df = costing_df.style.format()
        styled_df.hide(axis="index")
        styled_df.format(precision=2)
        headers = ["% Energy Savings",
         "% GHG Savings",
         "% Peak Savings",
         'Envelope ($/m2)',
         'Thermal Bridging ($/m2)',
         'Heating & Cooling ($/m2)',
         'Lighting ($/m2)',
         'Renewables ($/m2)',
         'SHW ($/m2)',
         'Ventilation & Ductwork ($/m2)',
         'Total ($/m2)'
         ]

        # Remove
        headers = [x for x in headers if x not in columns_removed]
        print(headers)
        styled_df.bar(subset=headers,  color=['red', 'lightgreen'])

        styled_df.to_excel(writer, sheet_name='colored', index=False)




        img_buf = BytesIO()  # Create image object
        dfi.export(styled_df, img_buf, dpi=200)
        pdf.image(img_buf,w=pdf.epw)
        img_buf.close()


        writer.close()


        # Iterate through all scenarios.
        for scenario in df[':scenario'].unique():
            print(f"Plotting scenario: {scenario} ")
            pdf.start_section(name=f"Appendix A: ECM {scenario}", level=0, strict=True)

            # Scatter plot

            sns.scatterplot(
                            x="baseline_energy_percent_better",
                            y="cost_equipment_total_cost_per_m_sq",
                            hue=scenario,
                            data=df.loc[df[':scenario'] == scenario].reset_index())

            img_buf = BytesIO()  # Create image object
            plt.savefig(img_buf, format="svg")
            pdf.image(img_buf, w=pdf.epw / 2)
            img_buf.close()
            plt.close('all')




            ## Stacked EUI chart.
            # Filter Table rows by scenario. Save it to a new df named filtered_df.
            filtered_df = df.loc[df[':scenario'] == scenario].reset_index()
            # Filter the table to contain only these columns.
            # List of columns to use for EUI sensitivity.
            columns_to_use = [
                scenario,
                'energy_eui_cooling_gj_per_m_sq',
                'energy_eui_heating_gj_per_m_sq',
                'energy_eui_fans_gj_per_m_sq',
                'energy_eui_heat recovery_gj_per_m_sq',
                'energy_eui_interior lighting_gj_per_m_sq',
                'energy_eui_interior equipment_gj_per_m_sq',
                'energy_eui_water systems_gj_per_m_sq',
                'energy_eui_pumps_gj_per_m_sq'
            ]
            filtered_df = filtered_df[columns_to_use]
            # Set Scenario Col as String. This makes it easier to plot on the x-axis of the stacked bar chart.
            filtered_df[scenario] = filtered_df[scenario].astype(str)
            # Sort order of Scenarios in accending order.
            filtered_df = filtered_df.sort_values(scenario)
            # Plot EUI stacked chart.
            ax = filtered_df.plot(
                x=scenario,  # The column name used as the x component of the chart.
                kind='bar',
                stacked=True,
                title=f"Sensitivity of {scenario} by EUI ",
                figsize=(16, 12),
                rot=0,
                xlabel=scenario,  # Use the column name as the X label.
                ylabel='GJ/M2')
            # Have the amount for each stack in chart.
            for c in ax.containers:
                # if the segment is small or 0, do not report zero.remove the labels parameter if it's not needed for customized labels
                labels = [round(v.get_height(), 3) if v.get_height() > 0 else '' for v in c]
                ax.bar_label(c, labels=labels, label_type='center')



            img_buf = BytesIO()  # Create image object
            plt.savefig(img_buf, format="svg")
            pdf.image(img_buf, w=pdf.epw / 2)
            img_buf.close()
            plt.close('all')

            ## Stacked Costing Chart.
            # Filter Table rows by scenario. Save it to a new df named filtered_df.
            filtered_df = df.loc[df[':scenario'] == scenario].reset_index()
            # Filter the table to contain only these columns.
            # List of columns that make up costing stacked totals.
            columns_to_use = [
                scenario,
                'cost_equipment_heating_and_cooling_total_cost_per_m_sq',
                'cost_equipment_lighting_total_cost_per_m_sq',
                'cost_equipment_shw_total_cost_per_m_sq',
                'cost_equipment_ventilation_total_cost_per_m_sq',
                'cost_equipment_thermal_bridging_total_cost_per_m_sq',
                'cost_equipment_envelope_total_cost_per_m_sq'

            ]
            filtered_df = filtered_df[columns_to_use]
            # Set Scenario Col as String. This makes it easier to plot on the x-axis of the stacked bar.
            filtered_df[scenario] = filtered_df[scenario].astype(str)
            # Sort order of Scenarios in accending order.
            filtered_df = filtered_df.sort_values(scenario)
            # Plot chart.
            ax = filtered_df.plot(
                x=scenario,
                kind='bar',
                stacked=True,
                title=f"Sensitivity of {scenario} by Costing ",
                figsize=(16, 12),
                rot=0,
                xlabel=scenario,
                ylabel='$/M2')
            # Have the amount for each stack in chart.
            for c in ax.containers:
                # if the segment is small or 0, do not report zero.remove the labels parameter if it's not needed for customized labels
                labels = [round(v.get_height(), 3) if v.get_height() > 0 else '' for v in c]
                ax.bar_label(c, labels=labels, label_type='center')
            img_buf = BytesIO()  # Create image object
            plt.savefig(img_buf, format="svg")
            pdf.image(img_buf, w=pdf.epw / 2)
            img_buf.close()
            plt.close('all')
        pdf.output(pdf_output)




# df = pd.read_excel(r'C:\Users\plopez\btap_batch\sqi2.xlsx')
# BTAPSensitivity.generate_pdf_report(df=df)
#
# #python ./bin/btap_batch.py build-environment --btap_costing_branch sqi_394

#python bin/btap_batch.py run-analysis-project --reference_run -p C:\Users\plopez\btap_batch\examples\sensitivity

