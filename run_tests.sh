#!/usr/bin/env bash

# Usage: ./run_tests.sh [TEST_MODULE]
#
# Examples:
#  Run all tests:               ./run_tests.sh
#  Run the input tests only:    ./run_tests.sh test_inputs.py

REPO_ROOT=`dirname $BASH_SOURCE`
SERVER_PORT=8003
export SCREENSHOT_DIR=$REPO_ROOT/screenshots

# Set up the screenshot directory
mkdir -p $SCREENSHOT_DIR
rm -rf $SCREENSHOT_DIR/*.png

# Start the server for the test fixture site
echo "Starting server for test fixture site..."
(cd $REPO_ROOT/tests/site && python -m SimpleHTTPServer $SERVER_PORT 2> /dev/null) &

# Ensure that the server is shut down on exit
trap "kill 0" SIGINT SIGTERM EXIT

# Run the test suite
echo "Running test suite..."
coverage run -m nose $REPO_ROOT/tests/$1
