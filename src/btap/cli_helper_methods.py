import pip_system_certs.wrapt_requests
from src.btap.constants import WORKER_CONTAINER_MEMORY, WORKER_CONTAINER_STORAGE, WORKER_CONTAINER_VCPU
from src.btap.constants import MANAGER_CONTAINER_VCPU, MANAGER_CONTAINER_MEMORY, MANAGER_CONTAINER_STORAGE
from src.btap.aws_batch import AWSBatch
from src.btap.aws_compute_environment import AWSComputeEnvironment
from src.btap.aws_image_manager import AWSImageManager
from src.btap.docker_image_manager import DockerImageManager
from src.btap.aws_iam_roles import IAMBatchJobRole, IAMBatchServiceRole, IAMCodeBuildRole
from src.btap.btap_analysis import BTAPAnalysis
from src.btap.btap_reference import BTAPReference
from src.btap.btap_optimization import BTAPOptimization
from src.btap.btap_parametric import BTAPParametric
from src.btap.btap_elimination import BTAPElimination
from src.btap.btap_lhs import BTAPSamplingLHS
from src.btap.btap_sensitivity import BTAPSensitivity
from src.btap.aws_s3 import S3
from src.btap.common_paths import CommonPaths
import shutil
import time
import copy
import os
from pathlib import Path
import uuid
import numpy as np
from icecream import ic
from src.btap.aws_dynamodb import AWSResultsTable
import pandas as pd


def get_pareto_points(costs, return_mask=True):
    """
    Find the pareto-efficient points
    :param costs: An (n_points, n_costs) array
    :param return_mask: True to return a mask
    :return: An array of indices of pareto-efficient points.
        If return_mask is True, this will be an (n_points, ) boolean array
        Otherwise it will be a (n_efficient_points, ) integer array of indices.
    """
    is_efficient = np.arange(costs.shape[0])
    n_points = costs.shape[0]
    next_point_index = 0  # Next index in the is_efficient array to search for
    while next_point_index < len(costs):
        nondominated_point_mask = np.any(costs < costs[next_point_index], axis=1)
        nondominated_point_mask[next_point_index] = True
        is_efficient = is_efficient[nondominated_point_mask]  # Remove dominated points
        costs = costs[nondominated_point_mask]
        next_point_index = np.sum(nondominated_point_mask[:next_point_index]) + 1
    if return_mask:
        is_efficient_mask = np.zeros(n_points, dtype=bool)
        is_efficient_mask[is_efficient] = True
        return is_efficient_mask
    else:
        return is_efficient

def build_and_configure_docker_and_aws(btap_batch_branch=None,
                                       btap_costing_branch=None,
                                       compute_environment=None,
                                       openstudio_version=None,
                                       os_standards_branch=None):
    # build args for aws and btap_cli container.
    build_args_btap_cli = {'OPENSTUDIO_VERSION': openstudio_version,
                           'BTAP_COSTING_BRANCH': btap_costing_branch,
                           'OS_STANDARDS_BRANCH': os_standards_branch}
    # build args for btap_batch container.
    build_args_btap_batch = {'BTAP_BATCH_BRANCH': btap_batch_branch}
    if compute_environment == 'aws_batch' or compute_environment == 'all':
        # Tear down
        ace = AWSComputeEnvironment()
        image_cli = AWSImageManager(image_name='btap_cli')
        image_btap_batch = AWSImageManager(image_name='btap_batch', compute_environment=ace)

        # tear down aws_btap_cli batch framework.
        batch_cli = AWSBatch(image_manager=image_cli, compute_environment=ace)
        batch_cli.tear_down()

        # tear down aws_btap_batch batch framework.
        batch_batch = AWSBatch(image_manager=image_btap_batch, compute_environment=ace)
        batch_batch.tear_down()

        # tear down compute resources.
        ace.tear_down()

        # Delete user role permissions.
        IAMBatchJobRole().delete()
        IAMCodeBuildRole().delete()
        IAMBatchServiceRole().delete()

        # # Create new
        IAMBatchJobRole().create_role()
        IAMCodeBuildRole().create_role()
        IAMBatchServiceRole().create_role()
        time.sleep(30)  # Give a few seconds for role to apply.
        ace = AWSComputeEnvironment()
        ace.setup()
        image_cli = AWSImageManager(image_name='btap_cli')
        print('Building AWS btap_cli image')
        image_cli.build_image(build_args=build_args_btap_cli)

        image_batch = AWSImageManager(image_name='btap_batch')
        print('Building AWS btap_batch image')
        image_batch.build_image(build_args=build_args_btap_batch)

        # create aws_btap_cli batch framework.
        batch_cli = AWSBatch(image_manager=image_cli,
                             compute_environment=ace
                             )
        batch_cli.setup(container_vcpu=WORKER_CONTAINER_VCPU,
                        container_memory=WORKER_CONTAINER_MEMORY)
        # create aws_btap_batch batch framework.
        batch_batch = AWSBatch(image_manager=image_batch,
                               compute_environment=ace
                               )
        batch_batch.setup(container_vcpu=MANAGER_CONTAINER_VCPU,
                          container_memory=MANAGER_CONTAINER_MEMORY)

        # Create AWS database for results if it does not already exist.
        AWSResultsTable().create_table()

    if compute_environment == 'all' or compute_environment == 'local_docker':
        # Build btap_batch image
        image_cli = DockerImageManager(image_name='btap_cli')
        print('Building btap_cli image')
        image_cli.build_image(build_args=build_args_btap_cli)

        # # Build batch image
        # image_batch = DockerImageManager(image_name='btap_batch')
        # print('Building btap_batch image')
        # image_batch.build_image(build_args=build_args_btap_batch)


