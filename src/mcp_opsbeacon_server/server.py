import logging
import os
import json
from pathlib import Path
import aiohttp
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio
from typing import Any
from pydantic import AnyUrl

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('mcp_opsbeacon_server')
logger.setLevel(logging.DEBUG)
logger.info("Starting MCP Opsbeacon Server")

class OpsbeaconClient:
    def __init__(self):
        self.token = self._get_token()
        self.base_url = "https://api.console-dev.opsbeacon.com"
        self.session = None
        self.initialized = False

    def _get_token(self) -> str:
        """Get bearer token from claude_desktop_config.json"""
        try:
            config_path = os.path.expanduser("~/Library/Application Support/Claude/claude_desktop_config.json")
            with open(config_path, 'r') as f:
                config = json.load(f)
                if (config.get('mcpServers') and 
                    config['mcpServers'].get('opsbeacon') and 
                    config['mcpServers']['opsbeacon'].get('env') and 
                    config['mcpServers']['opsbeacon']['env'].get('OPSBEACON_TOKEN')):
                    return config['mcpServers']['opsbeacon']['env']['OPSBEACON_TOKEN']
                else:
                    error_msg = "OPSBEACON_TOKEN not found in claude_desktop_config.json"
                    logger.error(error_msg)
                    raise ValueError(error_msg)
        except FileNotFoundError:
            error_msg = f"claude_desktop_config.json not found at {config_path}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        except json.JSONDecodeError:
            error_msg = "Invalid JSON in claude_desktop_config.json"
            logger.error(error_msg)
            raise ValueError(error_msg)
        except Exception as e:
            error_msg = f"Error reading token from config: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    async def _get_session(self):
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                }
            )
        return self.session

    async def list_commands(self) -> list[dict]:
        """List all available commands"""
        try:
            session = await self._get_session()
            async with session.get(f"{self.base_url}/workspace/v2/commands") as response:
                response.raise_for_status()
                text = await response.text()
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    logger.error(f"Non-JSON response from API: {text}")
                    return {"error": "Invalid response format", "response": text}
        except Exception as e:
            logger.error(f"Error listing commands: {e}")
            raise

    async def list_connections(self) -> list[dict]:
        """List all available connections"""
        try:
            session = await self._get_session()
            async with session.get(f"{self.base_url}/workspace/v2/connections") as response:
                response.raise_for_status()
                text = await response.text()
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    logger.error(f"Non-JSON response from API: {text}")
                    return {"error": "Invalid response format", "response": text}
        except Exception as e:
            logger.error(f"Error listing connections: {e}")
            raise

    async def get_execution_logs(self, start_date: str, end_date: str, page: int = 1, limit: int = 10) -> dict:
        """Get execution logs for a specific date range"""
        try:
            params = {
                'startDate': start_date,
                'endDate': end_date,
                'page': str(page),
                'limit': str(limit),
                'orderBy': 'timestamp',
                'direction': 'desc'
            }
            
            session = await self._get_session()
            async with session.get(f"{self.base_url}/workspace/v2/eventlogs", params=params) as response:
                response.raise_for_status()
                text = await response.text()
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    logger.error(f"Non-JSON response from API: {text}")
                    return {"error": "Invalid response format", "response": text}
        except Exception as e:
            logger.error(f"Error getting execution logs: {e}")
            raise

    async def execute_operation(self, connection: str, command: str, arguments: list[tuple[str, str]] = None) -> dict:
        """Execute an Opsbeacon operation"""
        try:
            # Build command line
            cmd_line = f"{connection} {command}"
            if arguments:
                for arg_name, arg_value in arguments:
                    cmd_line += f" --{arg_name} {arg_value}"

            payload = {
                "commandLine": cmd_line
            }
            
            logger.debug(f"Executing operation with payload: {payload}")
            
            session = await self._get_session()
            async with session.post(f"{self.base_url}/trigger/v1/api", json=payload) as response:
                response.raise_for_status()
                text = await response.text()
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    logger.error(f"Non-JSON response from API: {text}")
                    return {"error": "Invalid response format", "response": text}
        except Exception as e:
            logger.error(f"Error executing operation: {e}")
            raise

    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
            self.initialized = False

