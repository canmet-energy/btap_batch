from src.btap.btap_sensitivity import BTAPSensitivity
import seaborn as sns
import matplotlib.pyplot as plt
import dataframe_image as dfi
from fpdf import FPDF
import numpy as np
from io import BytesIO
import os
import pandas as pd
import pathlib
from icecream import ic

from concurrent.futures import ProcessPoolExecutor
def generate_btap_reports(data_file=None, pdf_output_folder=None, max_workers=1):
    ext = os.path.splitext(data_file)[1]
    if ext == '.csv':
        df = pd.read_csv(data_file)
    elif ext == '.xlsx':
        df = pd.read_excel(data_file)
    elif ext == '.parquet':
        df = pd.read_parquet(data_file).infer_objects()
    else:
        raise RuntimeError('File extension not recognized')

    # Ensure columns are numeric for what we are plotting.
    float_cols = ['baseline_energy_percent_better',
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
                  'baseline_difference_cost_equipment_total_cost_per_m_sq',
                  'energy_eui_cooling_gj_per_m_sq',
                  'energy_eui_heating_gj_per_m_sq',
                  'energy_eui_fans_gj_per_m_sq',
                  'energy_eui_heat recovery_gj_per_m_sq',
                  'energy_eui_interior lighting_gj_per_m_sq',
                  'energy_eui_interior equipment_gj_per_m_sq',
                  'energy_eui_water systems_gj_per_m_sq',
                  'energy_eui_pumps_gj_per_m_sq',
                  'cost_equipment_heating_and_cooling_total_cost_per_m_sq',
                  'cost_equipment_lighting_total_cost_per_m_sq',
                  'cost_equipment_shw_total_cost_per_m_sq',
                  'cost_equipment_ventilation_total_cost_per_m_sq',
                  'cost_equipment_thermal_bridging_total_cost_per_m_sq',
                  'cost_equipment_envelope_total_cost_per_m_sq'
                  ]
    for col in float_cols:
        # Make sure the col exists before casting to float.
        if col in df.columns:
            df[col] = df[col].astype('float64')

    # Gets all unique values in the scenario column.
    analysis_names = df[':analysis_name'].unique()
    dfcopy = df.copy()

    for analysis_name in analysis_names:
        print(analysis_name)
        generate_pdf(analysis_name, dfcopy, pdf_output_folder)


    # with ProcessPoolExecutor(max_workers=max_workers) as exe:
    #     for analysis_name in analysis_names:
    #         print(analysis_name)
    #         exe.submit(generate_pdf,analysis_name, dfcopy, pdf_output_folder)




def generate_pdf(analysis_name, dfcopy, pdf_output_folder):

    pdf_output_file = os.path.join(pdf_output_folder, analysis_name + ".pdf")
    filtered_df = dfcopy.loc[dfcopy[':analysis_name'] == analysis_name]
    algorithm_type = filtered_df[':algorithm_type'].unique()[0]

    if 'sensitivity' in filtered_df[':algorithm_type'].unique():
        ic(analysis_name)
        print(f"Generating BTAP report: {pdf_output_file}")
        sensitivity_report(df=filtered_df, pdf_output=pdf_output_file)
    if algorithm_type == 'nsga2':
        print(f"Generating BTAP report: {pdf_output_file}")
        nsga2_report(df=filtered_df, pdf_output=pdf_output_file)
    if algorithm_type == 'sample-lhs':
        print(f"Generating BTAP report: {pdf_output_file}")
        nsga2_report(df=filtered_df, pdf_output=pdf_output_file)


def nsga2_report(df=None,
                 pdf_output=None):
    import pathlib
    pathlib.Path(pdf_output).parent.mkdir(parents=True, exist_ok=True)
    # Filter by sensitivity type.
    df = df.copy().reset_index(drop=True)

    # Set up FPDF Object.
    pdf = FPDF()

    # Add Page
    pdf.add_page()
    # First Section
    # Iterate through all scenarios.
    for scenario in df[':scenario'].unique():
        ic(scenario)
        pdf.start_section(name=f"Appendix A: ECM {scenario}", level=0, strict=True)
        # Scatter plot
        sns.scatterplot(
            x="baseline_energy_percent_better",
            y="baseline_difference_cost_equipment_total_cost_per_m_sq",
            data=df,
            hue=scenario,
        ).set(title=pathlib.Path(pdf_output).stem)
        img_buf = BytesIO()  # Create image object
        plt.savefig(img_buf, format="svg")
        plt.legend(loc='best', frameon=False)
        pdf.image(img_buf, w=pdf.epw)
        img_buf.close()
        plt.close('all')
    pdf.output(pdf_output)


