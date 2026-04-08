from __future__ import annotations

import os


if __name__ == "__main__":
    try:
        import uvicorn

        from email_intelligence.api import app as fastapi_app
    except ModuleNotFoundError:
        from email_intelligence.service import run_server

        run_server(host="127.0.0.1", port=8000)
    else:
        uvicorn.run(
            fastapi_app,
            host="0.0.0.0",
            port=int(os.getenv("PORT", "8000")),
        )
