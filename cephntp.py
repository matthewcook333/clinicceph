#!/usr/bin/env python3

import os
import ipaddress
import subprocess

def config1(nodecount, offset, freqexpr, delayexprup, delayexprdown = "", refclockexpr = ""):

    """ Generate client configs """
    conf = ""

    for i in range(1, nodecount + 1):
        conf += "node{}_offset = {}\n".format(i, i)
        conf += "node{}_freq = {}\n".format(i, freqexpr)
        conf += "node{}_delay1 = {}\n".format(i, delayexprup)

        if (delayexprdown != ""):
            conf += "node1_delay{} = {}\n".format(i, delayexprdown)
        else:
            conf += "node1_delay{} = {}\n".format(i, delayexprup)

        if (refclockexpr != ""):
            conf += "node{}_refclock = {}\n".format(i, refclockexpr)

    confFile = open("./tmp/conf", 'w')

    confFile.write(conf)

    confFile.close()


    scriptname = "cephntp.dynamic.test"
    createScript(nodecount, scriptname)

    subprocess.check_call("./{}".format(scriptname), 
        shell=True)



def createScript(nodecount, scriptname):

    script = open("./{}".format(scriptname), 'w')

    script.write("#!/bin/bash\n\n")

    script.write("CLKNETSIM_PATH=..\n")
    script.write(". ../clknetsim.bash\n")

    """ Start clients """
    script.write("""start_client 1 ntp "server 127.127.1.0" \n""")

    for i in range(2, nodecount + 1):
        script.write("""start_client {} ntp "server {} minpoll 6 maxpoll 6" \n"""
            .format(i, ipaddress.IPv4Address("192.168.123.1")))

    """ Start experiment """
    timeLimit = 40000

    script.write("start_server {} -v 2 -o ./tmp/log.timeoffset \
        -g ./tmp/log.rawoffset -f ./tmp/log.freqoffset -p ./tmp/log.packetdelays \
        -l {} \n".format(nodecount, timeLimit))

    """ Output statistics """
    script.write("cat tmp/stats\n")
    script.write("echo\n")
    script.write("get_stat 'RMS offset'\n")
    script.write("get_stat 'RMS frequency'\n")

    script.close()

    subprocess.check_call("chmod +x ./{}".format(scriptname), 
        shell=True)




def main():

    if (not os.path.isdir("./tmp")):
        os.mkdir("./tmp")

    # config1(100, 0.01, "(+ 1e-6 (sum (* 1e-9 (normal))))", 
    #     "(+ 1e-3 (* 1e-3 (exponential)))")

    # TODO: change offset so each node starts at a different offset
    # config1(10, 0.01, "(sum (* 2e-5 (normal)))", 
    #     "(+ 1e-4 (* 7e-3 (poisson 5)))")
    
    config1(10, 0.01, "(* 0.0001 (normal))", 
        "(+ 1e-4 (* 7e-3 (poisson 5)))")



if __name__ == "__main__":
    main()
