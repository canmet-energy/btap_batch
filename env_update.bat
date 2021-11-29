
@echo off
git pull
conda env update -p "%~dp0env" --file environment.yml --prune


