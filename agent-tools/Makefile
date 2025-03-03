# Makefile to invoke CDK commands for the agent tools stack.
# Usage examples:
#   make help
#   make cdk-synth
#   make cdk-deploy
#   make cdk-deploy tool=sec-edgar
#   make cdk-diff
#   make cdk-destroy

SHELL := /bin/bash

.PHONY: help cdk-synth cdk-deploy cdk-diff cdk-destroy

help:  ## Show help for all targets
	@echo "Makefile targets:"
	@echo "  make cdk-synth           - Synthesize the CDK CloudFormation template"
	@echo "  make cdk-deploy          - Deploy the CDK stack (all tools)"
	@echo "  make cdk-deploy tool=XXX - Deploy a single tool by specifying tool=<tool_name>"
	@echo "  make cdk-diff            - Diff the deployed stack with the current state"
	@echo "  make cdk-destroy         - Destroy the CDK stack"

cdk-bootstrap:  ## Bootstrap the CDK environment
	cd cdk && npx cdk bootstrap

cdk-synth:  ## Synthesize the CDK CloudFormation template
	cd cdk && npm run build && npx cdk synth

cdk-deploy:  ## Deploy the CDK stack (all tools or single if tool parameter is set)
	aws ecr-public get-login-password --region us-east-1 | docker login --username AWS --password-stdin public.ecr.aws
	@if [ -n "$(tool)" ]; then \
	  echo "Deploying tool $(tool)..."; \
	  cd cdk && npm run build && npx cdk deploy --context tool=$(tool) --require-approval never; \
	else \
	  echo "Deploying all tools..."; \
	  cd cdk && npm run build && npx cdk deploy --require-approval never; \
	fi

cdk-diff:  ## Diff the deployed stack with the current state
	cd cdk && npm run build && npx cdk diff

cdk-destroy:  ## Destroy the CDK stack
	cd cdk && npm run build && npx cdk destroy --force


# --- Generic Virtual Environment Targets using UV ---

# Create a UV virtual environment for a single tool.
# Usage: make venv-uv tool=<tool_name>
venv-uv:
	@if [ -z "$(tool)" ]; then \
	  echo "Error: tool name must be provided. Usage: make venv-uv tool=<tool_name>"; \
	  exit 1; \
	fi
	@echo "Creating $(tool) virtual environment using uv with Python 3.10..."
	cd $(tool) && uv venv --python=python3.11 .venv && uv pip install -r requirements.txt


fmt:
	black sec-edgar/src
	black s3-uploader/src
	black scrapingant/src
