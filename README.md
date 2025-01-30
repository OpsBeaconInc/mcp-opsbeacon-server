# MCP Opsbeacon Server

An MCP (Model Context Protocol) server implementation for Opsbeacon operations. This server allows you to interact with the Opsbeacon API through Claude, providing tools for listing commands and connections.

## Features

- List available Opsbeacon commands
- List available Opsbeacon connections
- Authentication via bearer token
- Error handling and logging
- Returns structured JSON responses

## Prerequisites

- Python 3.10 or higher
- Access to Opsbeacon API
- Valid bearer token

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd mcp-opsbeacon-server
```

2. Install the package:
```bash
pip install -e .
```

## Configuration

There are two ways to provide your Opsbeacon API token, depending on your use case:

### Option 1: Using with Claude Desktop
If you want to use the MCP server with Claude, add the token to Claude Desktop's config file:

```json
{
  "mcpServers": {
    "opsbeacon": {
      "command": "python",
      "args": [
        "-m",
        "mcp_opsbeacon_server"
      ],
      "env": {
        "OPSBEACON_TOKEN": "your-bearer-token-here"
      }
    }
  }
}
```

### Option 2: Using without Claude
If you want to use the MCP server directly (e.g., for testing or development), you can set the token as an environment variable:

```bash
export OPSBEACON_TOKEN="your-bearer-token-here"
```

You can use either option or both simultaneously. Just replace `your-bearer-token-here` with your actual Opsbeacon API bearer token.

## Testing

To test the server functionality using the provided test script, make sure you have set the OPSBEACON_TOKEN environment variable (Option 2 above), then run:

```bash
python test_server.py
```

## Usage

### Available Tools

1. `list_commands`
   - Lists all available Opsbeacon commands
   - No additional parameters required
   - Returns command details in JSON format

2. `list_connections`
   - Lists all available Opsbeacon connections
   - No additional parameters required
   - Returns connection details in JSON format

### Example Usage with Claude

```
Human: List all available Opsbeacon commands.
Claude: Let me help you list the available commands using the Opsbeacon MCP server.
```

## Error Handling

Common error cases:
1. `OPSBEACON_TOKEN environment variable is not set`: Make sure the token is properly configured in claude_desktop_config.json
2. `Error listing commands/connections`: Check your network connection and token validity
3. `Connection refused`: Make sure the Opsbeacon API is accessible

## Development

To add new features or modify existing ones:
1. Make your changes
2. Run the test script to verify functionality
3. Update documentation as needed