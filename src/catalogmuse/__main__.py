"""Run the agent service.

The Go backend calls this process. It does not serve the React app.
"""

from __future__ import annotations

import os

import uvicorn


def main() -> None:
    host = os.environ.get("CATALOGMUSE_HOST", "127.0.0.1")
    port = int(os.environ.get("CATALOGMUSE_PORT", "8790"))
    uvicorn.run("catalogmuse.app:app", host=host, port=port, factory=False)


if __name__ == "__main__":
    main()
