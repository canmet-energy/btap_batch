import os
BTAP_BATCH_VERSION = '1.1.000'

# Maximum simulataneous simulations per analyses
MAX_SIMULATIONS_PER_ANALYSIS = 500
# Maximum AWS CPUS that AWS will allocate for the compute Environment.
MAX_AWS_VCPUS = 3000
# Minimum number of CPU should be set to zero.
MIN_AWS_VCPUS = 0
# Container allocated VCPU for AWS Batch
WORKER_CONTAINER_VCPU = 1
# Container allocated Memory (MB) for AWS Batch
WORKER_CONTAINER_MEMORY = 8000
# Container Storage (GB)
INSTANCE_STORAGE_SIZE_GB = 4000
# Container allocated VCPU for AWS Batch
MANAGER_CONTAINER_VCPU = 32
# Container allocated Memory (MB) for AWS Batch
MANAGER_CONTAINER_MEMORY = 128000

# Volume Type
AWS_VOLUME_TYPE = 'io2' # could be gp2,gp3,io1,io2
IOPS_VALUE = 10000 #Only used for io2 volumes.



# AWS Batch Allocation Strategy. https://docs.aws.amazon.com/batch/latest/userguide/allocation-strategies.html
AWS_BATCH_ALLOCATION_STRATEGY = 'BEST_FIT_PROGRESSIVE'
# AWS Compute instances types..setting to optimal to let AWS figure it out for me.
# https://docs.aws.amazon.com/batch/latest/userguide/create-compute-environment.html
AWS_BATCH_COMPUTE_INSTANCE_TYPES = ['m6idn.32xlarge',
                                    'm6idn.24xlarge',
                                    'm6idn.16xlarge',
                                    'm5d.24xlarge',
                                    'm5d.16xlarge']
# Using the public Amazon Linux 2 AMI to make use of overlay disk storage. Has all aws goodies already installed,
# makeing secure session manager possible, and has docker pre-installed.
AWS_BATCH_DEFAULT_IMAGE = 'ami-0a06b44c462364156'
# AWS_BATCH_DEFAULT_IMAGE = 'ami-0bef328bf875aa381'
# Location of Docker folder that contains information to build the btap image locally and on aws.
DOCKERFILES_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'Dockerfiles')
# Location of previously run baseline simulations to compare with design scenarios
BASELINE_RESULTS = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), '..', 'resources', 'reference', 'output.xlsx')
# Location of space_type library for NECB2011
NECB2011_SPACETYPE_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'resources',
                                       'space_type_library', 'NECB2011_space_types.osm')

# These resources were created either by hand or default from the AWS web console.
# If moving this to another aws account,
# recreate these 3 items in the new account. Also create s3 bucket to use named based account id like we did here.
# That should be all you need.. Ideally these should be created programmatically.
# Role used to build images on AWS Codebuild and ECR.
CLOUD_BUILD_SERVICE_ROLE = 'arn:aws:iam::834599497928:role/service-role/codebuild-test-service-role'
# Role to give permissions to jobs to run.
BATCH_JOB_ROLE = 'arn:aws:iam::834599497928:role/batchJobRole'
# Role to give permissions to batch to run.
BATCH_SERVICE_ROLE = 'arn:aws:iam::834599497928:role/service-role/AWSBatchServiceRole'
# Max Retry attemps for aws clients.
AWS_MAX_RETRIES = 90
# Dockerfile url location
DOCKERFILE_URL = 'https://raw.githubusercontent.com/canmet-energy/btap_cli/dev/Dockerfile'
RSMEANS_CURRENT_YEAR = '2024'