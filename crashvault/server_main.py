"""Entry point for running the server as a module: python -m crashvault.server"""

import sys
from .server import run_server, DEFAULT_PORT

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PORT
    host = sys.argv[2] if len(sys.argv) > 2 else "0.0.0.0"
    run_server(port=port, host=host)
