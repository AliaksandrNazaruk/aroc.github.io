#!/bin/bash
# this statement checks if there is an instance of the EtherSenseServer running
if [[ ! `ps -eaf | grep "python home/boris/backup 06.03/realsense/server.py" | grep -v grep` ]]; then
# if not, EtherSenseServer is started with the PYTHONPATH set due to cron not passing Env 
    PYTHONPATH=$HOME/bin/python3 "/home/boris/backup 06.03/realsense/server.py"
fi
