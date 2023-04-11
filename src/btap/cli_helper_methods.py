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
from icecream import ic
from src.btap.aws_dynamodb import AWSResultsTable


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

        reference_run_data_path = None
        if reference_run:
            # Run reference
            ref_analysis_config = copy.deepcopy(analysis_config)
            ref_analysis_config[':algorithm_type'] = 'reference'
            br = BTAPReference(analysis_config=ref_analysis_config,
                               analysis_input_folder=analysis_input_folder,
                               output_folder=os.path.join(output_folder))
            br.run()

            reference_run_data_path = br.analysis_excel_results_path()

        # ic(reference_run_data_path)

        # BTAP analysis placeholder.
        ba = None

        # nsga2
        if analysis_config[':algorithm_type'] == 'nsga2':
            ba = BTAPOptimization(analysis_config=analysis_config,
                                  analysis_input_folder=analysis_input_folder,
                                  output_folder=output_folder,
                                  reference_run_data_path=reference_run_data_path)
        # parametric
        elif analysis_config[':algorithm_type'] == 'parametric':
            ba = BTAPParametric(analysis_config=analysis_config,
                                analysis_input_folder=analysis_input_folder,
                                output_folder=output_folder,
                                reference_run_data_path=reference_run_data_path)

        # parametric
        elif analysis_config[':algorithm_type'] == 'elimination':
            ba = BTAPElimination(analysis_config=analysis_config,
                                 analysis_input_folder=analysis_input_folder,
                                 output_folder=output_folder,
                                 reference_run_data_path=reference_run_data_path)

        elif analysis_config[':algorithm_type'] == 'sampling-lhs':
            ba = BTAPSamplingLHS(analysis_config=analysis_config,
                                 analysis_input_folder=analysis_input_folder,
                                 output_folder=output_folder,
                                 reference_run_data_path=reference_run_data_path)

        elif analysis_config[':algorithm_type'] == 'sensitivity':
            ba = BTAPSensitivity(analysis_config=analysis_config,
                                 analysis_input_folder=analysis_input_folder,
                                 output_folder=output_folder,
                                 reference_run_data_path=reference_run_data_path)

        elif analysis_config[':algorithm_type'] == 'reference':
            ba = BTAPReference(analysis_config=analysis_config,
                               analysis_input_folder=analysis_input_folder,
                               output_folder=output_folder)

        else:
            print(f"Error:Analysis type {analysis_config[':algorithm_type']} not supported. Exiting.")
            exit(1)

        ba.run()
        print(f"Excel results file {ba.analysis_excel_results_path()}")

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


