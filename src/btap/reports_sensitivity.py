from src.btap.btap_packages import BTAPPackages
from src.btap.btap_analysis import BTAPAnalysis

def sensitivity_report(excel_file=r'C:/users/plopez/Desktop/output.xlsx', pdf_output_folder="./"):
    import pandas as pd
    import seaborn as sns
    import matplotlib.pyplot as plt
    from icecream import ic
    import dataframe_image as dfi
    from fpdf import FPDF
    import numpy as np
    from io import BytesIO
    import os


    # Load data into memory as a dataframe.
    df = pd.read_excel(open(excel_file, 'rb'), sheet_name='btap_data')

    # Iterate through analysis names.
    for analysis_name in df[':analysis_name'].unique():
        pdf_output_folder = os.path.join(pdf_output_folder, analysis_name + ".pdf")
        filtered_df = df.loc[df[':analysis_name'] == 'analysis_name']
        algorithm_type = df[':algorithm_type'].unique()[0]

        if algorithm_type == 'sensitivity':


            ranked_df = rank_sensitivity_ecms(df)

            # Set up FPDF Object.
            pdf = FPDF()
            # Add Page
            pdf.add_page()
            # First Section
            pdf.start_section(name="Sensitivity", level=0, strict=True)



            # Apply styling to dataframe and save
            pdf.start_section(name="Immediate Payback", level=1, strict=True)
            print(f"Plotting Immediate Payback ")
            immediate_payback_df = ranked_df.copy()
            # immediate_payback_df = ranked_df.loc[(ranked_df['energy_savings_cost_eff'] >= 0.0)].copy()

            # Remove rows where energy savings are negative.
            # immediate_payback_df.drop( immediate_payback_df[immediate_payback_df['baseline_energy_percent_better'] <= 0].index, inplace=True)

            immediate_payback_df = immediate_payback_df.sort_values(by=['energy_savings_rank'])

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


        elif algorithm_type == "nsga2":

            # https: // stackoverflow.com / questions / 32791911 / fast - calculation - of - pareto - front - in -python

            # 'baseline_necb_tier','cost_equipment_total_cost_per_m_sq'
            optimization_column_names = ['baseline_energy_percent_better', 'cost_equipment_total_cost_per_m_sq']
            # Add column to dataframe to indicate optimal datapoints.
            df['is_on_pareto'] = get_pareto_points(np.array(df[optimization_column_names].values.tolist()))

            # Filter by pareto curve.
            pareto_df = df.loc[df['is_on_pareto'] == True].reset_index()
            bins = [-100, 0, 25, 50, 60, 1000]
            labels = ["Non-Compliant", "Tier-1", "Tier-2", "Tier-3", "Tier-4"]
            pareto_df['binned'] = pd.cut(pareto_df['baseline_energy_percent_better'], bins=bins, labels=labels)
            sns.scatterplot(x="baseline_energy_percent_better",
                            y="cost_equipment_total_cost_per_m_sq",
                            hue="binned",
                            data=pareto_df)

            plt.show()

        elif algorithm_type == "elimination":
            print("No charting support for Elimination yet.")

        elif algorithm_type == "parametric":
            print("No charting support for parametric yet.")

        elif algorithm_type == "sampling-lhs":
            print("No charting support for sampling-lhs yet.")

        elif algorithm_type == "reference":
            print("No charting support for reference yet.")

        else:
            print(f"Unsupported analysis type {algorithm_type}")

        print(f"PDF report save here:{pdf_output_folder}")






