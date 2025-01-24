"""MCP server for Opsbeacon operations."""
from . import server
import asyncio

def main():
    """Main entry point for the package."""
    try:
        asyncio.run(server.main())
    except KeyboardInterrupt:
        pass  # Handle graceful shutdown on Ctrl+C
    except Exception as e:
        print(f"Error running server: {e}")
        raise

if __name__ == "__main__":
    main()

__all__ = ["main", "server"]