#!/usr/bin/env node
import * as cdk from "aws-cdk-lib";
import { AgentToolsStack } from "./agent-tools-stack";

const app = new cdk.App();
new AgentToolsStack(app, "AgentToolsStack", {
  // Optionally pass environment settings here.
  // env: { account: process.env.CDK_DEFAULT_ACCOUNT, region: process.env.CDK_DEFAULT_REGION }
});
