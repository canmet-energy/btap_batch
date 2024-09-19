## Requirements
* Windows 10 Professional version 1909 or greater 
* [Docker](https://docs.docker.com/desktop/install/windows-install/) running on your computer. Ensure that you complete creating the docker-users group on your system.
* [Python 3.9](https://www.python.org/ftp/python/3.9.13/python-3.9.13-amd64.exe) and Pip installed.  Ensure you check to install python in your PATH!
* [Git client](https://git-scm.com/downloads)
* A high speed internet connection.
* A github account and [git-token](https://docs.github.com/en/github/authenticating-to-github/creating-a-personal-access-token)
* A computer with at least 8GB+ ram and 4 or more cores (8+ threads). Preferably a powerful multi-core computer to run simulations fast locally. (24 core/48 thread with 32GB+) 
* [OpenStudio 3.7.0](https://github.com/NREL/OpenStudio/releases/tag/v3.7.0) (optional) Required to use the OpenStudio App to edit osm files.
* [OpenStudio Application 1.7.0](https://github.com/openstudiocoalition/OpenStudioApplication/releases) (optional) Required to use the OpenStudio App to edit osm files.
* If you would like to use costing and have an RSMeans account contact chris.kirney@nrcan-rncan.gc.ca for permissions to access canmet-energy repositories (For use of the btap_private_cli costing image.)
### Amazon only:
* [AWS CLI version 2 on Windows](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2-windows.html).
* [Set Up AWS credentials file](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html) . 


# Validation

This section is to ensure that you have installed the above requirements correctly. 

## Git
To ensure that git is installed. run the following command. 
```
git --version
```

You should get something like this. 
```
git version 2.38.1.windows.1
```

## Docker
Ensure that docker desktop is running on your system.  You should see it present in your windows task tray.  Then run the following command. 

```
docker run  hello-world
```

You should see the following output.

```
Unable to find image 'hello-world:latest' locally
latest: Pulling from library/hello-world
c1ec31eb5944: Pull complete
Digest: sha256:d000bc569937abbe195e20322a0bde6b2922d805332fd6d8a68b19f524b7d21d
Status: Downloaded newer image for hello-world:latest

Hello from Docker!
This message shows that your installation appears to be working correctly.

To generate this message, Docker took the following steps:
 1. The Docker client contacted the Docker daemon.
 2. The Docker daemon pulled the "hello-world" image from the Docker Hub.
    (amd64)
 3. The Docker daemon created a new container from that image which runs the
    executable that produces the output you are currently reading.
 4. The Docker daemon streamed that output to the Docker client, which sent it
    to your terminal.

To try something more ambitious, you can run an Ubuntu container with:
 $ docker run -it ubuntu bash

Share images, automate workflows, and more with a free Docker ID:
 https://hub.docker.com/

For more examples and ideas, visit:
 https://docs.docker.com/get-started/
```

## Python
To ensure that python is installed correctly, try to get the version of python via this command. 
```
python --version
```
You should get a result similar to. 
```
Python 3.9.13
```
## AWS-CLI
To ensure that you have installed AWS-CLI, try to get the version. 

```
aws --version
```

This should then show the version

```
aws-cli/2.13.22 Python/3.11.5 Windows/10 exe/AMD64 prompt/off
```
