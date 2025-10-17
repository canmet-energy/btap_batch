# Download btap_batch and install/update python requirements

## Initial download of source code
You can download the btap_batch source code by issuing a git clone command.  The commands below will download the source-code on your C: drive. 
```bash
cd C:/
git clone https://github.com/canmet-energy/btap_batch
```

You must also create a virtual environment to run your python commands in. This must be run from in the btap_batch project folder. 
```bash
cd btap_batch
python -m venv venv
```

To enable your environment to issue commands simple type this command from within the btap_batch folder. You must do this for every new session of work with btap_batch
```bash
venv\Scripts\activate.ps1
```

You also need to install python dependencies. You can do this by issuing the pip install command
```bash
pip install -r requirements.txt
```

# Update Sourcecode
Sometimes you want to refresh your local copy to reflect changes and fixes that NRCan has done to the btap_batch. To update your local copy you can simply do the following while you are in your btap_batch folder.

First ensure that you are in btap_batch folder. If you do not see the '(venv)' in your command prompt. You are not in your venv. You can fix this by running 

```bash
venv\Scripts\activate.bat
```
The following command will pull the latest version of btap_batch from github.
```bash
git pull
```
There may have been changes to the python packages used by btap_batch.. So it is always a good idea to reinstall them with the pip command
```bash
pip install -r requirements.txt
```
You are now up-to-date!

