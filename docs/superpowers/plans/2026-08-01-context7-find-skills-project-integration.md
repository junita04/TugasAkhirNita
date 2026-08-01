# Context7 and Find-Skills Project Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Install and configure Context7 and Vercel `find-skills` only for `D:\TugasAkhirNita`, and document a mandatory pre-coding lookup workflow.

**Architecture:** Use project-local `.codex/config.toml` for a stdio Context7 MCP server, project-local `.agents/skills/find-skills/` for the Vercel skill, and root `AGENTS.md` for the mandatory ordering and failure behavior. No global Codex files or other repositories are changed.

**Tech Stack:** Codex project configuration, TOML, Markdown, Node.js `npx`, `@upstash/context7-mcp`, Vercel Skills CLI.

## Global Constraints

- Scope is `D:\TugasAkhirNita` only.
- Context7 must be checked before writing or modifying code for coding requests.
- `find-skills` must be searched before writing or modifying code for coding requests.
- No secrets may be committed.
- Existing unrelated worktree changes must not be staged or modified.

---

### Task 1: Register the project-local Context7 MCP server

**Files:**
- Create: `.codex/config.toml`

**Interfaces:**
- Produces MCP server `context7` with command `npx`, arguments `-y @upstash/context7-mcp`.

- [ ] **Step 1: Create the project-local MCP configuration**

Write:

```toml
[mcp_servers.context7]
command = "npx"
args = ["-y", "@upstash/context7-mcp"]
```

- [ ] **Step 2: Validate the file contents**

Run:

```powershell
Get-Content -Raw .codex/config.toml
```

Expected: the `context7` MCP server is configured with the exact command and arguments above.

- [ ] **Step 3: Check the project-local configuration status**

Run:

```powershell
codex mcp list
```

Expected: the Context7 server is visible when Codex loads this workspace configuration. If the installed Codex CLI does not expose project-local servers in this command, record that limitation and validate the TOML structurally instead.

### Task 2: Install the project-local `find-skills` skill

**Files:**
- Create: `.agents/skills/find-skills/` (created by the CLI)

**Interfaces:**
- Produces the Vercel `find-skills` skill available to the Codex agent in this repository.

- [ ] **Step 1: Install only the requested skill with project scope**

Run from `D:\TugasAkhirNita`:

```powershell
npx skills add https://github.com/vercel-labs/skills --skill find-skills --agent codex --yes
```

Expected: installation completes under the repository's project skill directory, not the user-level skill directory.

- [ ] **Step 2: Verify the installed skill**

Run:

```powershell
npx skills list --agent codex
```

Expected: `find-skills` is listed as a project-local skill.

- [ ] **Step 3: Verify the skill metadata**

Run:

```powershell
Get-Content -Raw .agents/skills/find-skills/SKILL.md
```

Expected: the file contains the `find-skills` name and instructions for `npx skills find`.

### Task 3: Add the mandatory project workflow

**Files:**
- Create: `AGENTS.md`

**Interfaces:**
- Consumes: Context7 MCP server and project-local `find-skills` skill from Tasks 1-2.
- Produces: always-on project instructions for coding requests in this repository.

- [ ] **Step 1: Write the project instructions**

Create `AGENTS.md` with these requirements:

```markdown
# Project Coding Workflow

These instructions apply only to this repository.

## Mandatory pre-coding checks

For every request that will write or modify code:

1. Identify the technologies, libraries, APIs, and tools involved.
2. Check that the `context7` MCP server is available.
3. Use Context7 to resolve the relevant library/project and query current documentation and best practices.
4. Use the project-local `find-skills` skill by running a focused `npx skills find <query>` search for relevant skills.
5. Apply the results to the implementation plan.
6. Only then write or modify code.

If Context7 or `find-skills` is unavailable, report that precondition before coding and do not claim the lookup was completed.

Read-only inspection and non-coding explanations do not require these checks unless the request later becomes a coding change.
```

- [ ] **Step 2: Verify ordering and scope**

Run:

```powershell
Select-String -Path AGENTS.md -Pattern 'Context7','find-skills','Only then write','only this repository'
```

Expected: all mandatory workflow terms are present and the instructions explicitly limit scope to this repository.

### Task 4: Run final integration verification

**Files:**
- Verify: `.codex/config.toml`
- Verify: `.agents/skills/find-skills/SKILL.md`
- Verify: `AGENTS.md`

- [ ] **Step 1: Confirm only intended new files are present**

Run:

```powershell
git status --short
```

Expected: the three integration paths appear as new files/directories; unrelated existing changes remain untouched and unstaged.

- [ ] **Step 2: Check the diff for formatting errors**

Run:

```powershell
git diff --check -- AGENTS.md .codex/config.toml
```

Expected: no whitespace errors.

- [ ] **Step 3: Verify no global Codex configuration was modified**

Run:

```powershell
git diff --no-index -- /dev/null C:\Users\HP\.codex\config.toml
```

Expected: this command is not used as a mutation; inspect only that the global file was not part of the repository diff. Do not edit it.

- [ ] **Step 4: Commit only the integration files**

Run:

```powershell
git add AGENTS.md .codex/config.toml .agents/skills/find-skills
git commit -m "chore: add project-local context7 and skills workflow"
```

Expected: only the project-local integration files are committed; unrelated worktree changes remain uncommitted.
