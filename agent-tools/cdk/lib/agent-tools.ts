#!/usr/bin/env node
import * as cdk from "aws-cdk-lib";
import { AgentToolsStack } from "./agent-tools-stack";

const app = new cdk.App();
// Get the tool filter from context if provided
const toolFilter = app.node.tryGetContext('tool');

console.log(`Deploying with toolFilter: ${toolFilter || 'none (deploying all tools)'}`);

new AgentToolsStack(app, "AgentToolsStack", {
  // Pass the tool filter to the stack
  toolFilter: toolFilter,
  // Optionally pass environment settings here.
  // env: { account: process.env.CDK_DEFAULT_ACCOUNT, region: process.env.CDK_DEFAULT_REGION }
});