def analysis(project_input_folder=None,
             compute_environment=None,
             reference_run=None,
             output_folder=None):
    if project_input_folder.startswith('s3:'):
        # download project to local temp folder.
        local_dir = os.path.join(str(Path.home()), 'temp_analysis_folder')
        # Check if folder exists
        if os.path.isdir(local_dir):
            # Remove old folder
            try:
                shutil.rmtree(local_dir)
            except PermissionError:
                message = f'Could not delete {local_dir}. Do you have a file open in that folder? Exiting'
                print(message)
                exit(1)
        S3().download_s3_folder(s3_folder=project_input_folder, local_dir=local_dir)
        project_input_folder = local_dir
    # path of analysis input.yml
    analysis_config_file = os.path.join(project_input_folder, 'input.yml')

    if not os.path.isfile(analysis_config_file):
        print(f"input.yml file does not exist at path {analysis_config_file}")
        exit(1)
    if not os.path.isdir(project_input_folder):
        print(f"Folder does not exist at path {analysis_config_file}")
        exit(1)
    analysis_config, analysis_input_folder, analyses_folder = BTAPAnalysis.load_analysis_input_file(
        analysis_config_file=analysis_config_file)

    if compute_environment == 'local_docker' or compute_environment == 'aws_batch':
        analysis_config[':compute_environment'] = compute_environment

        reference_run_df = None
        if reference_run:
            # Run reference
            ref_analysis_config = copy.deepcopy(analysis_config)
            ref_analysis_config[':algorithm_type'] = 'reference'
            br = BTAPReference(analysis_config=ref_analysis_config,
                               analysis_input_folder=analysis_input_folder,
                               output_folder=os.path.join(output_folder))
            br.run()

            reference_run_df = br.btap_data_df

        # ic(reference_run_data_path)

        # BTAP analysis placeholder.
        ba = None

        # nsga2
        if analysis_config[':algorithm_type'] == 'nsga2':
            ba = BTAPOptimization(analysis_config=analysis_config,
                                  analysis_input_folder=analysis_input_folder,
                                  output_folder=output_folder,
                                  reference_run_df=reference_run_df)
        # parametric
        elif analysis_config[':algorithm_type'] == 'parametric':
            ba = BTAPParametric(analysis_config=analysis_config,
                                analysis_input_folder=analysis_input_folder,
                                output_folder=output_folder,
                                reference_run_df=reference_run_df)

        # parametric
        elif analysis_config[':algorithm_type'] == 'elimination':
            ba = BTAPElimination(analysis_config=analysis_config,
                                 analysis_input_folder=analysis_input_folder,
                                 output_folder=output_folder,
                                 reference_run_df=reference_run_df)

        elif analysis_config[':algorithm_type'] == 'sampling-lhs':
            ba = BTAPSamplingLHS(analysis_config=analysis_config,
                                 analysis_input_folder=analysis_input_folder,
                                 output_folder=output_folder,
                                 reference_run_df=reference_run_df)

        elif analysis_config[':algorithm_type'] == 'sensitivity':
            ba = BTAPSensitivity(analysis_config=analysis_config,
                                 analysis_input_folder=analysis_input_folder,
                                 output_folder=output_folder,
                                 reference_run_df=reference_run_df)

            # bp = BTAPSensitivity.run_sensitivity_best_packages(
            #     output_folder=ba.cp.output_folder(),
            #     project_input_folder=ba.cp.project_input_folder,
            #     df=ba.btap_data_df)
            # bp.run()
            # print(bp.btap_data_df)


        elif analysis_config[':algorithm_type'] == 'reference':
            ba = BTAPReference(analysis_config=analysis_config,
                               analysis_input_folder=analysis_input_folder,
                               output_folder=output_folder)

        else:
            print(f"Error:Analysis type {analysis_config[':algorithm_type']} not supported. Exiting.")
            exit(1)

        ba.run()

        all_df = ba.btap_data_df
        # If reference run was done, add to dataframe
        if isinstance(br.btap_data_df,pd.DataFrame):
            all_df = pd.concat([br.btap_data_df, ba.btap_data_df])

        # If Sensitivity best packages was run, add to dataframe.
        if isinstance(br.btap_data_df,pd.DataFrame):
            all_df = pd.concat([br.btap_data_df, ba.btap_data_df])



        # Save data to excel file.
        excel_path = os.path.join(ba.cp.algorithm_folder(), 'output.xlsx')
        with pd.ExcelWriter(excel_path) as writer:
            if isinstance(all_df, pd.DataFrame):
                all_df.to_excel(writer, index=False, sheet_name='btap_data')
                message = f'Saved Excel Output: {excel_path}'
                print(message)
            else:
                message = 'No simulations completed.'

        # Generate PDF
        ba.generate_pdf_report(df=all_df, pdf_output=os.path.join(ba.cp.algorithm_folder(),'results.pdf'))
        # Save data to excel file.
        excel_path = os.path.join(ba.cp.algorithm_folder(), 'output.xlsx')
        with pd.ExcelWriter(excel_path) as writer:
            if isinstance(all_df, pd.DataFrame):
                all_df.to_excel(writer, index=False, sheet_name='btap_data')
                message = f'Saved Excel Output: {excel_path}'
                print(message)
            else:
                message = 'No simulations completed.'


    if compute_environment == 'aws_batch_analysis':
        analysis_name = analysis_config[':analysis_name']
        analyses_folder = analysis_config[':analysis_name']
        # Set common paths singleton.
        cp = CommonPaths()
        # Setting paths to current context.
        cp.set_analysis_info(analysis_id=str(uuid.uuid4()),
                             analysis_name=analysis_name,
                             local_output_folder=output_folder,
                             project_input_folder=analysis_input_folder)
        # Gets an AWSAnalysisJob from AWSBatch
        batch = AWSBatch(image_manager=AWSImageManager(image_name='btap_batch'),
                         compute_environment=AWSComputeEnvironment()
                         )
        # Submit analysis job to aws.
        job = batch.create_job(job_id=analysis_name, reference_run=reference_run)
        return job.submit_job()

