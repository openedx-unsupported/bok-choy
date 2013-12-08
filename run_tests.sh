#!/usr/bin/env bash

REPO_ROOT=`dirname $BASH_SOURCE`
SERVER_PORT=8003

# Start the server for the test fixture site
echo "Starting server for test fixture site..."
(cd $REPO_ROOT/tests/site && python -m SimpleHTTPServer $SERVER_PORT 2> /dev/null) &

# Ensure that the server is shut down on exit
trap "kill 0" SIGINT SIGTERM EXIT

# Run the test suite
echo "Running test suite..."
coverage run -m nose $REPO_ROOT/tests
