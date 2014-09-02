#!/usr/bin/env bash

# Usage: ./run_tests.sh [TEST_MODULE]
#
# Examples:
#  Run all tests:               ./run_tests.sh
#  Run the input tests only:    ./run_tests.sh test_inputs.py

set -e

function echo_task {
    echo $'\n'
    echo "====== $1"
}

REPO_ROOT=`dirname $BASH_SOURCE`
SERVER_PORT=8003

export BOK_CHOY_HAR_DIR=$REPO_ROOT/hars
export LOG_DIR=$REPO_ROOT/logs
export SCREENSHOT_DIR=$LOG_DIR
export SELENIUM_DRIVER_LOG_DIR=$LOG_DIR

# Set up the har directory
mkdir -p $BOK_CHOY_HAR_DIR
rm -rf $BOK_CHOY_HAR_DIR/*.har

# Set up the output logs directory for
# screenshots and selenium driver logs
mkdir -p $LOG_DIR
rm -rf $LOG_DIR/*

# Ensure that the server is shut down on exit
trap "kill -- -$BASHPID || echo 'no child processes found'" SIGINT SIGTERM EXIT

# Start the server for the test fixture site
echo_task "Start server for test fixture site"
python -m tests.http_server $SERVER_PORT 2> /dev/null &
echo "Running test server on port $SERVER_PORT"

echo_task "Run unit test suite"
coverage run -m nose $REPO_ROOT/tests/$1

# Skip other tests if we've specified a particular unit test
if [ -z $1 ]; then

    echo_task "Coverage report"
    coverage report

    echo_task "Install bok-choy"
    pip uninstall bok-choy -y &> /dev/null || true
    python setup.py install

    echo_task "Run tutorial examples"
    python docs/code/round_1/test_search.py
    python docs/code/round_2/test_search.py
    python docs/code/round_3/test_search.py

    echo_task "Build docs"
    python setup.py build_sphinx
fi
