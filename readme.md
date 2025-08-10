# SLFJoiner
merging two SLF Files (sigma sport log file) to fix broken activities/tracks splitted by your sigma bike computer

## how to run
```sh
pip install lxml
python slfjoiner.py <inputFile1> <inputFile2> <outfile>
```

## how to use
* get Sigma Data Center and get your activities imported there (via sigma cloud)
* export the activities you want to merge as SLF files from there
* run this tool 
* import the merged SLF file into datacenter 
* delete the older activities which have been merged 

## why the hell?
* my bikecomputer (Sigma ROX 11.1 EVO) died on me once during a ride thus splitting my recorded activity/track into two parts (there is no `resume last activity ` ...)
* i wanted to join both activities to show up as one continuous activity/track incl. stats and gps-coords - so i can export the complete route to komoot
* after merging the summary-data manually (slf is just XML) I noticed that the activity was shown partly incomplete (however it was enough to export to komoot) 
* i wanted to write my first python project
* i wanted to testdrive copilot 

## known issues
* some oddity with altitude-alignment .. (i dont align the heights between the files since I have way too few datasets to fiddle around; when aligning with my current set, I get odd results)