async def main():
    logger.info("Starting Opsbeacon MCP Server")

    client = OpsbeaconClient()
    server = Server("opsbeacon")

    # Register handlers
    logger.debug("Registering handlers")

    @server.list_resources()
    async def handle_list_resources() -> list[types.Resource]:
        logger.debug("Handling list_resources request")
        return []

    @server.read_resource()
    async def handle_read_resource(uri: AnyUrl) -> str:
        logger.debug(f"Handling read_resource request for URI: {uri}")
        raise ValueError(f"Unsupported URI: {uri}")

    @server.list_prompts()
    async def handle_list_prompts() -> list[types.Prompt]:
        logger.debug("Handling list_prompts request")
        return []

    @server.get_prompt()
    async def handle_get_prompt(name: str, arguments: dict[str, str] | None) -> types.GetPromptResult:
        logger.debug(f"Handling get_prompt request for {name} with args {arguments}")
        raise ValueError(f"Unknown prompt: {name}")

    @server.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        """List available tools"""
        logger.debug("Listing tools")
        return [
            types.Tool(
                name="list_commands",
                description="List all available Opsbeacon commands",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            types.Tool(
                name="list_connections",
                description="List all available Opsbeacon connections",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            types.Tool(
                name="execute",
                description="Execute an Opsbeacon operation",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "connection": {
                            "type": "string",
                            "description": "Name of the connection to use"
                        },
                        "command": {
                            "type": "string",
                            "description": "Name of the command to execute"
                        },
                        "arguments": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {
                                        "type": "string",
                                        "description": "Argument name"
                                    },
                                    "value": {
                                        "type": "string",
                                        "description": "Argument value"
                                    }
                                },
                                "required": ["name", "value"]
                            },
                            "description": "Optional list of arguments"
                        }
                    },
                    "required": ["connection", "command"]
                },
            ),
            types.Tool(
                name="executionlogs",
                description="Get execution logs for a specific date range",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "interval": {
                            "type": "string",
                            "description": "Time interval (e.g., 'last week', 'last month', 'last 3 days')"
                        },
                        "page": {
                            "type": "integer",
                            "description": "Page number",
                            "default": 1
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of logs per page",
                            "default": 10
                        }
                    },
                    "required": ["interval"]
                },
            )
        ]

    @server.call_tool()
    async def handle_call_tool(
        name: str, arguments: dict[str, Any] | None
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        """Handle tool execution requests"""
        logger.debug(f"Tool '{name}' called with arguments: {arguments}")
        try:
            match name:
                case "list_commands":
                    try:
                        commands = await client.list_commands()
                        return [
                            types.TextContent(
                                type="text", 
                                text=str(commands),
                                artifact={"type": "json", "data": commands}
                            )
                        ]
                    except Exception as e:
                        logger.error(f"Error in list_commands: {e}")
                        return [types.TextContent(type="text", text=f"Error listing commands: {str(e)}")]
                
                case "list_connections":
                    try:
                        connections = await client.list_connections()
                        return [
                            types.TextContent(
                                type="text",
                                text=str(connections),
                                artifact={"type": "json", "data": connections}
                            )
                        ]
                    except Exception as e:
                        logger.error(f"Error in list_connections: {e}")
                        return [types.TextContent(type="text", text=f"Error listing connections: {str(e)}")]
                
                case "execute":
                    try:
                        if not arguments:
                            raise ValueError("Missing required arguments")
                        
                        connection = arguments.get("connection")
                        command = arguments.get("command")
                        if not connection or not command:
                            raise ValueError("Both connection and command are required")
                        
                        # Convert arguments list to tuples if provided
                        arg_list = None
                        if "arguments" in arguments and arguments["arguments"]:
                            arg_list = [(arg["name"], arg["value"]) for arg in arguments["arguments"]]
                        
                        result = await client.execute_operation(connection, command, arg_list)
                        return [
                            types.TextContent(
                                type="text",
                                text=str(result),
                                artifact={"type": "json", "data": result}
                            )
                        ]
                    except Exception as e:
                        logger.error(f"Error in execute: {e}")
                        return [types.TextContent(type="text", text=f"Error executing operation: {str(e)}")]
                
                case "executionlogs":
                    try:
                        if not arguments or "interval" not in arguments:
                            raise ValueError("Missing required interval argument")

                        from datetime import datetime, timedelta
                        today = datetime.now()
                        
                        # Parse the interval
                        interval = arguments["interval"].lower()
                        if "last week" in interval:
                            start_date = today - timedelta(days=7)
                        elif "last month" in interval:
                            start_date = today - timedelta(days=30)
                        elif "last" in interval and "days" in interval:
                            try:
                                days = int(''.join(filter(str.isdigit, interval)))
                                start_date = today - timedelta(days=days)
                            except ValueError:
                                start_date = today - timedelta(days=7)  # Default to a week
                        else:
                            start_date = today - timedelta(days=7)  # Default to a week

                        # Format dates
                        start_date_str = start_date.strftime("%Y%m%d")
                        end_date_str = today.strftime("%Y%m%d")

                        # Get optional parameters
                        page = arguments.get("page", 1)
                        limit = arguments.get("limit", 10)

                        result = await client.get_execution_logs(
                            start_date_str,
                            end_date_str,
                            page,
                            limit
                        )
                        return [
                            types.TextContent(
                                type="text",
                                text=str(result),
                                artifact={"type": "json", "data": result}
                            )
                        ]
                    except Exception as e:
                        logger.error(f"Error in executionlogs: {e}")
                        return [types.TextContent(type="text", text=f"Error getting execution logs: {str(e)}")]

                case _:
                    logger.error(f"Unknown tool: {name}")
                    return [types.TextContent(type="text", text=f"Unknown tool: {name}")]

        except Exception as e:
            logger.error(f"Error in handle_call_tool: {e}")
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]

    try:
        logger.info("Starting server with stdio transport")
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            logger.info("Server running with stdio transport")
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="opsbeacon",
                    server_version="0.1.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise
    finally:
        await client.close()