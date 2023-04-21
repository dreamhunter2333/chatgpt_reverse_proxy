import os
import json
import logging
import uvicorn

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, Response
from playwright.async_api import async_playwright

from config import settings

from tools import Tools

_logger = logging.getLogger(__name__)


class EndpointFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return all(
            path not in record.getMessage()
            for path in ("/docs", "/openapi.json")
        )


app = FastAPI()
logging.getLogger("uvicorn.access").addFilter(EndpointFilter())

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception):
    return PlainTextResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=f"Internal Server Error: {exc}",
    )


@app.get("/health_check")
async def health_check():
    res = False
    if os.path.exists(settings.server_state):
        with open(settings.server_state, "r") as f:
            res = f.read() == "running"
    if not res:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Server is not running",
        )
    return {"status": "ok"}


@app.get("/admin/refersh_access_token")
async def admin_refersh_access_token():
    Tools.refersh_access_token()
    _logger.info("Refreshed access token")
    return {"status": "ok"}


async def _reverse_proxy(request: Request):
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(
            settings.browser_server,
            timeout=settings.timeout
        )
        context = browser.contexts[0]
        page = context.pages[0]
        await Tools.refersh_access_token(page)

        access_token = (
            f"Bearer {Tools.get_access_token()}"
            if Tools.get_access_token() else
            request.headers.get("Authorization")
        )

        body = await request.body()
        body = (
            "null"
            if request.method.upper() in ("GET", "DELETE")
            else f"{json.dumps(body.decode(), ensure_ascii=False)}"
        )
        target_path = f"{request.url.path}?{request.url.query}" if request.url.query else request.url.path
        script = '''
            async () => {
                response = await fetch("https://chat.openai.com%s", {
                    "headers": {
                        "accept": "*/*",
                        "authorization": "%s",
                        "content-type": "application/json",
                    },
                    "referrer": "https://chat.openai.com/",
                    "referrerPolicy": "same-origin",
                    "body": %s,
                    "method": "%s",
                    "mode": "cors",
                    "credentials": "include"
                });
                return {
                    status: response.status,
                    statusText: response.statusText,
                    headers: response.headers,
                    content: await response.text()
                }
            }
            ''' % (target_path, access_token, body, request.method.upper())
        result = await page.evaluate(script)
        if result["status"] in (401, 403):
            page.reload(wait_until="domcontentloaded")
            result = await page.evaluate(script)
        if result["status"] in (401, 403):
            await Tools.handle_checkbox(page)
            result = await page.evaluate(script)
        if settings.auto_refersh_access_token and result["status"] in (401, 403):
            Tools.clear_access_token()
            await Tools.refersh_access_token(page)
            result = await page.evaluate(script)
        return Response(
            content=result["content"],
            status_code=result["status"],
            headers=result["headers"],
        )


app.add_route(
    "/backend-api/{path:path}",
    _reverse_proxy,
    ["GET", "POST", "DELETE", "PUT", "PATCH"]
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
