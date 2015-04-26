clinicceph
==========

Repo for Ceph Clinic 2014


cephntp.py

This file contains a script that creates configuration files for clknetsim
simulations and then runs the simulation. There are a number of different
possible configurations, including configurations that draw from real latency
data and ones that run multiple simulations while varying certain parameters.
Details for how to run the file and how to configure the simulations are
specified in the file comments.


clinicsimplots.py

This file contains a number of functions that analyze output from the clknetsim
simulations and produces plots and statistics about that data. It requires
data from:
    1) log.timeoffset
    2) log.ntp_offset
    3) log.ntp_maxerror
    4) log.packetdelays
which are all created by clknetsim. The filepaths need to be specified in the
file, using the global filename variables. The plots are saved in the directory
that contains clinicsimplots.py. The plots and stats that are generated are 
specified in the function comments.