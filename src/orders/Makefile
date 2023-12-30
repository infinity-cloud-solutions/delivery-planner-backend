PIP ?= pip3
SHELL := /bin/bash

target:
	$(info ${HELP_MESSAGE})
	@exit 0

clean: 
	$(info [*] Who needs all that anyway? Destroying environment....)
	rm -rf ./.aws-sam/ ./.venv/

checkOSDependencies:
	python3 --version || grep "3.10" || (echo "Error: Requires Python 3.10 " && exit 1)

all: clean build

install: checkOSDependencies
	${PIP} install virtualenv
	python3 -m venv .venv
	source ./.venv/bin/activate && ${PIP} install -r tests/requirements.txt

shell:
	source ./.venv/bin/activate

deps:
	source ./.venv/bin/activate && ${PIP} install -r tests/requirements.txt

coverage:
	source ./.venv/bin/activate &&  coverage run -m unittest discover
	source ./.venv/bin/activate &&  coverage html --omit "tests/*",".venv/*"

test:
	source ./.venv/bin/activate &&  pytest -v --disable-socket -s tests/unit/

build: 
	sam build --use-container

deploy:
	sam build --use-container
	sam deploy

deploy.g:
	sam build --use-container
	sam deploy --guided

delete:
	sam delete

#############
#  Helpers  #
#############

define HELP_MESSAGE

	Usage: make <command>

	Commands:

	build     Build Lambda function and dependencies
	deploy.g  Deploy guided (for initial deployment)
	deploy    Deploy subsequent changes

	install   Install application and dev dependencies defined in requirements.txt
	shell     Spawn a virtual environment shell
	deps      Install project dependencies locally
	test      Run unit test locally using mocks


	clean     Cleans up local build artifacts and environment
	delete    Delete stack from AWS

endef