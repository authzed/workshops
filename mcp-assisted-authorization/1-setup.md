# Part 1 — Setup and First Run

## Overview

This part guides you through installing and running the SpiceDB Dev MCP Server and connecting tools. You will:

- Install the Zed CLI
- Run the SpiceDB Dev MCP server
- Connect your AI coding assistant
- Connect the AuthZed MCP server
- Validate that everything is working

## 1. Install Dependencies

### Install Zed CLI

The development server relies on the Zed CLI.

Most systems:

```
brew install authzed/tap/zed
```

Verify:

```
zed version
```

## 2. Run the Local Development Server

Start an in-memory SpiceDB instance:

```
zed mcp experimental-run
```

It will start on:

```
http://localhost:9999/mcp
```

Important notes:

- In-memory only
- All schemas and relationships are lost on shutdown
- No external dependencies

Keep this terminal open.

## 3. Connect Your MCP Client

Pick one:

### Claude Code

```
claude mcp add --transport http spicedb http://localhost:9999/mcp
```

Restart Claude Code.

### ChatGPT (Pro/Plus)

Enable Developer Mode, then add connector:

- Name: spicedb
- URL: http://localhost:9999/mcp

### VS Code with Copilot

Command Palette → MCP: Add Server

- Transport: HTTP
- URL: http://localhost:9999/mcp
- Name: spicedb

## 4. Connect the AuthZed MCP Server

Add this remote server:

- Name: authzed
- URL: https://mcp.authzed.com

No authentication required.

## 5. Validate

Ask your assistant:

```
What MCP servers are available?
```

You should see:

- spicedb (local)
- authzed (remote)

Then test schema writing:

```
Write a minimal schema with a single resource and permission.
```

## 6. Separation of Roles

| Server | Purpose |
|---|---|
| SpiceDB Dev MCP Server | Local development and testing |
| AuthZed MCP Server | Documentation, concepts, examples |

Typical workflow:

```
Ask AuthZed for a pattern
Build/test it locally with SpiceDB
Export to file when done
```

## Completion Milestone: Part 1

You have:

- Installed Zed
- Run the dev server
- Connected tools
- Written a first schema

