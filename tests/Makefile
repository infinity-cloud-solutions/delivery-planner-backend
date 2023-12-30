PIP ?= pip3
SHELL := /bin/bash

install: 
	${PIP} install virtualenv
	python3 -m venv .venv
	source ./.venv/bin/activate && ${PIP} install -r requirements.txt

test:
	source ./.venv/bin/activate  &&  pytest -v