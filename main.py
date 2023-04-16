import logging
import uvicorn

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, Response
from playwright.sync_api import sync_playwright

from config import settings
from server import launch_context

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


def _reverse_proxy(request: Request):
    global ACCESS_TOKEN
    with sync_playwright() as p:
        if settings.enable_browser_server:
            browser = p.chromium.connect_over_cdp(
                settings.browser_server,
                timeout=settings.timeout
            )
            context = browser.contexts[0]
            page = context.pages[0]
        else:
            context = launch_context(p)
            page = context.pages[0]
        #     page.goto(settings.base_url)
        #     page.wait_for_timeout(5000)
        #     checkbox = page.locator('//input[@type="checkbox"]')
        #     if checkbox.count():
        #         checkbox.click()

        # if not ACCESS_TOKEN:
        #     page.goto(settings.base_url)
        #     with page.expect_response("https://chat.openai.com/api/auth/session") as session:
        #         ACCESS_TOKEN = session.value.json()["accessToken"]
        # result = page.evaluate(
        #     f'fetch("https://chat.openai.com{request.url.path}",'
        #     '{"headers": {"accept": "*/*", '
        #     f'"authorization": "Bearer {ACCESS_TOKEN}", '
        #     '"content-type": "application/json", }, '
        #     '"referrer": "https://chat.openai.com/",'
        #     '"referrerPolicy": "same-origin",'
        #     '"body": null,'
        #     '"method": "GET",'
        #     '"mode": "cors",credentials": "include"})'
        # )
    result = page.evaluate(
        'fetch("http://baidu.com").then(response => response.text())')

    return result


app.add_route(
    "/backend-api/{path:path}",
    _reverse_proxy,
    ["GET", "POST"]


)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
