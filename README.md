# BreachHound MCP demo

Companion repo for the Apify Content Program article
*"I gave my SOC agent a tool to audit an email's digital footprint in one prompt."*

It shows how to expose the **BreachHound** Apify Actor (`blukaze/breachhound`)
to an AI client as a tool through the [Apify MCP server](https://docs.apify.com/integrations/mcp).

## What's here

- `example_agent.py` — standalone script that calls BreachHound through the Apify API.
  No MCP client required; useful to verify the Actor works.
- `verify_actor_call.py` — offline check (no token) that the code targets the right
  Actor with the right input and that the MCP configs parse.
- `claude_desktop_config.json` — local stdio MCP config for Claude Desktop.
- `cursor_mcp.json` — hosted `mcp.apify.com` config for Cursor / VS Code / Windsurf / Codex.

## Run the standalone example

```bash
pip install -r requirements.txt
export APIFY_TOKEN="apify-your-token-here"
python example_agent.py
```

Replace the sample email in `main()` with an address you are **authorized** to audit.

## Offline verification (no token)

```bash
python verify_actor_call.py
```

## Wire it into an agent

Hosted (recommended) — Antigravity and other native Streamable-HTTP clients connect directly to Apify; do NOT wrap it in `mcp-remote` (Apify's server requires the `Mcp-Method` header that `mcp-remote@latest` 0.1.38 omits, causing a `server/discover` `-32020` error). Use the exact form Apify's CLI writes:

```json
{
  "mcpServers": {
    "apify": {
      "url": "https://mcp.apify.com"
    }
  }
}
```

`apify login` then `apify mcp install antigravity` produces the same entry. Scope to specific Actors via the [Apify UI configurator](https://mcp.apify.com/).

Claude Desktop (caveat) — its app policy refuses email-enumeration lookups, so it won't invoke this tool even once connected. For the local stdio option only, use `claude_desktop_config.json` and set `APIFY_TOKEN` in the client's environment. Prefer a coding agent for the live demo.

## Legal and ethical use

BreachHound is built for authorized corporate security, identity verification, fraud
prevention, and M&A due diligence. Only audit email addresses you are authorized to
investigate. See the Actor's [README](https://apify.com/blukaze/breachhound) for the
full disclaimer.
