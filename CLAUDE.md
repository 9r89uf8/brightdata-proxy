# CLAUDE.md - Project Documentation & Development Guidelines

## What We're Building

This project is a **Google Search Agent powered by Claude AI** - an intelligent browser automation system that performs web navigation and research tasks through natural language commands. The agent combines stealth browser automation with Claude AI's decision-making capabilities to create a human-like web interaction experience.

### Core Functionality
- **Natural Language Control**: Users describe what they want in plain English
- **Intelligent Decision Making**: Claude AI analyzes pages and decides optimal actions
- **Stealth Automation**: Undetected browser with anti-bot techniques
- **Dual Operation Modes**: Fast DOM-based text processing
- **Mobile & Desktop Support**: Emulates iPhone or runs in desktop mode

How you ship changes now
Edit brightdata_proxy_headless.py (or Dockerfile, etc.)

Push to main → GitHub Actions builds/pushes to ECR and registers a new task definition revision

The API’s Lambda still calls your task family, so new runs automatically use the latest revision

Rotating/handling certs
You kept certs out of Git—good. For Bright Data CA, keep it in SSM /brightdata/ca_b64 (or Secrets Manager).

To rotate: update the SSM parameter; no image rebuild needed. New tasks read the new value at start.

Selenium-Wire CA is extracted in-container each run, so nothing to rotate there.


Here’s the rule of thumb:

If you only change the value of an existing Parameter Store entry that’s already mapped in your ECS task definition → No CloudFormation redeploy needed.
Just restart the ECS task so it pulls the new value at startup.

If you add a new Parameter Store variable or rename an existing one → You must update the ECS task definition, because the secrets array in the task definition explicitly lists which parameters to inject as environment variables.
That means CloudFormation (or a manual register-task-definition) update is required.

Think of the ECS task definition as the "wiring diagram":

Adding new wires → need to rewire (update/redeploy stack).

Sending new power through existing wires → no rewire, just restart.
