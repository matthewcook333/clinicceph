#!/usr/bin/env python3

import os
import subprocess
import json
import time

rootPath = "/home/ubuntu"
copyScript = rootPath + "/hmcclinic/copyfromssh.sh"
filePath = "/var/log/ntpstats"
outFolder = rootPath + "/hmcclinic/ntpdata"
logFile = "/hmcclinic/copyntpstats.log"


def main():
    serverInfoBlob = subprocess.check_output("teuthology-lock --list --all", shell=True)

    serverInfo = json.loads(bytes.decode(serverInfoBlob))

    # bound = 0
    for node in serverInfo:
        if (not node["up"] or node["is_vm"]):
            log("{} skipped -- up: {}, locked: {}, is_vm: {}".format(node["name"], node["up"], node["locked"], node["is_vm"]))
        else:
            # bound +=1
            # if (bound > 10): break
            serverName = node["name"]
            sp = subprocess.Popen([copyScript, filePath, serverName, outFolder +"/"+ serverName], 
               stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, err = sp.communicate()
            output = output + err
            log("{}: {}".format(serverName, bytes.decode(output)))

def log(msg):
    t = time.strftime("%d %b %Y %H:%M:%S", time.gmtime())
    formatted = "{} \t {}\n".format(t, msg)

    with open(rootPath + logFile, "a") as log:
        log.write(formatted)



if __name__ == "__main__":
    main()
