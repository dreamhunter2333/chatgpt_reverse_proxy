import logging
import uvicorn

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, Response
from playwright.sync_api import sync_playwright

from config import settings


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
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(
            settings.browser_server,
            timeout=settings.timeout
        )
        context = browser.contexts[0]
        api_request_context = context.request
        target_url = "https://chat.openai.com/backend-api" + request.url.path
        if request.url.query:
            target_url += "?" + request.url.query
        api_response = api_request_context.fetch(
            target_url, method=request.method, data=request.body()
        )
        return Response(
            headers=api_response.headers,
            content=api_response.body,
            status_code=api_response.status,
        )


app.add_route(
    "/api/{path:path}",
    _reverse_proxy,
    ["GET", "POST"]
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
