#!/usr/bin/env python3
"""
agent.py — AI agent that reads a Jira user story and creates a virtual service
           on a locally-deployed Parasoft Virtualize server.

Flow:
  1. Load MCP server configuration from mcp.json
  2. Connect to the Jira MCP Server (cloud) and the Virtualize MCP Server (local)
  3. Collect all available tools from both servers
  4. Run an agentic loop with Claude — it reads the Jira story and calls
     Virtualize MCP tools to create and deploy the virtual service
  5. Write the final result to agent-output.json and agent-output.log
"""

import asyncio
import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any

import anthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("agent-output.log"),
    ],
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
MCP_CONFIG_FILE = REPO_ROOT / "mcp.json"

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
JIRA_TICKET = os.environ["JIRA_TICKET"]
DRY_RUN = os.environ.get("DRY_RUN", "false").lower() == "true"

CLAUDE_MODEL = "claude-opus-4-5"
MAX_TOKENS = 4096
MAX_AGENT_TURNS = 20

SYSTEM_PROMPT = """\
You are an expert DevOps automation engineer with deep knowledge of both
Atlassian Jira and Parasoft Virtualize.

Your task:
1. Read the Jira user story provided by the user (use the Jira MCP tools).
2. Analyze the story to extract all virtual service requirements — endpoint path,
   HTTP method(s), request/response schema, port, and any behavior rules.
3. Use the Parasoft Virtualize MCP tools to create and deploy a virtual service
   that satisfies those requirements.
4. Report a concise summary of what was created (service name, endpoint, port).

Guidelines:
- If information is missing from the Jira story, make reasonable defaults and
  note them in your final summary.
- If DRY_RUN is true, describe what you *would* create but do not call any
  Virtualize write/deploy tools.
- Always confirm successful deployment before finishing.
"""


