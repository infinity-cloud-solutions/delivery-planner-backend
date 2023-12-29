PIP ?= pip3
SHELL := /bin/bash

install: 
	${PIP} install virtualenv
	python3 -m venv .venv
	source ./.venv/bin/activate && ${PIP} install -r requirements.txt

test:
	source ./.venv/bin/activate  &&  python -m unittest create_order/test_lambda_handler.py
	source ./.venv/bin/activate  &&  python -m unittest -v integration/test_shopify_data_mapper.py