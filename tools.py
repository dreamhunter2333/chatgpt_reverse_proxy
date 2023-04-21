import logging
import asyncio

from playwright.async_api import Page

from config import settings

_logger = logging.getLogger(__name__)
refersh_access_token_lock = asyncio.Lock()
handle_checkbox_lock = asyncio.Lock()
ACCESS_TOKEN = None


class Tools:

    @staticmethod
    def get_access_token():
        return ACCESS_TOKEN

    @staticmethod
    async def refersh_access_token(page: Page):
        global ACCESS_TOKEN
        async with refersh_access_token_lock:
            if not settings.auto_refersh_access_token or ACCESS_TOKEN:
                return
            await page.goto(settings.base_url)
            try:
                async with page.expect_response("https://chat.openai.com/api/auth/session") as session:
                    value = await session.value
                    value_json = await value.json()
                    ACCESS_TOKEN = value_json["accessToken"]
                    _logger.info("Refreshed access token")
                    return
            except Exception as e:
                _logger.exception("Failed to refresh access token", e)

    @staticmethod
    async def handle_checkbox(page: Page):
        async with handle_checkbox_lock:
            try:
                await page.locator('//iframe[contains(@src, "cloudflare")]').wait_for(timeout=settings.checkbox_timeout)
                handle = await page.query_selector('//iframe[contains(@src, "cloudflare")]')
                await handle.wait_for_element_state(
                    "visible", timeout=settings.checkbox_timeout
                )
                owner_frame = await handle.content_frame()
                await owner_frame.click(
                    '//input[@type="checkbox"]',
                    timeout=settings.checkbox_timeout
                )
            except Exception as e:
                _logger.exception("Checkbox not found", e)
