"""MCP Server para o Banco Nacional de Precedentes (BNP/PAGEA) do CNJ."""

from .server import mcp


def main():
    """Entry point para o servidor MCP."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
