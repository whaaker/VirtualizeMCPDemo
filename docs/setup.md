# Setup Guide

This document walks through every step needed to get the
**VirtualizeMCPDemo** workflow running end-to-end.

---

## 1. Register a self-hosted GitHub Actions runner

The workflow must run on the same machine (or network) as your
Parasoft Virtualize server so the agent can reach the locally-deployed
Virtualize MCP Server.

1. In your GitHub repository go to **Settings → Actions → Runners → New self-hosted runner**.
2. Select the OS of the machine running Virtualize, then follow the
   on-screen installation commands.
3. Start the runner service (`./run.sh` or install as a service with `./svc.sh install && ./svc.sh start`).
4. Verify it appears as **Idle** in the Runners list.

> **Tip:** assign a custom label (e.g. `virtualize-host`) to the runner
> and update `runs-on` in the workflow file accordingly.

---

## 2. Install runtime prerequisites on the runner machine

| Tool | Minimum version | Install guide |
|------|----------------|---------------|
| Python | 3.11 | <https://python.org/downloads> |
| Node.js | 20 LTS | <https://nodejs.org> |
| npm | 10+ | Bundled with Node.js |

The Jira MCP Server is launched automatically by the agent via
`npx @aashari/mcp-server-atlassian-jira`, so no separate install is needed.

---

## 3. Start the Parasoft Virtualize MCP Server

Consult your Parasoft Virtualize documentation for the exact steps to start
the built-in MCP Server. In general:

1. Open Virtualize and navigate to the MCP Server settings.
2. Start the server — by default it listens on **port 4000** and exposes
   an SSE endpoint at `/sse`.
3. Confirm it is reachable:
   ```bash
   curl http://localhost:4000/sse
   ```
4. Set the `PARASOFT_VIRTUALIZE_MCP_URL` secret to the full SSE URL, e.g.:
   ```
   http://localhost:4000/sse
   ```

If your Virtualize MCP Server uses a **stdio** interface instead, update
`mcp.json` — change `transport` to `"stdio"` and add the `command` and `args`
fields (see `mcp.json` comments).

---

## 4. Add GitHub Actions secrets

In **Settings → Secrets and variables → Actions → New repository secret**,
add each of the following:

| Secret name | Where to get the value |
|-------------|------------------------|
| `ANTHROPIC_API_KEY` | <https://console.anthropic.com> |
| `ATLASSIAN_SITE_NAME` | Your Jira subdomain, e.g. `acme` for `acme.atlassian.net` |
| `ATLASSIAN_USER_EMAIL` | The email address on your Atlassian account |
| `ATLASSIAN_API_TOKEN` | <https://id.atlassian.com/manage-profile/security/api-tokens> |
| `PARASOFT_VIRTUALIZE_MCP_URL` | SSE endpoint of the Virtualize MCP Server (step 3) |
| `PARASOFT_VIRTUALIZE_URL` | Base URL of Virtualize, e.g. `http://localhost:9080` |
| `PARASOFT_VIRTUALIZE_USER` | Virtualize server username |
| `PARASOFT_VIRTUALIZE_PASSWORD` | Virtualize server password |

---

## 5. (Optional) Test locally before running in CI

```bash
# Clone the repo and enter it
git clone https://github.com/whaaker/VirtualizeMCPDemo.git
cd VirtualizeMCPDemo

# Copy the env template and fill in your values
cp .env.example .env
# edit .env ...

# Install Python dependencies
pip install -r requirements.txt

# Run the agent directly
export $(grep -v '^#' .env | xargs)
JIRA_TICKET=PROJ-123 python scripts/agent.py
```

---

## 6. Trigger the workflow

1. Go to **Actions → Create Virtual Service from Jira Story**.
2. Click **Run workflow**.
3. Enter the Jira ticket number (e.g. `PROJ-123`).
4. Optionally override the Virtualize server URL or enable **dry run** mode.
5. Click **Run workflow** to start.

The agent log and a JSON summary are available as a downloadable artifact
once the run completes.
