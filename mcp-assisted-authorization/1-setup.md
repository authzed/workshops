# Part 1 — Setup and First Run

In this step, we'll install the SpiceDB Dev MCP Server and the AuthZed MCP Server and connect the two to the coding assistant of your choice.

## 1. Run the Local Development Server

Install [Zed](https://github.com/authzed/zed) - the command line client for managing SpiceDB

We'll start by using the SpiceDB Dev MCP Server. This is a local development tool that runs an in-memory SpiceDB instance accessible through MCP. It’s designed to iterate quickly on schemas and test permission logic with AI assistance.

Lets start an in-memory SpiceDB instance:

```
zed mcp experimental-run
```

It will start on `http://localhost:9999/mcp` with an empty in-memory SpiceDB instance.

**Important:** The server runs in-memory only. All schemas and relationships are lost when you stop the server.

Keep this terminal open and notice the updates when you run the commands later in the workshop.

## 3. Connect Your MCP Client

Pick one:

### a. Claude Code

```
claude mcp add --transport http spicedb http://localhost:9999/mcp
```

Restart Claude Code.

### b. ChatGPT (Pro/Plus)

Enable Developer Mode, then add connector:

- Name: spicedb
- URL: http://localhost:9999/mcp

### c. VSCode with Copilot

Command Palette → MCP: Add Server

- Transport: HTTP
- URL: http://localhost:9999/mcp
- Name: spicedb

## 4. Connect the AuthZed MCP Server

The AuthZed MCP Server is a remote MCP server that provides tools with searchable access to SpiceDB and AuthZed resources to learn about authorization systems, explore APIs, and find implementation examples without leaving your LLM chat or development environment.

To use it, add this remote MCP server:

- Name: authzed
- URL: https://mcp.authzed.com

There's no authentication required.

## 5. Validate

Ask your AI assistant:

```
What MCP servers are available?
```

You should see:

- spicedb (local)
- authzed (remote)

## 6. Separation of Roles

| Server | Purpose |
|---|---|
| SpiceDB Dev MCP Server | Local development and testing |
| AuthZed MCP Server | Documentation, concepts, examples |

Typical workflow:

```
1. Ask AuthZed for a pattern
2. Build/test it locally with SpiceDB
3. Export to file when done
4. ??? (maybe deploy to AuthZed Cloud?)
5. PROFIT
```

## Completion Milestone: Part 1

You have:

- Installed Zed
- Added two MCP Servers
- Connected them to your AI assistant

In [Step 2](/2-schema.md), we'll being adding schema, relations and permissions.

