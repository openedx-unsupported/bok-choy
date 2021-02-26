.PHONY: clean coverage docs help requirements test test-all upgrade

.DEFAULT_GOAL := help

define BROWSER_PYSCRIPT
import os, webbrowser, sys
from time import sleep
try:
	from urllib import pathname2url
except:
	from urllib.request import pathname2url

path_or_url = sys.argv[1]
delay = int(sys.argv[2]) if len(sys.argv) > 2 else 0
if delay > 0:
    sleep(delay)
if '://' in path_or_url:
    webbrowser.open(path_or_url)
else:
    webbrowser.open("file://" + pathname2url(os.path.abspath(path_or_url)))
endef
export BROWSER_PYSCRIPT
BROWSER := python -c "$$BROWSER_PYSCRIPT"

help: ## display this help message
	@echo "Please use \`make <target>' where <target> is one of"
	@perl -nle'print $& if m{^[a-zA-Z_-]+:.*?## .*$$}' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m  %-25s\033[0m %s\n", $$1, $$2}'

clean: ## remove generated byte code, coverage reports, and build artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	coverage erase
	rm -fr build/
	rm -fr dist/
	rm -fr *.egg-info

coverage: clean ## generate and view HTML coverage report
	pytest --cov-report html
	$(BROWSER) htmlcov/index.html

docs: ## generate Sphinx HTML documentation, including API docs
	tox -e doc
	$(BROWSER) build/sphinx/html/index.html

requirements: ## install development environment requirements
	pip install -r requirements/pip.txt
	pip install -r requirements/pip-tools.txt
	pip-sync requirements/dev.txt requirements/private.*

test: clean ## run tests in the current virtualenv
	pytest

test-all: ## run tests on every supported Python version
	tox

upgrade: export CUSTOM_COMPILE_COMMAND=make upgrade
upgrade: ## update the requirements/*.txt files with the latest packages satisfying requirements/*.in
	pip install -r requirements/pip-tools.txt
	pip-compile --upgrade --allow-unsafe --rebuild -o requirements/pip.txt requirements/pip.in
	pip-compile --rebuild --upgrade -o requirements/pip-tools.txt requirements/pip-tools.in
	pip-compile --rebuild --upgrade -o requirements/base.txt requirements/base.in
	pip-compile --rebuild --upgrade -o requirements/doc.txt requirements/doc.in
	pip-compile --rebuild --upgrade -o requirements/test.txt requirements/test.in
	pip-compile --rebuild --upgrade -o requirements/needle.txt requirements/needle.in
	pip-compile --rebuild --upgrade -o requirements/travis.txt requirements/travis.in
	pip-compile --rebuild --upgrade -o requirements/dev.txt requirements/dev.in
