import time
import logging
import schedule

from playwright.sync_api import sync_playwright, BrowserContext

from config import settings


_logger = logging.getLogger(__name__)

playwright = sync_playwright().start()


def launch_persistent_context() -> "BrowserContext":
    return playwright.chromium.launch_persistent_context(
        base_url=settings.base_url,
        user_data_dir=settings.user_data_dir,
        headless=settings.headless,
        timeout=settings.timeout,
        args=[
            '--no-sandbox',
            '--remote-debugging-port=9222',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--window-size=1920,1080',
            '--start-maximized',
            '--blink-settings=imagesEnabled=false',
            '--disable-blink-features=AutomationControlled',
            '--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.87 Safari/537.36',
        ])


def launch_context() -> "BrowserContext":
    context = launch_persistent_context()
    context.set_default_navigation_timeout(settings.navigation_timeout)
    context.set_default_timeout(settings.timeout)
    return context


context = launch_context()


def heart_beat():
    if not settings.heart_beat:
        return
    global context
    try:
        context.new_page().close()
    except Exception as e:
        _logger.exception(e)
        try:
            context.close()
        except Exception as e:
            _logger.exception(e)
        _logger.info("Relaunching context")
        context = launch_context()


schedule.every(10).seconds.do(heart_beat)

while True:
    schedule.run_pending()
    time.sleep(1)
