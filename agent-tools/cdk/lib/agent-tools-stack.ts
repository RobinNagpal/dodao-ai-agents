import * as cdk from "aws-cdk-lib";
import * as ecr from "aws-cdk-lib/aws-ecr";
import * as ecr_assets from "aws-cdk-lib/aws-ecr-assets";
import * as lambda from "aws-cdk-lib/aws-lambda";
import {Construct} from "constructs";
import * as dotenv from "dotenv";
import * as fs from "fs";
import * as path from "path";

dotenv.config();

export interface AgentToolsStackProps extends cdk.StackProps {
  // Optional filter – if set, deploy only this tool.
  toolFilter?: string;
}

// Check if all the environment variables are set
if (!process.env.SCRAPINGANT_API_KEY) {
  throw new Error("SCRAPINGANT_API_KEY environment variable is not set.");
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

      // Create an ECR repository for the tool.
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

      // Create a Lambda function that uses the container image.
      const lambdaFunction = new lambda.DockerImageFunction(this, `${tool}Function`, {
        functionName: tool,
        code: lambda.DockerImageCode.fromImageAsset(toolDir),
        timeout: cdk.Duration.seconds(30),
        memorySize: 512,
        environment: {
          SCRAPINGANT_API_KEY: process.env.SCRAPINGANT_API_KEY || "",
          EDGAR_LOCAL_DATA_DIR: "/tmp/edgar_data",

        },

      });

      // Add a Lambda Function URL with no auth (public endpoint).
      const functionUrl = lambdaFunction.addFunctionUrl({
        authType: lambda.FunctionUrlAuthType.NONE,
        cors: {
          allowedOrigins: ["*"],
          allowedMethods: [lambda.HttpMethod.POST, lambda.HttpMethod.GET], // adjust as needed
        },
      });

      // Output the ECR repository URI.
      new cdk.CfnOutput(this, `${tool}RepoURI`, {
        value: repository.repositoryUri,
        description: `ECR repository URI for ${tool}`,
      });

      // Output the Lambda Function URL.
      new cdk.CfnOutput(this, `${tool}FunctionUrl`, {
        value: functionUrl.url,
        description: `Lambda Function URL for ${tool}`,
      });
    }
  }
}
