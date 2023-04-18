import logging
import uvicorn

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, Response
from playwright.async_api import async_playwright

from config import settings

ACCESS_TOKEN = None


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


async def _reverse_proxy(request: Request):
    global ACCESS_TOKEN
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(
            settings.browser_server,
            timeout=settings.timeout
        )
        context = browser.contexts[0]
        page = context.pages[0]

        if settings.auto_refersh_access_token and not ACCESS_TOKEN:
            await page.goto(settings.base_url)
            try:
                checkbox = page.locator(
                    '//input[@type="checkbox"]'
                ).wait_for(
                    timeout=settings.checkbox_timeout
                )
                if checkbox.count():
                    checkbox.click()
            except Exception:
                pass
            async with page.expect_response("https://chat.openai.com/api/auth/session") as session:
                value = await session.value
                value_json = await value.json()
                ACCESS_TOKEN = value_json["accessToken"]

        access_token = (
            f"Bearer {ACCESS_TOKEN}"
            if ACCESS_TOKEN else
            request.headers.get("Authorization")
        )

        body = await request.body()
        body = (
            "null"
            if request.method.upper() in ("GET", "DELETE")
            else f"'{body.decode()}'"
        )
        target_path = f"{request.url.path}?{request.url.query}" if request.url.query else request.url.path
        result = await page.evaluate('''
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
        )
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
