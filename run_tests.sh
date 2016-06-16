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

# Ensure that the server is shut down on exit
trap "kill -- -$BASHPID || echo 'no child processes found'" SIGINT SIGTERM EXIT

# Start the server for the test fixture site
echo_task "Start server for test fixture site"
python -m tests.http_server $SERVER_PORT 2> /dev/null &
echo "Running test server on port $SERVER_PORT"

echo_task "Run unit test suite"
coverage run -m nose $REPO_ROOT/tests/$1
