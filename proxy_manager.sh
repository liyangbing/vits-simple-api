#!/bin/bash

# pip install gunicorn
# pip install gevent
# test 

start() {
    echo "Activating conda environment..."
    source ~/miniconda3/etc/profile.d/conda.sh
    conda activate vits
    
    echo "Changing to the correct directory..."
    cd /public/vits-simple-api || exit
    echo "Stopping existing instances..."
    stop

    echo "Starting program..."

    nohup python proxy.py &
}

stop() {
    echo "Stopping program..."
    pkill -f "python proxy.py"
}

case $1 in
    start|stop) "$1" ;;
    *) echo "Usage: $0 start|stop" ;;
esac
