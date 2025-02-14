#!/usr/bin/env python
import json
import os
import subprocess
import sys
from pathlib import Path

import click

# Default configurations - adjust to your environment
DEFAULT_AWS_REGION = "us-east-1"
DEFAULT_ECR_BASE_URI = "123456789012.dkr.ecr.us-east-1.amazonaws.com"

# Paths to important files/folders
TOOLS_BASE_DIR = Path(__file__).parent  # If deploy.py is next to the tool folders
AGENTS_TOOLS_JSON = TOOLS_BASE_DIR / "agents-tools.json"
DEPLOYMENT_STATUS_JSON = TOOLS_BASE_DIR / "deployment-status.json"
TERRAFORM_DIR = TOOLS_BASE_DIR / "terraform"

# Get the current Git commit hash
def get_git_version() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("utf-8").strip()
    except Exception:
        # fallback if git not available
        return "unknown-git-version"

def load_enabled_tools() -> list[str]:
    """Load the list of enabled tools from agents-tools.json."""
    with open(AGENTS_TOOLS_JSON, "r") as f:
        data = json.load(f)
    # Return only the names that have "enabled": true
    return [agent["name"] for agent in data["agents"] if agent["enabled"] is True]

def update_deployment_status(tool_name: str, git_version: str) -> None:
    """Update or insert the deployment status for a particular tool."""
    if not DEPLOYMENT_STATUS_JSON.exists():
        DEPLOYMENT_STATUS_JSON.write_text(json.dumps({"deployments": []}, indent=2))

    with open(DEPLOYMENT_STATUS_JSON, "r") as f:
        status_data = json.load(f)

    # Filter out any existing entry for this tool
    new_deployments = [
        entry for entry in status_data.get("deployments", [])
        if entry["tool"] != tool_name
    ]
    # Add the new record
    new_deployments.append({"tool": tool_name, "version": git_version})
    status_data["deployments"] = new_deployments

    with open(DEPLOYMENT_STATUS_JSON, "w") as f:
        json.dump(status_data, f, indent=2)

@click.group()
@click.option("--aws-region", default=DEFAULT_AWS_REGION, help="AWS region to use.")
@click.option("--ecr-base-uri", default=DEFAULT_ECR_BASE_URI, help="Base URI of your ECR repository.")
@click.pass_context
def cli(ctx, aws_region, ecr_base_uri):
    """Deployment CLI for building, pushing, and deploying Lambda tools."""
    ctx.ensure_object(dict)
    ctx.obj["AWS_REGION"] = aws_region
    ctx.obj["ECR_BASE_URI"] = ecr_base_uri
    ctx.obj["GIT_VERSION"] = get_git_version()

@cli.command("list-tools")
@click.pass_context
def list_tools(ctx):
    """List all enabled tools from agents-tools.json."""
    enabled = load_enabled_tools()
    click.echo("Enabled tools: " + ", ".join(enabled))

#
# BUILD COMMANDS
#
@cli.command("build-all")
@click.pass_context
def build_all(ctx):
    """Build Docker images for all enabled tools."""
    enabled_tools = load_enabled_tools()
    for tool_name in enabled_tools:
        build_lambda_image(tool_name)

@cli.command("build-lambda")
@click.argument("tool_name")
@click.pass_context
def build_lambda(ctx, tool_name):
    """Build Docker image for a single tool."""
    build_lambda_image(tool_name)

def build_lambda_image(tool_name: str) -> None:
    """Helper to build Docker image for a single tool."""
    tool_dir = TOOLS_BASE_DIR / tool_name
    if not tool_dir.is_dir():
        click.echo(f"[ERROR] The tool folder '{tool_name}' does not exist.", err=True)
        sys.exit(1)

    click.echo(f"Building Docker image for {tool_name}...")
    cmd = ["docker", "build", "-t", f"{tool_name}:latest", str(tool_dir)]
    run_command(cmd)

#
# PUSH COMMANDS
#
@cli.command("push-all")
@click.pass_context
def push_all(ctx):
    """Push Docker images for all enabled tools."""
    enabled_tools = load_enabled_tools()
    for tool_name in enabled_tools:
        push_lambda_image(ctx, tool_name)

@cli.command("push-lambda")
@click.argument("tool_name")
@click.pass_context
def push_lambda(ctx, tool_name):
    """Push Docker image for a single tool."""
    push_lambda_image(ctx, tool_name)

def push_lambda_image(ctx, tool_name: str) -> None:
    ecr_base = ctx.obj["ECR_BASE_URI"]
    git_ver = ctx.obj["GIT_VERSION"]
    click.echo(f"Tagging and pushing Docker image for {tool_name} with tag {git_ver}...")

    # docker tag <tool>:latest <ECR_BASE_URI>/<tool>:<git_ver>
    tag_cmd = ["docker", "tag", f"{tool_name}:latest", f"{ecr_base}/{tool_name}:{git_ver}"]
    run_command(tag_cmd)

    # docker push <ECR_BASE_URI>/<tool>:<git_ver>
    push_cmd = ["docker", "push", f"{ecr_base}/{tool_name}:{git_ver}"]
    run_command(push_cmd)

