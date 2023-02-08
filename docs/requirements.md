## Requirements
* Windows 10 Professional version 1909 or greater (As a  workaround. if you are using 1709, make sure your git repository is cloned into C:/users/your-user-name/btap_batch) Performance however will not be optimal and will not use all available ram. 
* [Docker](https://docs.docker.com/docker-for-windows/install/) running on your computer.
* A python **miniconda** environment [3.8](https://docs.conda.io/en/latest/miniconda.html). use Windows installers.
* A git [client](https://git-scm.com/downloads)
* A high speed internet connection.
* A github account and [git-token](https://docs.github.com/en/github/authenticating-to-github/creating-a-personal-access-token)
* Add the github token as a user windows/linux environment variable as GIT_API_TOKEN
* If you would like to use costing and have an RSMeans account contact chris.kirney@nrcan-rncan.gc.ca for permissions to access canmet-energy repositories (For use of the btap_private_cli costing image.)
* For AWS runs: [AWS CLI on Windows, install the AWS CLI version 2 on Windows](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2-windows.html).
* If you are an NRCan employee: [NRCan btap_dev AWS account credentials set up on your computer](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html) for Amazon HPC runs(Optional). 
* At least 8GB+ ram with 4 or more cores (8+ threads). Preferably a powerful multi-core computer to run simulations fast locally. (24 core/48 thread with 32GB+)
* [OpenStudio 3.2.1](https://github.com/NREL/OpenStudio/releases/tag/v3.2.1) (optional) Required to use the OpenStudio App and the SketchUp plugin.
* [OpenStudio App 1.2.1](https://github.com/openstudiocoalition/OpenStudioApplication/releases/tag/v1.2.1) (optional) To view BTAP models and to create custom geometry models (must have OpenStudio v3.2.1 installed first).
* [SketchUp 2021](https://help.sketchup.com/en/downloading-older-versions) (optional) To view BTAP models and create custom geometry models in SketchUp.
* [OpenStudio SketchUp Plugin 1.2.1](https://github.com/openstudiocoalition/openstudio-sketchup-plugin/releases/tag/v1.2.1) (optional) To modify OpenStudio models in SketchUp.
