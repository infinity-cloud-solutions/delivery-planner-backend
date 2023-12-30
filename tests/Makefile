PIP ?= pip3
SHELL := /bin/bash

install: 
	${PIP} install virtualenv
	python3 -m venv .venv
	source ./.venv/bin/activate && ${PIP} install -r requirements.txt

test:
	source ./.venv/bin/activate  &&  python -m unittest -v create_order/test_*.py
	source ./.venv/bin/activate  &&  python -m unittest -v integration/test_*.py