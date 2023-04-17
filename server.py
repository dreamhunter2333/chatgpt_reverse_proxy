import time
import logging
import schedule

from playwright.sync_api import sync_playwright, BrowserContext, ProxySettings

from config import settings


_logger = logging.getLogger(__name__)


def launch_persistent_context(playwright) -> "BrowserContext":
    return playwright.chromium.launch_persistent_context(
        base_url=settings.base_url,
        user_data_dir=settings.user_data_dir,
        headless=settings.headless,
        timeout=settings.timeout,
        proxy=ProxySettings(server=settings.proxy) if settings.proxy else None,
        args=[
            '--no-sandbox',
            '--remote-debugging-port=9999',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--window-size=1920,1080',
            '--start-maximized',
            '--disable-blink-features=AutomationControlled',
            '--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
        ])


def launch_context(playwright) -> "BrowserContext":
    context = launch_persistent_context(playwright)
    context.set_default_navigation_timeout(settings.navigation_timeout)
    context.set_default_timeout(settings.timeout)
    return context


def heart_beat():
    global playwright
    if not settings.heart_beat:
        return
    global context
    try:
        page = context.pages[0]
        page.goto(settings.base_url)
        page.wait_for_timeout(50000)
        checkbox = page.locator('//input[@type="checkbox"]')
        if checkbox.count():
            checkbox.click()
    except Exception as e:
        _logger.exception(e)
        try:
            context.close()
        except Exception as e:
            _logger.exception(e)
        _logger.info("Relaunching context")
        context = launch_context(playwright)


if __name__ == "__main__":
    playwright = sync_playwright().start()
    context = launch_context(playwright)
    schedule.every(settings.heart_beat).seconds.do(heart_beat)
    while True:
        schedule.run_pending()
        time.sleep(1)
