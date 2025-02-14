# Agent Tools
This directory contains various tools that will be called from the ai agents. These tools are deployed as separate 
Lambda functions and can be invoked via HTTP requests. The tools are designed to perform specific tasks like web 
scraping, data extraction, or API calls, and they return the results in a structured format.

# Deployment

The deployment works by leveraging AWS CDK and a Makefile to automate the creation and update of our agent tools stack. Here's a quick overview:

- **Configuration & Filtering:**  
  The `agents-tools.json` file lists all agent tools (like `sec-edgar` and `scrapingant`) with an `enabled` flag. The CDK stack reads this file and, if a `tool` context is provided (via the `tool` parameter), it deploys only that specific tool; otherwise, it deploys all enabled tools.

- **Building & Packaging:**  
  For each enabled tool, the CDK stack:
    - Locates the corresponding directory (which contains a Dockerfile, Lambda code, and dependencies).
    - Uses the DockerImageAsset to build a container image.
    - Creates an ECR repository to store the image.
    - Deploys an AWS Lambda function that uses the container image, exposing it via a public Lambda Function URL.

- **Environment Variables:**  
  Critical environment variables (e.g., `SCRAPINGANT_API_KEY`) are verified during deployment to ensure all runtime requirements are met.

- **Key Commands:**  
  Use the provided Makefile for deployment tasks:
    - **`make help`**: Lists all available Makefile targets.
    - **`make cdk-synth`**: Synthesizes the CloudFormation template from the CDK code.
    - **`make cdk-deploy`**: Deploys the entire stack. To deploy a single tool, run `make cdk-deploy tool=<tool_name>`.
    - **`make cdk-diff`**: Shows differences between the deployed stack and the current code.
    - **`make cdk-destroy`**: Destroys the deployed stack.

This setup ensures a streamlined, container-based deployment of each agent tool, making it easy to manage, update, and scale our services.

# CDK Commands
The AWS CDK commands help translate your TypeScript (or other language) code into AWS CloudFormation templates and manage your cloud resources. Here's a brief explanation of some key commands:

- **`cdk bootstrap`**  
  Sets up your AWS environment with necessary resources (like an S3 bucket) for deploying CDK stacks. It only needs to run once per environment.

- **`cdk synth`**  
  Synthesizes your CDK application into a CloudFormation template. This lets you review the generated template before deployment.

- **`cdk deploy`**  
  Deploys the synthesized CloudFormation stack to AWS. You can deploy all stacks or filter to a specific tool (using context variables, e.g., `tool=sec-edgar`).

- **`cdk diff`**  
  Compares your local CDK code with the deployed stack, showing any differences before you commit changes.

- **`cdk destroy`**  
  Removes the deployed stack and all associated AWS resources.

These commands are wrapped in our Makefile for convenience, allowing you to execute them with simple `make` targets. For example, running `make cdk-deploy` builds and deploys all tools, while `make cdk-deploy tool=sec-edgar` deploys only the SEC Edgar tool.
