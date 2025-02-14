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

cdk-synth:  ## Synthesize the CDK CloudFormation template
	cd cdk && npm run build && npx cdk synth

cdk-deploy:  ## Deploy the CDK stack (all tools or single if tool parameter is set)
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
