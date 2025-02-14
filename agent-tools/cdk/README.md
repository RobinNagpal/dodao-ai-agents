Below is a list of the most useful AWS CDK CLI commands you’ll use during your project’s lifecycle, along with a brief explanation of what each does:

---

### 1. **cdk bootstrap**

**Command:**
```bash
cdk bootstrap
```

**What it does:**
- **Purpose:** Prepares your AWS environment (account and region) to receive CDK deployments.
- **Details:**
    - Creates a CloudFormation stack (the “bootstrap stack”) that provisions resources required by CDK such as an S3 bucket for storing assets (e.g., Docker images, Lambda deployment packages).
    - **Important:** This step is essential especially when you’re using assets like Docker images because the assets need a location to be stored before they can be referenced in your deployed stacks.

---

### 2. **cdk synth**

**Command:**
```bash
cdk synth
```

**What it does:**
- **Purpose:** Synthesizes (or “compiles”) your CDK application into a CloudFormation template.
- **Details:**
    - It produces a JSON or YAML CloudFormation template that represents your infrastructure.
    - Useful for inspecting what resources will be created or modified without actually deploying them.

---

### 3. **cdk diff**

**Command:**
```bash
cdk diff
```

**What it does:**
- **Purpose:** Compares your locally synthesized CloudFormation template with what’s currently deployed in your AWS account.
- **Details:**
    - Helps you review changes before running a deployment.
    - Lists additions, modifications, or deletions to your infrastructure, so you can be confident about the changes you’re about to make.

---

### 4. **cdk deploy**

**Command:**
```bash
cdk deploy
```

**What it does:**
- **Purpose:** Deploys your CDK stack(s) to AWS.
- **Details:**
    - Automatically packages your assets (such as your Docker image built from your tool directory), uploads them to S3 (or ECR in the case of Docker assets), and then creates or updates the CloudFormation stack.
    - You can deploy a specific stack by providing its name as an argument:
      ```bash
      cdk deploy AgentToolsStack
      ```
    - You can also use additional flags (e.g., `--profile myAWSProfile` to specify a particular AWS CLI profile).

---

### 5. **cdk destroy**

**Command:**
```bash
cdk destroy
```

**What it does:**
- **Purpose:** Tears down (deletes) your deployed stacks from AWS.
- **Details:**
    - Removes the CloudFormation stack and all the resources associated with it.
    - As with deploy, you can specify a particular stack to destroy:
      ```bash
      cdk destroy AgentToolsStack
      ```

---

### 6. **Additional Useful Commands**

- **cdk list (or cdk ls):**
  ```bash
  cdk list
  ```
  **Purpose:** Lists all the stacks defined in your CDK application.

- **cdk doctor:**
  ```bash
  cdk doctor
  ```
  **Purpose:** Checks your environment and configuration for potential issues with your CDK setup.

- **cdk version:**
  ```bash
  cdk version
  ```
  **Purpose:** Displays the current version of the CDK CLI you’re using.

- **Context Commands:**
    - You can pass context values when running CDK commands, which can be used in your app:
      ```bash
      cdk deploy --context tool=myToolName
      ```
    - Context can also be managed via the `cdk.json` file.

---

### **Workflow Summary**

1. **Bootstrap (One-Time Setup):**  
   Set up your AWS account/environment for CDK deployments.
   ```bash
   cdk bootstrap
   ```

2. **Synthesize:**  
   Generate the CloudFormation template to check what will be deployed.
   ```bash
   cdk synth
   ```

3. **Diff:**  
   Compare the current state with your changes.
   ```bash
   cdk diff
   ```

4. **Deploy:**  
   Push your changes to AWS.
   ```bash
   cdk deploy
   ```

5. **Destroy:**  
   Remove your deployed stack when it’s no longer needed.
   ```bash
   cdk destroy
   ```

Using these commands, you can effectively create, update, and delete your infrastructure as you iterate on your project using the AWS CDK.
