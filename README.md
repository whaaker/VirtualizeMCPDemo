# VirtualizeMCPDemo

A showcase of how to use **GitHub Actions** (self-hosted runner) with AI
automation to read a Jira user story and automatically create and deploy a
virtual service on a locally-running **Parasoft Virtualize** server — all
orchestrated by Claude via the **Model Context Protocol (MCP)**.

---

## How it works

```
┌─────────────────────────────────────────────────────────────────┐
│  GitHub Actions  (self-hosted runner on the same host as        │
│                   Parasoft Virtualize)                          │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  scripts/agent.py  (Claude + MCP agentic loop)         │    │
│  │                                                         │    │
│  │   ┌──────────────────┐    ┌──────────────────────────┐ │    │
│  │   │  Jira MCP Server │    │  Virtualize MCP Server   │ │    │
│  │   │  (cloud / stdio) │    │  (local SSE endpoint)    │ │    │
│  │   │                  │    │                          │ │    │
│  │   │  • get_issue     │    │  • list_virtual_services │ │    │
│  │   │  • search_issues │    │  • create_virtual_service│ │    │
│  │   │  • …             │    │  • deploy / start / stop │ │    │
│  │   └──────────────────┘    └──────────────────────────┘ │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

1. You trigger the workflow (`workflow_dispatch`) with a Jira ticket number.
2. Claude reads the story via the **Jira MCP Server** (Atlassian Cloud).
3. Claude extracts the API specification from the story and calls the
   **Parasoft Virtualize MCP Server** (running locally on the runner) to
   create and deploy the virtual service.
4. A summary is uploaded as a workflow artifact.

---

## Repository layout

```
.
├── .github/
│   └── workflows/
│       └── create-virtual-service.yml   # GitHub Actions workflow
├── scripts/
│   └── agent.py                         # AI agent orchestration script
├── docs/
│   ├── setup.md                         # Full setup guide
│   └── jira-story-format.md             # Required Jira story structure
├── mcp.json                             # MCP server connection configuration
├── requirements.txt                     # Python dependencies
└── .env.example                         # Environment variable template
```

---

## Quick start

### 1 — Prerequisites

| Requirement | Notes |
|---|---|
| Self-hosted GitHub Actions runner | Must be on the same machine as Parasoft Virtualize |
| Parasoft Virtualize | With the MCP Server enabled and running |
| Anthropic API key | [console.anthropic.com](https://console.anthropic.com) |
| Atlassian Jira Cloud | API token from [id.atlassian.com](https://id.atlassian.com/manage-profile/security/api-tokens) |
| Python 3.11+ | Installed on the runner |
| Node.js 20+ | Required to run the Jira MCP Server via `npx` |

### 2 — Configure GitHub Secrets

Add the following secrets in **Settings → Secrets and variables → Actions**:

| Secret | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Claude API key |
| `ATLASSIAN_SITE_NAME` | Jira subdomain (e.g. `acme` for `acme.atlassian.net`) |
| `ATLASSIAN_USER_EMAIL` | Your Atlassian account email |
| `ATLASSIAN_API_TOKEN` | Atlassian API token |
| `PARASOFT_VIRTUALIZE_MCP_URL` | URL of the Virtualize MCP Server SSE endpoint (e.g. `http://localhost:4000/sse`) |
| `PARASOFT_VIRTUALIZE_URL` | Base URL of the Virtualize server (e.g. `http://localhost:9080`) |
| `PARASOFT_VIRTUALIZE_USER` | Virtualize username |
| `PARASOFT_VIRTUALIZE_PASSWORD` | Virtualize password |

### 3 — Configure MCP servers

Edit **`mcp.json`** if you need to change:
- The Jira MCP server package or startup arguments
- The Virtualize MCP server transport type (`stdio` vs `sse`) or URL

### 4 — Write your Jira story

See **[docs/jira-story-format.md](docs/jira-story-format.md)** for the
recommended story structure that gives the agent everything it needs.

### 5 — Run the workflow

Go to **Actions → Create Virtual Service from Jira Story → Run workflow**,
enter your Jira ticket number, and click **Run workflow**.

---

## Customisation

- **Different LLM**: change `CLAUDE_MODEL` in `scripts/agent.py`.
- **Different Jira MCP server**: update the `jira` entry in `mcp.json`.
- **Virtualize MCP server over stdio**: change `transport` to `"stdio"` and
  add `command`/`args` in `mcp.json`.
- **Additional workflow triggers** (e.g. on issue label): extend the `on:`
  block in `.github/workflows/create-virtual-service.yml`.

---

## Detailed setup

See **[docs/setup.md](docs/setup.md)** for step-by-step instructions including
self-hosted runner registration and Parasoft Virtualize MCP Server configuration.
