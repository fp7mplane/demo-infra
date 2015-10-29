# Author: Sarah Wassermann <sarah.wassermann@student.ulg.ac.be>

import subprocess
from time import sleep

def checkMeasurements(measurementIDs, verbose):
    stopped = 0
    total = 0

    nbOfConsecutiveFailures = 0

    for udm in measurementIDs:
        total += 1
        while True:
            try:
                statusInfo = subprocess.check_output(['DisNETPerf/contrib/udm-status.pl', '--udm', udm])
                statusInfo = statusInfo.decode("utf-8")
                nbOfConsecutiveFailures = 0
                break
            except subprocess.CalledProcessError:
                nbOfConsecutiveFailures += 1

                # if 5 consecutive checks failed, abord
                if nbOfConsecutiveFailures == 5:
                    if verbose:
                        print ('error: Could not check measurement-status!\n')
                    return None

        runningFlags = ["'name' => 'Scheduled'", "'name' => 'Ongoing'", "'name' => 'Specified'"]
        if not any(flag in statusInfo for flag in runningFlags): # UDM finished
            stopped += 1

    return not (total - stopped > 0)
