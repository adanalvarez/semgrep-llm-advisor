# semgrep-llm-advisor

**Proof of Concept**

semgrep-llm-advisor is an experimental repository that integrates Semgrep static analysis with AI-powered recommendations. Leveraging Anthropic's Claude model via AWS Bedrock, this PoC demonstrates how to generate actionable remediation suggestions and annotate pull requests with detailed feedback.

> **Note:** This project is a proof-of-concept and is provided "as-is" for demonstration purposes. It is not production-ready and may require additional enhancements and security reviews before any production use.

## Overview

semgrep-llm-advisor combines two main composite actions:
- **Semgrep Scan Action:** Runs a Semgrep CI scan against your codebase and outputs the results as a JSON string.
- **AI Enhancement Action:** Processes Semgrep results with an LLM to generate remediation recommendations in pull requests with the findings.

This integration helps streamline code security reviews by automatically identifying vulnerabilities and suggesting fixes.

## Features

- **Automated Code Analysis:** Uses Semgrep to perform static code analysis.
- **AI-Driven Remediation:** Invokes an LLM (Anthropic's Claude) to propose remediation steps based on detected vulnerabilities.
- **GitHub Actions Integration:** Seamlessly integrates into CI/CD pipelines to comment on pull requests.
- **Customizable Configuration:** Supports custom Semgrep configurations and flexible AWS credential management.

## Getting Started

### Prerequisites

- AWS credentials with permissions to invoke AWS Bedrock (Anthropic's Claude). [[Configuring OpenID Connect in Amazon Web Services](https://docs.github.com/en/actions/security-for-github-actions/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services)]
- Repository variable and secret setup:
  - **Repository Variable:** `AWS_REGION` (e.g., `us-east-2`)
  - **Repository Secret:** `AWS_ROLE` (e.g., `arn:aws:iam::YOUR_ACCOUNT_ID:role/YOUR_ROLE_NAME`)
  - **Amazon Bedrock foundation model:** `MODEL_ID` (e.g., `us.anthropic.claude-3-5-haiku-20241022-v1:0`)

### Setting Up the Workflow

1. **Add the Workflow File:**  
   Create a workflow file (e.g., `.github/workflows/semgrep-ai.yml`) in your repository with the following content:

   ```yaml
   name: Semgrep AI Code Review (PoC)

   on:
     pull_request:
       branches: [ "main" ]

   permissions:
     id-token: write
     contents: read
     pull-requests: write 

   jobs:
     semgrep-ai:
       runs-on: ubuntu-latest
       env:
          AWS_REGION: ${{ vars.AWS_REGION }}
          MODEL_ID: ${{ vars.MODEL_ID }}
       steps:
         - name: Checkout Code
           uses: actions/checkout@v3

         - name: Configure AWS Credentials
           uses: aws-actions/configure-aws-credentials@v4
           with:
             aws-region: ${{ vars.AWS_REGION }}
             role-to-assume: ${{ secrets.AWS_ROLE }}

         - name: Run Semgrep Scan
           id: semgrep
           uses: adanalvarez/semgrep-llm-advisor/semgrep@main
           with:
             semgrep_config: ''  # Optionally provide a custom Semgrep configuration

         - name: Run AI Enhancement and Comment
           if: ${{ toJson(fromJson(steps.semgrep.outputs.semgrep_results_json).results) != '[]' }}
           uses: adanalvarez/semgrep-llm-advisor/ai@main
           with:
             semgrep_results: ${{ steps.semgrep.outputs.semgrep_results_json }}
   ```

2. **Configure Repository Variables and Secrets:**

- In your repository settings, add a variable named AWS_REGION with your desired region (e.g., us-east-2) and a variable named MODEL_ID with your desired foundational model (e.g., `us.anthropic.claude-3-5-haiku-20241022-v1:0`).
- Under repository secrets, add a secret named AWS_ROLE containing your AWS role ARN.

3. **Customize Inputs as Needed:**
The composite actions support customizable inputs. For instance, you can specify a custom Semgrep configuration if desired.

## How It Works
1. **Semgrep Scan:**
The semgrep composite action checks out your code, sets up a Python environment, and runs a Semgrep scan. It outputs the results as JSON for downstream processing.

2. **AI Enhancement:** 
The AI composite action:

- Sets up its environment.
- Invokes the AI enhancement script to extract relevant code context and generate remediation recommendations using Anthropic's Claude model via AWS Bedrock.
- Formats the recommendations into Markdown and, if configured, comments on the pull request.

3. **AWS Credential Management:**
AWS credentials are configured in the main workflow via a repository variable for the region and a repository secret for the role ARN, making the actions easily reusable by anyone.
