# Download btap_batch and install/update python requirements

## Initial download of source code
You can download the btap_batch source code by issuing a git clone command.  The commands below will download the source-code on your C: drive. 
```bash
cd C:/
git clone https://github.com/canmet-energy/btap_batch
```

You must also install [uv](https://docs.astral.sh/uv/getting-started/installation/), which manages Python and the project dependencies.
```bash
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Run btap_batch commands with `uv run` from within the btap_batch folder. On each run, uv automatically installs Python and syncs the project dependencies as needed, so no manual virtual environment setup is required.
```bash
cd btap_batch
uv run bin/btap_batch.py -h
```

# Update Sourcecode
Sometimes you want to refresh your local copy to reflect changes and fixes that NRCan has done to the btap_batch. To update your local copy you can simply do the following while you are in your btap_batch folder.

The following command will pull the latest version of btap_batch from github.
```bash
git pull
```
Any changes to the python packages used by btap_batch will be picked up automatically the next time you use `uv run`.

You are now up-to-date!

