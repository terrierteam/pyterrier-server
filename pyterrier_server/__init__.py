"""Top-level package for PyTerrier Serve."""

__version__ = '0.1.0'

import os
import sys
import logging
from dotenv import load_dotenv

load_dotenv()

def _setup_logging():
    """Configure root logger with separate file for MCP if enabled.

    Controlled by environment variables:
      - PYTERRIER_SERVER_LOG_LEVEL (default: INFO)
      - PYTERRIER_SERVER_LOG_FILE  (default: <package_parent>/pyterrier_server.log)
      - PYTERRIER_MCP              (if set, logs go to <package_parent>/pyterrier_mcp.log)
    """
    root = logging.getLogger()

    if getattr(root, "_pyterrier_serve_configured", False):
        return

    level_name = os.environ.get("PYTERRIER_SERVER_LOG_LEVEL", "INFO").upper()
    try:
        level = getattr(logging, level_name)
    except Exception:
        level = logging.INFO

    pkg_parent = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    # Switch log file if MCP server is running
    if os.environ.get("PYTERRIER_MCP", "").lower() in ['1', 'true', 'yes']:
        default_logfile = os.path.join(pkg_parent, "pyterrier_mcp.log")
    else:
        default_logfile = os.environ.get("PYTERRIER_SERVER_LOG_FILE",
                                         os.path.join(pkg_parent, "pyterrier_server.log"))

    # Clear existing handlers
    for h in list(root.handlers):
        root.removeHandler(h)

    root.setLevel(level)

    fmt = logging.Formatter(fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s",
                            datefmt="%Y-%m-%d %H:%M:%S")

    # Stream handler
    sh = logging.StreamHandler(stream=sys.stdout)
    sh.setFormatter(fmt)
    sh.setLevel(logging.NOTSET)
    root.addHandler(sh)

    # File handler
    try:
        fh = logging.FileHandler(default_logfile, encoding="utf-8")
        fh.setFormatter(fmt)
        fh.setLevel(logging.NOTSET)
        root.addHandler(fh)
    except Exception:
        root.exception("Could not create log file handler; continuing without file logging")

    root._pyterrier_serve_configured = True
    root.debug(f"pyterrier_server logging configured (level={level_name}, file={default_logfile})")

# Configure logging on package import
_setup_logging()