def _expand_env(value: Any) -> Any:
    """Replace ${VAR} placeholders in a string with environment variable values."""
    if isinstance(value, str):
        return re.sub(
            r"\$\{([^}]+)\}",
            lambda m: os.environ.get(m.group(1), m.group(0)),
            value,
        )
    if isinstance(value, dict):
        return {k: _expand_env(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_expand_env(i) for i in value]
    return value


def _load_mcp_config() -> dict:
    """Load and expand mcp.json."""
    with open(MCP_CONFIG_FILE) as fh:
        raw = json.load(fh)
    return _expand_env(raw)


_EMPTY_SCHEMA: dict = {"type": "object", "properties": {}}


def _tools_to_claude(tools) -> list[dict]:
    """Convert MCP tool list to Anthropic tool format."""
    result = []
    for t in tools:
        schema = t.inputSchema if hasattr(t, "inputSchema") else _EMPTY_SCHEMA
        result.append(
            {
                "name": t.name,
                "description": t.description or "",
                "input_schema": schema,
            }
        )
    return result


async def _call_mcp_tool(
    name: str,
    arguments: dict,
    jira_session: ClientSession,
    virt_session: ClientSession,
    jira_tool_names: set[str],
    virt_tool_names: set[str],
) -> str:
    """Route a tool call to the correct MCP session and return the text result."""
    if name in jira_tool_names:
        session = jira_session
    elif name in virt_tool_names:
        session = virt_session
    else:
        return f"ERROR: unknown tool '{name}'"

    result = await session.call_tool(name, arguments)

    # Flatten content to a plain string
    parts = []
    for block in result.content:
        if hasattr(block, "text"):
            parts.append(block.text)
        else:
            parts.append(str(block))
    return "\n".join(parts)


async def run_agent(
    jira_session: ClientSession,
    virt_session: ClientSession,
    jira_tool_names: set[str],
    virt_tool_names: set[str],
    all_claude_tools: list[dict],
) -> str:
    """Run the agentic loop and return the final assistant message."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    user_content = (
        f"Jira ticket: {JIRA_TICKET}\n"
        f"Dry run: {DRY_RUN}\n\n"
        "Please read this Jira story and create the virtual service it describes."
    )

    messages: list[dict] = [{"role": "user", "content": user_content}]
    final_text = ""

    for turn in range(MAX_AGENT_TURNS):
        log.info("Agent turn %d/%d", turn + 1, MAX_AGENT_TURNS)

        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            tools=all_claude_tools,
            messages=messages,
        )

        # Collect all content blocks into the message history
        assistant_blocks = []
        tool_uses = []

        for block in response.content:
            assistant_blocks.append(block)
            if block.type == "text":
                final_text = block.text
                log.info("Assistant: %s", block.text[:200])
            elif block.type == "tool_use":
                tool_uses.append(block)
                log.info("Tool call: %s(%s)", block.name, json.dumps(block.input)[:120])

        messages.append({"role": "assistant", "content": assistant_blocks})

        if response.stop_reason == "end_turn" or not tool_uses:
            log.info("Agent finished (stop_reason=%s)", response.stop_reason)
            break

        # Execute all tool calls and build tool-result blocks
        tool_results = []
        for tu in tool_uses:
            result_text = await _call_mcp_tool(
                tu.name,
                tu.input,
                jira_session,
                virt_session,
                jira_tool_names,
                virt_tool_names,
            )
            log.info("Tool result (%s): %s", tu.name, result_text[:200])
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": tu.id,
                    "content": result_text,
                }
            )

        messages.append({"role": "user", "content": tool_results})

    return final_text


async def main() -> None:
    log.info("Starting VirtualizeMCPDemo agent")
    log.info("Jira ticket : %s", JIRA_TICKET)
    log.info("Dry run     : %s", DRY_RUN)

    config = _load_mcp_config()
    servers = config["mcpServers"]

    jira_cfg = servers["jira"]
    virt_cfg = servers["virtualize"]

    # ------------------------------------------------------------------
    # Open connections to both MCP servers
    # ------------------------------------------------------------------
    async def _connect_stdio(cfg: dict):
        env = {**os.environ, **cfg.get("env", {})}
        params = StdioServerParameters(
            command=cfg["command"],
            args=cfg.get("args", []),
            env=env,
        )
        return stdio_client(params)

    async def _connect_sse(cfg: dict):
        return sse_client(cfg["url"])

    log.info("Connecting to Jira MCP Server …")
    jira_transport_ctx = (
        await _connect_stdio(jira_cfg)
        if jira_cfg["transport"] == "stdio"
        else await _connect_sse(jira_cfg)
    )

    log.info("Connecting to Virtualize MCP Server …")
    virt_transport_ctx = (
        await _connect_stdio(virt_cfg)
        if virt_cfg["transport"] == "stdio"
        else await _connect_sse(virt_cfg)
    )

    async with jira_transport_ctx as (jira_r, jira_w):
        async with ClientSession(jira_r, jira_w) as jira_session:
            await jira_session.initialize()
            jira_tools_resp = await jira_session.list_tools()
            jira_tool_names = {t.name for t in jira_tools_resp.tools}
            log.info("Jira tools available: %s", sorted(jira_tool_names))

            async with virt_transport_ctx as (virt_r, virt_w):
                async with ClientSession(virt_r, virt_w) as virt_session:
                    await virt_session.initialize()
                    virt_tools_resp = await virt_session.list_tools()
                    virt_tool_names = {t.name for t in virt_tools_resp.tools}
                    log.info("Virtualize tools available: %s", sorted(virt_tool_names))

                    all_claude_tools = _tools_to_claude(
                        jira_tools_resp.tools + virt_tools_resp.tools
                    )

                    # --------------------------------------------------
                    # Run the agent
                    # --------------------------------------------------
                    final_summary = await run_agent(
                        jira_session,
                        virt_session,
                        jira_tool_names,
                        virt_tool_names,
                        all_claude_tools,
                    )

    # ------------------------------------------------------------------
    # Write output artifacts
    # ------------------------------------------------------------------
    output = {
        "jira_ticket": JIRA_TICKET,
        "dry_run": DRY_RUN,
        "summary": final_summary,
    }
    output_path = Path("agent-output.json")
    output_path.write_text(json.dumps(output, indent=2))
    log.info("Results written to %s", output_path)
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(final_summary)


if __name__ == "__main__":
    asyncio.run(main())
