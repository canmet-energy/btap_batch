## Troubleshooting
**Problem**: Analysis seem to fail with 'out of space' or 'cannot write' errors.

**Solution**: Sometimes docker fills either it hard disk or your system hard disk. You can check how much docker is using with this command. 
```
docker system df
```

This will produce an output that will show how full your system is. 

```
TYPE            TOTAL     ACTIVE    SIZE      RECLAIMABLE
Images          3         0         13.51GB   13.51GB (100%)
Containers      0         0         0B        0B
Local Volumes   4         0         624MB     624MB (100%)
Build Cache     0         0         0B        0B
```

You can remove the images, containers and volumes all at once with the following command. Warning! This will delete all your containers from your system. Make sure you have backed up any work to a safe location.  See [docker documentation on this](https://docs.docker.com/engine/reference/commandline/system_prune/) for more information. 
```
docker system prune -a -f --volumes
```


## Troubleshooting
**Problem**: Analysis seem to be very slow locally. Takes literally hours to run simple simulations

**Solution**: If you are using WSL in your docker setttings. You may get a performance boost by not using WSL. Go into your Docker
settings and under "General" tab, deselect the "Use the WSL2 based engine" This will force Docker to use the Hyper-V engine.  Then go to the "Resources" tab and allocate
 80% of your computers total processor capacity. The processor capacity if the number of cpu cores you have x2. 
 Similarly devote 50-80% of your Memory, keep 2GB of swap and whatever disk image size you can spare from your disk storage. I would recommend at least 200GB. 
 Apply and restart. You may have to reboot your computer and launch Docker Desktop as soon as you log in to windows. 

**Problem**: Certificate issues while working at NRCan. 

**Solution**: To fix certificate issues when using AWS from a computer at work do the following: 
* Put a proper certificate somewhere on your system. 
* Look for your AWS 'config' file (the path should be something 'C:\Users\ckirney\.aws\c') 
* Edit the 'config' file with a text editor. 
* Add "ca_bundle = <path to your certificate>" to the end of the 'config' file (e.g. on my computer I added "ca_bundle = C:\Users\ckirney\py_cert\nrcan+azure+amazon.cer") and save the changes.
* if you are on the NRCan network you can point to this file in your config folder.
```
 \\s0-ott-nas1\CETC-CTEC\BET\windows_certs\nrcan_azure_amazon.cer . 
```