#
# DEPLOY (Terraform) COMMANDS
#
@cli.command("deploy-all")
@click.pass_context
def deploy_all(ctx):
    """Deploy all enabled tools (build, push, then terraform apply)."""
    aws_region = ctx.obj["AWS_REGION"]
    ecr_base = ctx.obj["ECR_BASE_URI"]
    git_ver = ctx.obj["GIT_VERSION"]

    # 1. Build & push for all
    build_all(ctx)
    push_all(ctx)

    # 2. Terraform init
    tf_init()

    # 3. Terraform apply (pass in your container URIs as variables).
    #    For demonstration, we handle only 'sec-edgar' and 'scrapingant'.
    #    For new tools, expand this logic or pass them differently.
    sec_edgar_uri = f"{ecr_base}/sec-edgar:{git_ver}"
    scrapingant_uri = f"{ecr_base}/scrapingant:{git_ver}"

    tf_apply([
        f"-var=region={aws_region}",
        f"-var=sec_edgar_image_uri={sec_edgar_uri}",
        f"-var=scrapingant_image_uri={scrapingant_uri}",
    ])

    # 4. Update deployment status for each tool
    for tool_name in load_enabled_tools():
        update_deployment_status(tool_name, git_ver)

@cli.command("deploy-lambda")
@click.argument("tool_name")
@click.pass_context
def deploy_lambda(ctx, tool_name):
    """Deploy a single tool (build, push, then partial terraform apply)."""
    aws_region = ctx.obj["AWS_REGION"]
    ecr_base = ctx.obj["ECR_BASE_URI"]
    git_ver = ctx.obj["GIT_VERSION"]

    # 1. Build & push for this specific tool
    build_lambda_image(tool_name)
    push_lambda_image(ctx, tool_name)

    # 2. Terraform init
    tf_init()

    # 3. Terraform apply for the single tool. We'll do a quick if-case.
    #    For 'sec-edgar', pass in that image as <git_ver>, others as 'latest' or vice versa.
    #    Adjust as needed or add a dynamic approach for new tools.
    if tool_name == "sec-edgar":
        tf_vars = [
            f"-var=region={aws_region}",
            f"-var=sec_edgar_image_uri={ecr_base}/sec-edgar:{git_ver}",
            f"-var=scrapingant_image_uri={ecr_base}/scrapingant:latest",
        ]
    elif tool_name == "scrapingant":
        tf_vars = [
            f"-var=region={aws_region}",
            f"-var=sec_edgar_image_uri={ecr_base}/sec-edgar:latest",
            f"-var=scrapingant_image_uri={ecr_base}/scrapingant:{git_ver}",
        ]
    else:
        click.echo(f"Warning: No specific Terraform variable logic for '{tool_name}'. Using defaults.")
        tf_vars = [f"-var=region={aws_region}"]

    tf_apply(tf_vars)

    # 4. Update deployment status
    update_deployment_status(tool_name, git_ver)

#
# Virtual Environments (optional)
#
@cli.command("create-venv")
@click.argument("tool_name")
def create_venv(tool_name):
    """Create a uv-based virtual environment for the given tool."""
    tool_dir = TOOLS_BASE_DIR / tool_name
    if not tool_dir.is_dir():
        click.echo(f"[ERROR] Tool folder '{tool_name}' does not exist.", err=True)
        sys.exit(1)

    venv_name = f"venv-{tool_name}"
    click.echo(f"Creating virtual environment {venv_name} for {tool_name} using uv...")
    cmd = ["uv", "new", venv_name]
    run_command(cmd, cwd=tool_dir)

@cli.command("create-venv-all")
def create_venv_all():
    """Create uv-based virtual environments for all enabled tools."""
    enabled_tools = load_enabled_tools()
    for tool_name in enabled_tools:
        create_venv(tool_name)

#
# Helpers for running shell commands
#
def run_command(cmd, cwd=None):
    click.echo(f"Running command: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, cwd=cwd, check=True)
    except subprocess.CalledProcessError as e:
        click.echo(f"[ERROR] Command failed with exit code {e.returncode}", err=True)
        sys.exit(e.returncode)

def tf_init():
    """Run Terraform init in the Terraform directory."""
    click.echo("Initializing Terraform...")
    run_command(["terraform", "init"], cwd=str(TERRAFORM_DIR))

def tf_apply(vars_list):
    """Run Terraform apply with a list of -var=... arguments."""
    cmd = ["terraform", "apply"] + vars_list + ["-auto-approve"]
    run_command(cmd, cwd=str(TERRAFORM_DIR))

if __name__ == "__main__":
    cli()
