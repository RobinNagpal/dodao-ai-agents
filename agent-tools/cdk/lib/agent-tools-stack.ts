import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as ecr_assets from "aws-cdk-lib/aws-ecr-assets";
import * as ecr from "aws-cdk-lib/aws-ecr";
import * as path from "path";
import * as fs from "fs";

export interface AgentToolsStackProps extends cdk.StackProps {
  // Optional filter – if set, deploy only this tool.
  toolFilter?: string;
}

export class AgentToolsStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: AgentToolsStackProps) {
    super(scope, id, props);

    // Path to agents-tools.json (assumed to be one level up from the cdk folder)
    const toolsConfigPath = path.join(__dirname, "../..", "agents-tools.json");

    if (!fs.existsSync(toolsConfigPath)) {
      throw new Error(`agents-tools.json not found at ${toolsConfigPath}`);
    }
    const agentsTools = JSON.parse(fs.readFileSync(toolsConfigPath, "utf8"));

    // Get names of enabled tools (filter by context "tool" if provided)
    const allEnabled: string[] = agentsTools.agents
      .filter((agent: any) => agent.enabled)
      .map((agent: any) => agent.name);

    const toolFilter = props?.toolFilter;
    const enabledTools = toolFilter ? [toolFilter] : allEnabled;

    for (const tool of enabledTools) {
      // Define the directory of the tool (each tool has its own folder with Dockerfile etc.)
      const toolDir = path.join(__dirname, "../..", tool);
      if (!fs.existsSync(toolDir)) {
        throw new Error(`Tool folder not found: ${toolDir}`);
      }

      // Create a Docker image asset from the tool’s directory.
      const imageAsset = new ecr_assets.DockerImageAsset(this, `${tool}Asset`, {
        directory: toolDir,
        // You can pass build arguments or specify a file name if needed.
      });

      console.log(`Image asset for ${tool} created at ${imageAsset.imageUri}`);

      // Get a reference to the automatically created ECR repository.
      // (Override repositoryName so that it is predictable.)
      const repository = new ecr.Repository(this, `${tool}Repo`, {
        repositoryName: tool,
        imageTagMutability: ecr.TagMutability.MUTABLE,
        lifecycleRules: [
          {
            rulePriority: 1,
            description: "Keep only the last 3 images",
            maxImageCount: 3,
            tagStatus: ecr.TagStatus.ANY,
          },
        ],
      });

      // (Optional) You could configure a custom process to push the built image
      // into your repository. For simplicity, here we assume that the DockerImageAsset
      // is used as the source for the Lambda function.
      //
      // Create a Lambda function that uses the container image.
      new lambda.DockerImageFunction(this, `${tool}Function`, {
        functionName: tool,
        code: lambda.DockerImageCode.fromImageAsset(toolDir),
        timeout: cdk.Duration.seconds(30),
        memorySize: 512,
      });

      // (Optional) You might want to output the repository URI.
      new cdk.CfnOutput(this, `${tool}RepoURI`, {
        value: repository.repositoryUri,
        description: `ECR repository URI for ${tool}`,
      });
    }
  }
}
