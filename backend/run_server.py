import sys
import asyncio
import selectors

if sys.platform == "win32":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception:
        pass

import uvicorn

async def main():
    config = uvicorn.Config("app.main:app", host="0.0.0.0", port=8000, loop="asyncio")
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    if sys.platform == "win32":
        try:
            asyncio.run(main(), loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()))
        except TypeError:
            asyncio.run(main())
    else:
        asyncio.run(main())
