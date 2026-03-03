# Deployment

This document is the canonical reference for deployment and post-deploy validation.

## Databricks Apps Deployment

This project includes `app.yaml` and is ready for Databricks Apps.

High-level flow:

1. Deploy with Databricks CLI or UI.
2. Open the deployed app URL.
3. Validate MCP endpoint and tool behavior.

Reference: [Deploy Databricks Apps](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/deploy#deploy-the-app)

## MCP Endpoint

Deployed MCP endpoint pattern:

```text
https://<workspace>/serving-endpoints/<app-name>/mcp
```

## AI Playground Validation

After deployment:

1. Open AI Playground in your Databricks workspace.
2. Select a model with **Tools enabled**.
3. Add your deployed MCP server under **Tools**.
4. Run prompts that trigger tool invocation.

Reference: [AI Playground agent prototyping](https://docs.databricks.com/aws/en/generative-ai/agent-framework/ai-playground-agent)

## OAuth User-Authorization Validation

Use:

```bash
./scripts/dev/query_remote.sh
```

The script helps validate real user-authenticated calls against deployed endpoints.

## Related Docs

- [Testing](./testing.md)
- [Reference](./reference.md)
