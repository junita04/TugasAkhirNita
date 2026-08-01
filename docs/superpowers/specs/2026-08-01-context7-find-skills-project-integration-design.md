# Context7 and Find-Skills Project Integration Design

**Date:** 2026-08-01
**Scope:** `D:\TugasAkhirNita` only

## Goal

Configure this workspace to use Context7 for documentation and best-practice lookup and Vercel's `find-skills` for relevant skill discovery before coding work begins, without changing Codex behavior for other projects.

## Architecture

The project will contain three project-local integration points:

1. `.codex/config.toml` registers Context7 as a stdio MCP server using `npx -y @upstash/context7-mcp`.
2. `.agents/skills/find-skills/` contains the project-scoped Vercel `find-skills` skill installed with `npx skills add ... --skill find-skills`.
3. Root `AGENTS.md` defines the mandatory coding workflow: verify Context7 availability and consult relevant documentation/best practices, then search for relevant skills with `find-skills`, and only then write or modify code.

The configuration is intentionally stored under the repository root. No global Codex configuration, global skill directory, or other workspace will be modified.

## Required Workflow

For every coding request in this project:

1. Inspect the request and identify the frameworks, libraries, APIs, or tools involved.
2. Use the Context7 MCP server to resolve the relevant library/project and query current documentation and best practices.
3. Use the installed `find-skills` workflow to search for a relevant skill using a focused query.
4. Record or apply the findings to the implementation approach.
5. Only after steps 2-3 succeed, write or modify code.
6. If either service is unavailable, report the limitation before coding and do not claim that the required lookup was completed.

Non-coding questions and read-only repository inspection do not require this coding gate unless they lead into code changes.

## Installation and Verification

The implementation will install `find-skills` with project scope from the requested Vercel repository URL. Context7 will be configured as an on-demand stdio MCP server so `npx` can resolve the current package without a global installation.

Verification will check:

- the project-local MCP configuration parses and names the Context7 server;
- `npx skills list` reports the project-local `find-skills` installation;
- `AGENTS.md` contains the mandatory ordering and failure behavior;
- no global Codex configuration is changed.

## Error Handling and Security

No secrets will be committed. If Context7 credentials are needed for higher rate limits, they must be supplied through the user's environment or local untracked configuration. The MCP command is restricted to the Context7 package, and the skill installation targets only this repository.

## Out of Scope

- changing application code or runtime services;
- installing either integration globally;
- automatically enforcing the workflow through a custom wrapper or hook;
- modifying other repositories or Codex global preferences.