def generate_yml(project_input_folder=None): #Sara
    import yaml
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

    # solution sets folder
    print('project_input_folder is', project_input_folder)
    os.mkdir(os.path.join(Path(project_input_folder).parent, 'solution_sets_folder'))

    # weather locations
    locations_dict = {
        'Vancouver': 'CAN_BC_Vancouver.Intl.AP.718920_CWEC2016.epw',
        'Montreal': 'CAN_QC_Montreal-Trudeau.Intl.AP.716270_CWEC2016.epw',
        'Yellowknife': 'CAN_NT_Yellowknife.AP.719360_CWEC2016.epw'
    }

    # ================================================================================================
    # case 1: (set :ecm_system_name as 'NECB_Default') & (set :primary_heating_fuel as 'NaturalGas')
    for location_name in locations_dict.keys():
        print('location_name is', location_name)
        print(locations_dict[location_name])
        for building_name in [
            'MediumOffice',
            'LargeOffice'
        ]:
            # Make a copy of anaylsis_config and use it as template to create all other .yml files
            template_yml = copy.deepcopy(analysis_config)
            # :building_type
            template_yml[':options'][':building_type'] = [building_name]
            # :epw_file
            template_yml[':options'][':epw_file'] = [locations_dict[location_name]]
            # :ecm_system_name
            template_yml[':options'][':ecm_system_name'] = [i for i in template_yml[':options'][':ecm_system_name'] if i in ['NECB_Default']] # this removes all inputs except for 'NECB_Default'
            # :primary_heating_fuel
            template_yml[':options'][':primary_heating_fuel'] = [i for i in template_yml[':options'][':primary_heating_fuel'] if i in ['NaturalGas']]
            # yml file name
            yml_file_name = template_yml[':analysis_name'].replace('_example', '') + '_' + \
                            template_yml[':options'][':building_type'][0] + '_' + \
                            location_name + '_' + \
                            template_yml[':options'][':primary_heating_fuel'][0] + '_' + \
                            template_yml[':options'][':ecm_system_name'][0]
            print('yml_file_name is', yml_file_name)
            # :analysis_name
            template_yml[':analysis_name'] = yml_file_name
            # yml file path
            os.mkdir(os.path.join(Path(project_input_folder).parent, 'solution_sets_folder', yml_file_name))
            yml_file_name = os.path.join(Path(project_input_folder).parent, 'solution_sets_folder', yml_file_name, 'input.yml')
            # save .yml file
            file = open(yml_file_name, "w")
            yaml.dump(template_yml, file)
            file.close()

        for building_name in [
            'SmallOffice',
            'PrimarySchool',
            'SecondarySchool',
            'LowriseApartment',
            'MidriseApartment',
            'HighriseApartment'
        ]:
            # Make a copy of anaylsis_config and use it as template to create all other .yml files
            template_yml = copy.deepcopy(analysis_config)
            # :building_type
            template_yml[':options'][':building_type'] = [building_name]
            # :epw_file
            template_yml[':options'][':epw_file'] = [locations_dict[location_name]]
            # :ecm_system_name
            template_yml[':options'][':ecm_system_name'] = [i for i in template_yml[':options'][':ecm_system_name'] if i in ['NECB_Default']] # this removes all inputs except for 'NECB_Default'
            # :primary_heating_fuel
            template_yml[':options'][':primary_heating_fuel'] = [i for i in template_yml[':options'][':primary_heating_fuel'] if i in ['NaturalGas']]
            # :chiller_type
            template_yml[':options'][':chiller_type'] = [i for i in template_yml[':options'][':chiller_type'] if i in ['NECB_Default']]
            # yml file name
            yml_file_name = template_yml[':analysis_name'].replace('_example', '') + '_' + \
                            template_yml[':options'][':building_type'][0] + '_' + \
                            location_name + '_' + \
                            template_yml[':options'][':primary_heating_fuel'][0] + '_' + \
                            template_yml[':options'][':ecm_system_name'][0]
            # :analysis_name
            template_yml[':analysis_name'] = yml_file_name
            # yml file path
            os.mkdir(os.path.join(Path(project_input_folder).parent, 'solution_sets_folder', yml_file_name))
            yml_file_name = os.path.join(Path(project_input_folder).parent, 'solution_sets_folder', yml_file_name, 'input.yml')
            # save .yml file
            file = open(yml_file_name, "w")
            yaml.dump(template_yml, file)
            file.close()
    #================================================================================================
    # case 2: (set :ecm_system_name as 'NECB_Default') & (set :primary_heating_fuel as 'Electricity')
    for location_name in locations_dict.keys():
        print('location_name is', location_name)
        print(locations_dict[location_name])
        for building_name in [
            'MediumOffice',
            'LargeOffice'
        ]:
            # Make a copy of anaylsis_config and use it as template to create all other .yml files
            template_yml = copy.deepcopy(analysis_config)
            # :building_type
            template_yml[':options'][':building_type'] = [building_name]
            # :epw_file
            template_yml[':options'][':epw_file'] = [locations_dict[location_name]]
            # :ecm_system_name
            template_yml[':options'][':ecm_system_name'] = [i for i in template_yml[':options'][':ecm_system_name'] if i in ['NECB_Default']] # this removes all inputs except for 'NECB_Default'
            # :primary_heating_fuel
            template_yml[':options'][':primary_heating_fuel'] = [i for i in template_yml[':options'][':primary_heating_fuel'] if i in ['Electricity']]
            # :boiler_eff
            template_yml[':options'][':boiler_eff'] = [i for i in template_yml[':options'][':boiler_eff'] if i in ['NECB_Default']]
            # :furnace_eff
            template_yml[':options'][':furnace_eff'] = [i for i in template_yml[':options'][':furnace_eff'] if i in ['NECB_Default']]
            # :shw_eff
            template_yml[':options'][':shw_eff'] = [i for i in template_yml[':options'][':shw_eff'] if i in ['NECB_Default']]
            # yml file name
            yml_file_name = template_yml[':analysis_name'].replace('_example', '') + '_' + \
                            template_yml[':options'][':building_type'][0] + '_' + \
                            location_name + '_' + \
                            template_yml[':options'][':primary_heating_fuel'][0] + '_' + \
                            template_yml[':options'][':ecm_system_name'][0]
            print('yml_file_name is', yml_file_name)
            # :analysis_name
            template_yml[':analysis_name'] = yml_file_name
            # yml file path
            os.mkdir(os.path.join(Path(project_input_folder).parent, 'solution_sets_folder', yml_file_name))
            yml_file_name = os.path.join(Path(project_input_folder).parent, 'solution_sets_folder', yml_file_name, 'input.yml')
            # save .yml file
            file = open(yml_file_name, "w")
            yaml.dump(template_yml, file)
            file.close()

        for building_name in [
            'SmallOffice',
            'PrimarySchool',
            'SecondarySchool',
            'LowriseApartment',
            'MidriseApartment',
            'HighriseApartment'
        ]:
            # Make a copy of anaylsis_config and use it as template to create all other .yml files
            template_yml = copy.deepcopy(analysis_config)
            # :building_type
            template_yml[':options'][':building_type'] = [building_name]
            # :epw_file
            template_yml[':options'][':epw_file'] = [locations_dict[location_name]]
            # :ecm_system_name
            template_yml[':options'][':ecm_system_name'] = [i for i in template_yml[':options'][':ecm_system_name'] if i in ['NECB_Default']] # this removes all inputs except for 'NECB_Default'
            # :primary_heating_fuel
            template_yml[':options'][':primary_heating_fuel'] = [i for i in template_yml[':options'][':primary_heating_fuel'] if i in ['Electricity']]
            # :chiller_type
            template_yml[':options'][':chiller_type'] = [i for i in template_yml[':options'][':chiller_type'] if i in ['NECB_Default']]
            # :boiler_eff
            template_yml[':options'][':boiler_eff'] = [i for i in template_yml[':options'][':boiler_eff'] if i in ['NECB_Default']]
            # :furnace_eff
            template_yml[':options'][':furnace_eff'] = [i for i in template_yml[':options'][':furnace_eff'] if i in ['NECB_Default']]
            # :shw_eff
            template_yml[':options'][':shw_eff'] = [i for i in template_yml[':options'][':shw_eff'] if i in ['NECB_Default']]
            # yml file name
            yml_file_name = template_yml[':analysis_name'].replace('_example', '') + '_' + \
                            template_yml[':options'][':building_type'][0] + '_' + \
                            location_name + '_' + \
                            template_yml[':options'][':primary_heating_fuel'][0] + '_' + \
                            template_yml[':options'][':ecm_system_name'][0]
            print('yml_file_name is', yml_file_name)
            # :analysis_name
            template_yml[':analysis_name'] = yml_file_name
            # yml file path
            os.mkdir(os.path.join(Path(project_input_folder).parent, 'solution_sets_folder', yml_file_name))
            yml_file_name = os.path.join(Path(project_input_folder).parent, 'solution_sets_folder', yml_file_name, 'input.yml')
            # save .yml file
            file = open(yml_file_name, "w")
            yaml.dump(template_yml, file)
            file.close()
    # ================================================================================================
    # case 3: (:ecm_system_name='HS09_CCASHP_Baseboard') & primary_heating_fuel='NaturalGas'
    for location_name in locations_dict.keys():
        print('location_name is', location_name)
        print(locations_dict[location_name])
        for building_name in [
            'MediumOffice',
            'LargeOffice',
            'SmallOffice',
            'PrimarySchool',
            'SecondarySchool',
            'LowriseApartment',
            'MidriseApartment',
            'HighriseApartment'
        ]:
            # Make a copy of anaylsis_config and use it as template to create all other .yml files
            template_yml = copy.deepcopy(analysis_config)
            # :building_type
            template_yml[':options'][':building_type'] = [building_name]
            # :epw_file
            template_yml[':options'][':epw_file'] = [locations_dict[location_name]]
            # :ecm_system_name
            template_yml[':options'][':ecm_system_name'] = [i for i in template_yml[':options'][':ecm_system_name'] if i in ['HS09_CCASHP_Baseboard']] # this removes all inputs except for 'HS09_CCASHP_Baseboard'
            # :primary_heating_fuel
            template_yml[':options'][':primary_heating_fuel'] = [i for i in template_yml[':options'][':primary_heating_fuel'] if i in ['NaturalGas']]
            # :adv_dx_units
            template_yml[':options'][':adv_dx_units'] = [i for i in template_yml[':options'][':adv_dx_units'] if i in ['NECB_Default']]
            # :chiller_type
            template_yml[':options'][':chiller_type'] = [i for i in template_yml[':options'][':chiller_type'] if i in ['NECB_Default']]
            # yml file name
            yml_file_name = template_yml[':analysis_name'].replace('_example', '') + '_' + \
                            template_yml[':options'][':building_type'][0] + '_' + \
                            location_name + '_' + \
                            template_yml[':options'][':primary_heating_fuel'][0] + '_' + \
                            template_yml[':options'][':ecm_system_name'][0]
            print('yml_file_name is', yml_file_name)
            # :analysis_name
            template_yml[':analysis_name'] = yml_file_name
            # yml file path
            os.mkdir(os.path.join(Path(project_input_folder).parent, 'solution_sets_folder', yml_file_name))
            yml_file_name = os.path.join(Path(project_input_folder).parent, 'solution_sets_folder', yml_file_name, 'input.yml')
            # save .yml file
            file = open(yml_file_name, "w")
            yaml.dump(template_yml, file)
            file.close()
    # ================================================================================================
    # case 4: :ecm_system_name='HS09_CCASHP_Baseboard' & primary_heating_fuel='Electricity'
    for location_name in locations_dict.keys():
        print('location_name is', location_name)
        print(locations_dict[location_name])
        for building_name in [
            'MediumOffice',
            'LargeOffice',
            'SmallOffice',
            'PrimarySchool',
            'SecondarySchool',
            'LowriseApartment',
            'MidriseApartment',
            'HighriseApartment'
        ]:
            # Make a copy of anaylsis_config and use it as template to create all other .yml files
            template_yml = copy.deepcopy(analysis_config)
            # :building_type
            template_yml[':options'][':building_type'] = [building_name]
            # :epw_file
            template_yml[':options'][':epw_file'] = [locations_dict[location_name]]
            # :ecm_system_name
            template_yml[':options'][':ecm_system_name'] = [i for i in template_yml[':options'][':ecm_system_name'] if i in ['HS09_CCASHP_Baseboard']] # this removes all inputs except for 'HS09_CCASHP_Baseboard'
            # :primary_heating_fuel
            template_yml[':options'][':primary_heating_fuel'] = [i for i in template_yml[':options'][':primary_heating_fuel'] if i in ['Electricity']]
            # :boiler_eff
            template_yml[':options'][':boiler_eff'] = [i for i in template_yml[':options'][':boiler_eff'] if i in ['NECB_Default']]
            # :furnace_eff
            template_yml[':options'][':furnace_eff'] = [i for i in template_yml[':options'][':furnace_eff'] if i in ['NECB_Default']]
            # :shw_eff
            template_yml[':options'][':shw_eff'] = [i for i in template_yml[':options'][':shw_eff'] if i in ['NECB_Default']]
            # :adv_dx_units
            template_yml[':options'][':adv_dx_units'] = [i for i in template_yml[':options'][':adv_dx_units'] if i in ['NECB_Default']]
            # :chiller_type
            template_yml[':options'][':chiller_type'] = [i for i in template_yml[':options'][':chiller_type'] if i in ['NECB_Default']]
            # yml file name
            yml_file_name = template_yml[':analysis_name'].replace('_example', '') + '_' + \
                            template_yml[':options'][':building_type'][0] + '_' + \
                            location_name + '_' + \
                            template_yml[':options'][':primary_heating_fuel'][0] + '_' + \
                            template_yml[':options'][':ecm_system_name'][0]
            print('yml_file_name is', yml_file_name)
            # :analysis_name
            template_yml[':analysis_name'] = yml_file_name
            # yml file path
            os.mkdir(os.path.join(Path(project_input_folder).parent, 'solution_sets_folder', yml_file_name))
            yml_file_name = os.path.join(Path(project_input_folder).parent, 'solution_sets_folder', yml_file_name, 'input.yml')
            # save .yml file
            file = open(yml_file_name, "w")
            yaml.dump(template_yml, file)
            file.close()
    # ================================================================================================
    # case 5: :ecm_system_name='HS08_CCASHP_VRF' & primary_heating_fuel='NaturalGas'
    for location_name in locations_dict.keys():
        print('location_name is', location_name)
        print(locations_dict[location_name])
        for building_name in [
            'MediumOffice',
            'LargeOffice',
            'SmallOffice',
            'PrimarySchool',
            'SecondarySchool',
            'LowriseApartment',
            'MidriseApartment',
            'HighriseApartment'
        ]:
            # Make a copy of anaylsis_config and use it as template to create all other .yml files
            template_yml = copy.deepcopy(analysis_config)
            # :building_type
            template_yml[':options'][':building_type'] = [building_name]
            # :epw_file
            template_yml[':options'][':epw_file'] = [locations_dict[location_name]]
            # :ecm_system_name
            template_yml[':options'][':ecm_system_name'] = [i for i in template_yml[':options'][':ecm_system_name'] if i in ['HS08_CCASHP_VRF']] # this removes all inputs except for 'HS08_CCASHP_VRF'
            # :primary_heating_fuel
            template_yml[':options'][':primary_heating_fuel'] = [i for i in template_yml[':options'][':primary_heating_fuel'] if i in ['NaturalGas']]
            # :adv_dx_units
            template_yml[':options'][':adv_dx_units'] = [i for i in template_yml[':options'][':adv_dx_units'] if i in ['NECB_Default']]
            # :chiller_type
            template_yml[':options'][':chiller_type'] = [i for i in template_yml[':options'][':chiller_type'] if i in ['NECB_Default']]
            # :airloop_economizer_type
            template_yml[':options'][':airloop_economizer_type'] = [i for i in template_yml[':options'][':airloop_economizer_type'] if i in ['NECB_Default']]
            # yml file name
            yml_file_name = template_yml[':analysis_name'].replace('_example', '') + '_' + \
                            template_yml[':options'][':building_type'][0] + '_' + \
                            location_name + '_' + \
                            template_yml[':options'][':primary_heating_fuel'][0] + '_' + \
                            template_yml[':options'][':ecm_system_name'][0]
            print('yml_file_name is', yml_file_name)
            # :analysis_name
            template_yml[':analysis_name'] = yml_file_name
            # yml file path
            os.mkdir(os.path.join(Path(project_input_folder).parent, 'solution_sets_folder', yml_file_name))
            yml_file_name = os.path.join(Path(project_input_folder).parent, 'solution_sets_folder', yml_file_name, 'input.yml')
            # save .yml file
            file = open(yml_file_name, "w")
            yaml.dump(template_yml, file)
            file.close()

    # ================================================================================================
    # case 6: :ecm_system_name='HS08_CCASHP_VRF' & primary_heating_fuel='Electricity'
    for location_name in locations_dict.keys():
        print('location_name is', location_name)
        print(locations_dict[location_name])
        for building_name in [
            'MediumOffice',
            'LargeOffice',
            'SmallOffice',
            'PrimarySchool',
            'SecondarySchool',
            'LowriseApartment',
            'MidriseApartment',
            'HighriseApartment'
        ]:
            # Make a copy of anaylsis_config and use it as template to create all other .yml files
            template_yml = copy.deepcopy(analysis_config)
            # :building_type
            template_yml[':options'][':building_type'] = [building_name]
            # :epw_file
            template_yml[':options'][':epw_file'] = [locations_dict[location_name]]
            # :ecm_system_name
            template_yml[':options'][':ecm_system_name'] = [i for i in template_yml[':options'][':ecm_system_name'] if i in ['HS08_CCASHP_VRF']] # this removes all inputs except for 'HS08_CCASHP_VRF'
            # :primary_heating_fuel
            template_yml[':options'][':primary_heating_fuel'] = [i for i in template_yml[':options'][':primary_heating_fuel'] if i in ['Electricity']]
            # :boiler_eff
            template_yml[':options'][':boiler_eff'] = [i for i in template_yml[':options'][':boiler_eff'] if i in ['NECB_Default']]
            # :furnace_eff
            template_yml[':options'][':furnace_eff'] = [i for i in template_yml[':options'][':furnace_eff'] if i in ['NECB_Default']]
            # :shw_eff
            template_yml[':options'][':shw_eff'] = [i for i in template_yml[':options'][':shw_eff'] if i in ['NECB_Default']]
            # :adv_dx_units
            template_yml[':options'][':adv_dx_units'] = [i for i in template_yml[':options'][':adv_dx_units'] if i in ['NECB_Default']]
            # :chiller_type
            template_yml[':options'][':chiller_type'] = [i for i in template_yml[':options'][':chiller_type'] if i in ['NECB_Default']]
            # :airloop_economizer_type
            template_yml[':options'][':airloop_economizer_type'] = [i for i in template_yml[':options'][':airloop_economizer_type'] if i in ['NECB_Default']]
            # yml file name
            yml_file_name = template_yml[':analysis_name'].replace('_example', '') + '_' + \
                            template_yml[':options'][':building_type'][0] + '_' + \
                            location_name + '_' + \
                            template_yml[':options'][':primary_heating_fuel'][0] + '_' + \
                            template_yml[':options'][':ecm_system_name'][0]
            print('yml_file_name is', yml_file_name)
            # :analysis_name
            template_yml[':analysis_name'] = yml_file_name
            # yml file path
            os.mkdir(os.path.join(Path(project_input_folder).parent, 'solution_sets_folder', yml_file_name))
            yml_file_name = os.path.join(Path(project_input_folder).parent, 'solution_sets_folder', yml_file_name, 'input.yml')
            # save .yml file
            file = open(yml_file_name, "w")
            yaml.dump(template_yml, file)
            file.close()

    # ================================================================================================
    # case 7: :ecm_system_name='HS11_ASHP_PTHP' & primary_heating_fuel='NaturalGas'
    for location_name in locations_dict.keys():
        print('location_name is', location_name)
        print(locations_dict[location_name])
        for building_name in [
            'MediumOffice',
            'LargeOffice',
            'SmallOffice',
            'PrimarySchool',
            'SecondarySchool',
            'LowriseApartment',
            'MidriseApartment',
            'HighriseApartment'
        ]:
            # Make a copy of anaylsis_config and use it as template to create all other .yml files
            template_yml = copy.deepcopy(analysis_config)
            # :building_type
            template_yml[':options'][':building_type'] = [building_name]
            # :epw_file
            template_yml[':options'][':epw_file'] = [locations_dict[location_name]]
            # :ecm_system_name
            template_yml[':options'][':ecm_system_name'] = [i for i in template_yml[':options'][':ecm_system_name'] if i in ['HS11_ASHP_PTHP']] # this removes all inputs except for 'HS11_ASHP_PTHP'
            # :primary_heating_fuel
            template_yml[':options'][':primary_heating_fuel'] = [i for i in template_yml[':options'][':primary_heating_fuel'] if i in ['NaturalGas']]
            # :boiler_eff
            template_yml[':options'][':boiler_eff'] = [i for i in template_yml[':options'][':boiler_eff'] if i in ['NECB_Default']]
            # :adv_dx_units
            template_yml[':options'][':adv_dx_units'] = [i for i in template_yml[':options'][':adv_dx_units'] if i in ['NECB_Default']]
            # :chiller_type
            template_yml[':options'][':chiller_type'] = [i for i in template_yml[':options'][':chiller_type'] if i in ['NECB_Default']]
            # :airloop_economizer_type
            template_yml[':options'][':airloop_economizer_type'] = [i for i in template_yml[':options'][':airloop_economizer_type'] if i in ['NECB_Default']]
            # yml file name
            yml_file_name = template_yml[':analysis_name'].replace('_example', '') + '_' + \
                            template_yml[':options'][':building_type'][0] + '_' + \
                            location_name + '_' + \
                            template_yml[':options'][':primary_heating_fuel'][0] + '_' + \
                            template_yml[':options'][':ecm_system_name'][0]
            print('yml_file_name is', yml_file_name)
            # :analysis_name
            template_yml[':analysis_name'] = yml_file_name
            # yml file path
            os.mkdir(os.path.join(Path(project_input_folder).parent, 'solution_sets_folder', yml_file_name))
            yml_file_name = os.path.join(Path(project_input_folder).parent, 'solution_sets_folder', yml_file_name, 'input.yml')
            # save .yml file
            file = open(yml_file_name, "w")
            yaml.dump(template_yml, file)
            file.close()

    # ================================================================================================
    # case 8: :ecm_system_name='HS11_ASHP_PTHP' & primary_heating_fuel='Electricity'
    for location_name in locations_dict.keys():
        print('location_name is', location_name)
        print(locations_dict[location_name])
        for building_name in [
            'MediumOffice',
            'LargeOffice',
            'SmallOffice',
            'PrimarySchool',
            'SecondarySchool',
            'LowriseApartment',
            'MidriseApartment',
            'HighriseApartment'
        ]:
            # Make a copy of anaylsis_config and use it as template to create all other .yml files
            template_yml = copy.deepcopy(analysis_config)
            # :building_type
            template_yml[':options'][':building_type'] = [building_name]
            # :epw_file
            template_yml[':options'][':epw_file'] = [locations_dict[location_name]]
            # :ecm_system_name
            template_yml[':options'][':ecm_system_name'] = [i for i in template_yml[':options'][':ecm_system_name'] if i in ['HS11_ASHP_PTHP']] # this removes all inputs except for 'HS11_ASHP_PTHP'
            # :primary_heating_fuel
            template_yml[':options'][':primary_heating_fuel'] = [i for i in template_yml[':options'][':primary_heating_fuel'] if i in ['Electricity']]
            # :boiler_eff
            template_yml[':options'][':boiler_eff'] = [i for i in template_yml[':options'][':boiler_eff'] if i in ['NECB_Default']]
            # :furnace_eff
            template_yml[':options'][':furnace_eff'] = [i for i in template_yml[':options'][':furnace_eff'] if i in ['NECB_Default']]
            # :shw_eff
            template_yml[':options'][':shw_eff'] = [i for i in template_yml[':options'][':shw_eff'] if i in ['NECB_Default']]
            # :adv_dx_units
            template_yml[':options'][':adv_dx_units'] = [i for i in template_yml[':options'][':adv_dx_units'] if i in ['NECB_Default']]
            # :chiller_type
            template_yml[':options'][':chiller_type'] = [i for i in template_yml[':options'][':chiller_type'] if i in ['NECB_Default']]
            # :airloop_economizer_type
            template_yml[':options'][':airloop_economizer_type'] = [i for i in template_yml[':options'][':airloop_economizer_type'] if i in ['NECB_Default']]
            # yml file name
            yml_file_name = template_yml[':analysis_name'].replace('_example', '') + '_' + \
                            template_yml[':options'][':building_type'][0] + '_' + \
                            location_name + '_' + \
                            template_yml[':options'][':primary_heating_fuel'][0] + '_' + \
                            template_yml[':options'][':ecm_system_name'][0]
            print('yml_file_name is', yml_file_name)
            # :analysis_name
            template_yml[':analysis_name'] = yml_file_name
            # yml file path
            os.mkdir(os.path.join(Path(project_input_folder).parent, 'solution_sets_folder', yml_file_name))
            yml_file_name = os.path.join(Path(project_input_folder).parent, 'solution_sets_folder', yml_file_name, 'input.yml')
            # save .yml file
            file = open(yml_file_name, "w")
            yaml.dump(template_yml, file)
            file.close()

    # ================================================================================================
    # case 9: :ecm_system_name='HS13_ASHP_VRF' & primary_heating_fuel='NaturalGas'
    for location_name in locations_dict.keys():
        print('location_name is', location_name)
        print(locations_dict[location_name])
        for building_name in [
            'MediumOffice',
            'LargeOffice',
            'SmallOffice',
            'PrimarySchool',
            'SecondarySchool',
            'LowriseApartment',
            'MidriseApartment',
            'HighriseApartment'
        ]:
            # Make a copy of anaylsis_config and use it as template to create all other .yml files
            template_yml = copy.deepcopy(analysis_config)
            # :building_type
            template_yml[':options'][':building_type'] = [building_name]
            # :epw_file
            template_yml[':options'][':epw_file'] = [locations_dict[location_name]]
            # :ecm_system_name
            template_yml[':options'][':ecm_system_name'] = [i for i in template_yml[':options'][':ecm_system_name'] if i in ['HS13_ASHP_VRF']] # this removes all inputs except for 'HS13_ASHP_VRF'
            # :primary_heating_fuel
            template_yml[':options'][':primary_heating_fuel'] = [i for i in template_yml[':options'][':primary_heating_fuel'] if i in ['NaturalGas']]
            # :adv_dx_units
            template_yml[':options'][':adv_dx_units'] = [i for i in template_yml[':options'][':adv_dx_units'] if i in ['NECB_Default']]
            # :chiller_type
            template_yml[':options'][':chiller_type'] = [i for i in template_yml[':options'][':chiller_type'] if i in ['NECB_Default']]
            # :airloop_economizer_type
            template_yml[':options'][':airloop_economizer_type'] = [i for i in template_yml[':options'][':airloop_economizer_type'] if i in ['NECB_Default']]
            # yml file name
            yml_file_name = template_yml[':analysis_name'].replace('_example', '') + '_' + \
                            template_yml[':options'][':building_type'][0] + '_' + \
                            location_name + '_' + \
                            template_yml[':options'][':primary_heating_fuel'][0] + '_' + \
                            template_yml[':options'][':ecm_system_name'][0]
            print('yml_file_name is', yml_file_name)
            # :analysis_name
            template_yml[':analysis_name'] = yml_file_name
            # yml file path
            os.mkdir(os.path.join(Path(project_input_folder).parent, 'solution_sets_folder', yml_file_name))
            yml_file_name = os.path.join(Path(project_input_folder).parent, 'solution_sets_folder', yml_file_name, 'input.yml')
            # save .yml file
            file = open(yml_file_name, "w")
            yaml.dump(template_yml, file)
            file.close()

    # ================================================================================================
    # case 10: :ecm_system_name='HS13_ASHP_VRF' & primary_heating_fuel='Electricity'
    for location_name in locations_dict.keys():
        print('location_name is', location_name)
        print(locations_dict[location_name])
        for building_name in [
            'MediumOffice',
            'LargeOffice',
            'SmallOffice',
            'PrimarySchool',
            'SecondarySchool',
            'LowriseApartment',
            'MidriseApartment',
            'HighriseApartment'
        ]:
            # Make a copy of anaylsis_config and use it as template to create all other .yml files
            template_yml = copy.deepcopy(analysis_config)
            # :building_type
            template_yml[':options'][':building_type'] = [building_name]
            # :epw_file
            template_yml[':options'][':epw_file'] = [locations_dict[location_name]]
            # :ecm_system_name
            template_yml[':options'][':ecm_system_name'] = [i for i in template_yml[':options'][':ecm_system_name'] if i in ['HS13_ASHP_VRF']] # this removes all inputs except for 'HS13_ASHP_VRF'
            # :primary_heating_fuel
            template_yml[':options'][':primary_heating_fuel'] = [i for i in template_yml[':options'][':primary_heating_fuel'] if i in ['Electricity']]
            # :boiler_eff
            template_yml[':options'][':boiler_eff'] = [i for i in template_yml[':options'][':boiler_eff'] if i in ['NECB_Default']]
            # :furnace_eff
            template_yml[':options'][':furnace_eff'] = [i for i in template_yml[':options'][':furnace_eff'] if i in ['NECB_Default']]
            # :shw_eff
            template_yml[':options'][':shw_eff'] = [i for i in template_yml[':options'][':shw_eff'] if i in ['NECB_Default']]
            # :adv_dx_units
            template_yml[':options'][':adv_dx_units'] = [i for i in template_yml[':options'][':adv_dx_units'] if i in ['NECB_Default']]
            # :chiller_type
            template_yml[':options'][':chiller_type'] = [i for i in template_yml[':options'][':chiller_type'] if i in ['NECB_Default']]
            # :airloop_economizer_type
            template_yml[':options'][':airloop_economizer_type'] = [i for i in template_yml[':options'][':airloop_economizer_type'] if i in ['NECB_Default']]
            # yml file name
            yml_file_name = template_yml[':analysis_name'].replace('_example', '') + '_' + \
                            template_yml[':options'][':building_type'][0] + '_' + \
                            location_name + '_' + \
                            template_yml[':options'][':primary_heating_fuel'][0] + '_' + \
                            template_yml[':options'][':ecm_system_name'][0]
            print('yml_file_name is', yml_file_name)
            # :analysis_name
            template_yml[':analysis_name'] = yml_file_name
            # yml file path
            os.mkdir(os.path.join(Path(project_input_folder).parent, 'solution_sets_folder', yml_file_name))
            yml_file_name = os.path.join(Path(project_input_folder).parent, 'solution_sets_folder', yml_file_name, 'input.yml')
            # save .yml file
            file = open(yml_file_name, "w")
            yaml.dump(template_yml, file)
            file.close()

    # ================================================================================================

    raise #Sara