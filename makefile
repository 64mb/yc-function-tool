THIS_FILE := $(lastword $(MAKEFILE_LIST))
.PHONY: deploy

deploy:
	python yc_deploy.py by-rest
