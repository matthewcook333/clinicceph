#!/usr/bin/env python3

import os
import ipaddress
import subprocess

def config1(nodecount, offset, freqexpr, delayexprup, delayexprdown = "", refclockexpr = ""):

    """ Generate client configs """
    conf = ""

    for i in range(1, nodecount + 1):
        conf += "node{}_offset = {}\n".format(i, offset)
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
    script.write("start_server {} -v 2 -o log.offset -r 2000 -l 40000 \n".format(nodecount))

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

    config1(100, 0.01, "(+ 1e-6 (sum (* 1e-9 (normal))))", 
        "(+ 1e-3 (* 1e-3 (exponential)))")

    




if __name__ == "__main__":
    main()