def list_active_analyses():
    # Gets an AWSBatch analyses object.
    ace = AWSComputeEnvironment()
    analysis_queue = AWSBatch(image_manager=AWSImageManager(image_name='btap_batch'),
                     compute_environment=ace
                     )
    return analysis_queue.get_active_jobs()


def terminate_aws_analyses():
    # Gets an AWSBatch analyses object.
    ace = AWSComputeEnvironment()
    analysis_queue = AWSBatch(image_manager=AWSImageManager(image_name='btap_batch'),
                     compute_environment=ace
                     )
    analysis_queue.clear_queue()
    batch_cli = AWSBatch(image_manager=AWSImageManager(image_name='btap_cli'), compute_environment=ace)
    batch_cli.clear_queue()


def sensitivity_chart(excel_file = None, pdf_output_folder ="./"):
    import pandas as pd
    import numpy as np
    import seaborn as sns
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    from icecream import ic
    import dataframe_image as dfi


    import time
    # Location of Excel file used from sensitivity.
    OUTPUT_XLSX = excel_file
    # Load data into memory as a dataframe.
    df = pd.read_excel(open(OUTPUT_XLSX, 'rb'), sheet_name='btap_data')
    # Gets all unique values in the scenario column.
    scenarios = df[':scenario'].unique()
    analysis_names = df[':analysis_name'].unique()

    for analysis_name in analysis_names:
        pdf_output_folder = os.path.join(pdf_output_folder,analysis_name + ".pdf")
        filtered_df = df.loc[df[':analysis_name'] == 'analysis_name']
        algorithm_type = df[':algorithm_type'].unique()[0]

        if algorithm_type == 'sensitivity':

            # This is a pdf writer.. This will save all our charts to a PDF.
            with PdfPages(pdf_output_folder) as pdf:
                # Order Measures that had the biggest impact.
                # https: // stackoverflow.com / questions / 32791911 / fast - calculation - of - pareto - front - in -python
                ranked_df = df.copy()
                #Remove rows where energy savings are negative.
                ranked_df.drop(ranked_df[ranked_df['baseline_energy_percent_better'] <= 0].index, inplace = True)

                # Use only columns for ranking.

                ranked_df["scenario_value"]  = ranked_df.values[ranked_df.index.get_indexer(ranked_df[':scenario'].index), ranked_df.columns.get_indexer(ranked_df[':scenario'])]
                ranked_df["energy_savings_per_cost"] =  ranked_df['baseline_energy_percent_better'] / ranked_df["cost_equipment_total_cost_per_m_sq"]
                ranked_df['energy_savings_rank'] = ranked_df['energy_savings_per_cost'].rank(ascending=False)
                ranked_df = ranked_df.sort_values(by=['energy_savings_rank'])
                ranked_df['ECM'] = ranked_df[':scenario']+ "=" + ranked_df["scenario_value"].astype(str)
                # Use only columns for ranking.
                ranked_df = ranked_df[['ECM',':scenario','scenario_value','energy_savings_per_cost']]





                ranked_df.plot.barh(x='ECM', y='energy_savings_per_cost')
                plt.tight_layout()
                pdf.savefig()
                plt.close()

                # Apply styling to dataframe and save
                styled_df = ranked_df.style.format({'energy_savings_per_cost': "{:.4f}"}).hide(axis="index").bar(subset=["energy_savings_per_cost", ], color='lightgreen')
                dfi.export(styled_df, 'ecm_ranked.png')


                # Iterate through all scenarios.
                for scenario in scenarios:

                    # Scatter plot

                    sns.scatterplot(
                                    x="baseline_energy_percent_better",
                                    y="cost_equipment_total_cost_per_m_sq",
                                    hue=scenario,
                                    data=df.loc[df[':scenario'] == scenario].reset_index())

                    pdf.savefig()
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
                    pdf.savefig()
                    plt.close()

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
                    pdf.savefig()
                    plt.close()

        elif algorithm_type == "nsga2":

            # https: // stackoverflow.com / questions / 32791911 / fast - calculation - of - pareto - front - in -python

            #'baseline_necb_tier','cost_equipment_total_cost_per_m_sq'
            optimization_column_names = ['baseline_energy_percent_better', 'cost_equipment_total_cost_per_m_sq']
            # Add column to dataframe to indicate optimal datapoints.
            df['is_on_pareto'] = get_pareto_points(np.array(df[optimization_column_names].values.tolist()))

            # Filter by pareto curve.
            pareto_df = df.loc[df['is_on_pareto'] == True].reset_index()
            bins = [-100, 0, 25, 50, 60, 1000]
            labels = ["Non-Compliant", "Tier-1", "Tier-2","Tier-3", "Tier-4"]
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

        print(pdf_output_folder)














