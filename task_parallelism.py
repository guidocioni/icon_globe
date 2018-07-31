import subprocess
import sys
import time
import os

POLL_INTERVAL = 15.          # seconds between checking status of tasks
MAX_CONCURRENT =  4          

def launchTask(script):
#    print "Launching: ", script
    task = subprocess.Popen("ncl -Q " + script, shell=True, executable="/bin/bash") 
    return task
 
# ------------------------- main -----------------------------------------------
 
# get command-line args, strip out 1st element, which is the name of this script...
scripts = sys.argv[1:]

# fire off up-to MAX_CONCURRENT subprocesses...
tasks = list()
for i,script in enumerate(scripts):
    if i >= MAX_CONCURRENT:
        break
    tasks.append( launchTask(script) )

scripts = scripts[len(tasks):]  # remove those scripts we've just launched...

while len(tasks) > 0:
    finishedList = []
    for task in tasks:
         retCode = task.poll()
         if retCode != None:
             finishedList.append(task)

             # more scripts to be run?
             if len(scripts) > 0:
                 tasks.append( launchTask(scripts[0]) )
                 del scripts[0]

    for task in finishedList:
        tasks.remove(task)

    time.sleep(POLL_INTERVAL)

print "task_parallelism.py: Done!"

