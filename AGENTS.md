# Project Coding Workflow

These instructions apply only to this repository.

## Mandatory pre-coding checks

For every request that will write or modify code:

1. Identify the technologies, libraries, APIs, and tools involved.
2. Check that the `context7` MCP server is available.
3. Use Context7 to resolve the relevant library or project and query current documentation and best practices.
4. Use the project-local `find-skills` skill by running a focused `npx skills find <query>` search for relevant skills.
5. Apply the results to the implementation plan.
6. Only then write or modify code.

If Context7 or `find-skills` is unavailable, report that precondition before coding and do not claim the lookup was completed.

Read-only inspection and non-coding explanations do not require these checks unless the request later becomes a coding change.