def sensitivity_report(df=None,
                       pdf_output=None,
                       ):
    import pathlib
    pathlib.Path(pdf_output).parent.mkdir(parents=True, exist_ok=True)
    # Filter by sensitivity type.
    df = df.query("`:algorithm_type` == 'sensitivity'").copy().reset_index(drop=True)

    # Set up FPDF Object.
    pdf = FPDF()

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

    # Remove ECMs that have no effect on model at all.
    costing_df = costing_df[(costing_df['baseline_energy_percent_better'] != 0.0)]
    # Sort decending of percent better.
    costing_df = costing_df.sort_values(by=['baseline_energy_percent_better'], ascending=False).reset_index(drop=True)
    #Rename column names
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

    # Create Styled Dataframe
    styled_df = costing_df.style.format()
    styled_df.hide(axis="index")
    styled_df.format(precision=2)
    headers = ["% Energy Savings",
               "% GHG Savings",
               "% Peak Savings",
               'Envelope ($/m2)',
               'Heating & Cooling ($/m2)',
               'Lighting ($/m2)',
               'SHW ($/m2)',
               'Ventilation & Ductwork ($/m2)',
               'Total ($/m2)'
               ]

    # Remove other columns not to be considered.
    headers = [x for x in headers if x not in columns_removed]

    # Remove headers if columns does not exist
    headers = [x for x in headers if x in styled_df.columns]

    styled_df.bar(subset=headers, color=['red', 'lightgreen'])
    img_buf = BytesIO()  # Create image object
    dfi.export(styled_df, img_buf, dpi=200)
    pdf.image(img_buf, w=pdf.epw)
    img_buf.close()

    # Iterate through all scenarios.
    for scenario in df[':scenario'].unique():
        ic(scenario)
        pdf.start_section(name=f"Appendix A: ECM {scenario}", level=0, strict=True)
        #Scatter plot
        g= sns.scatterplot(
            x="baseline_energy_percent_better",
            y="cost_equipment_total_cost_per_m_sq",
            hue=scenario,
            data=df.loc[df[':scenario'] == scenario].reset_index())
        g.legend(loc='best')


        img_buf = BytesIO()  # Create image object
        plt.savefig(img_buf, format="svg")
        pdf.image(img_buf, w=pdf.epw)
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
        ax.legend(loc='best')
        # Have the amount for each stack in chart.
        for c in ax.containers:
            # if the segment is small or 0, do not report zero.remove the labels parameter if it's not needed for customized labels
            labels = [round(v.get_height(), 3) if v.get_height() > 0 else '' for v in c]
            ax.bar_label(c, labels=labels, label_type='center')

        img_buf = BytesIO()  # Create image object
        plt.savefig(img_buf, format="svg")
        pdf.image(img_buf, w=pdf.epw)
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
        ax.legend(loc='best')
        # Have the amount for each stack in chart.
        for c in ax.containers:
            # if the segment is small or 0, do not report zero.remove the labels parameter if it's not needed for customized labels
            labels = [round(v.get_height(), 3) if v.get_height() > 0 else '' for v in c]
            ax.bar_label(c, labels=labels, label_type='center')
        img_buf = BytesIO()  # Create image object
        plt.savefig(img_buf, format="svg")
        pdf.image(img_buf, w=pdf.epw)
        img_buf.close()
        plt.close('all')
    pdf.output(pdf_output)

#generate_btap_reports(data_file=r'/home/plopez/btap_batch/downloads/SmallOffice_NaturalGas_YZF_sens_output.xlsx', pdf_output_folder=r'/home/plopez/btap_batch/downloads/pdf')