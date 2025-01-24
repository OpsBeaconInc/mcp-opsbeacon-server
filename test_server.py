import asyncio
from mcp_opsbeacon_server.server import OpsbeaconClient
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)

async def test_client():
    print("Testing Opsbeacon Client...")
    
    try:
        # Initialize client - this will attempt to read the token from config
        client = OpsbeaconClient()
        print(f"Token loaded successfully: {client.token[:5]}...")  # Show first 5 chars of token
        
        # Test list_commands
        print("\nTesting list_commands:")
        commands = await client.list_commands()
        if isinstance(commands, dict) and 'error' in commands:
            print(f"Error response: {commands}")
        else:
            print(f"Commands retrieved successfully: {len(commands) if commands else 0} commands found")
            print("Raw response:", commands)
        
        # Test list_connections
        print("\nTesting list_connections:")
        connections = await client.list_connections()
        if isinstance(connections, dict) and 'error' in connections:
            print(f"Error response: {connections}")
        else:
            print(f"Connections retrieved successfully: {len(connections) if connections else 0} connections found")
            print("Raw response:", connections)
        
    except ValueError as e:
        print(f"Configuration error: {str(e)}")
    except Exception as e:
        print(f"Error during testing: {str(e)}")
    finally:
        if 'client' in locals():
            await client.close()

if __name__ == "__main__":
    asyncio.run(test_client())