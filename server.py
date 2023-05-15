import sys
import time
import signal
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
    page = context.pages[0]
    page.goto(settings.base_url)
    return context


def heart_beat():
    global playwright
    if not settings.heart_beat:
        return
    global context
    try:
        _logger.info(f"server heart_beat: {settings.heart_beat}")
        page = context.pages[0]
        page.reload(wait_until="commit")
    except Exception as e:
        _logger.exception(e)
        try:
            context.close()
        except Exception as e:
            _logger.exception(e)
        _logger.info("Relaunching context")
        context = launch_context(playwright)


def checkbox():
    global playwright
    if not settings.heart_beat:
        return
    global context
    try:
        page = context.pages[0]
        handle = page.query_selector(
            '//iframe[contains(@src, "cloudflare")]')
        owner_frame = handle.content_frame()
        owner_frame.click(
            '//input[@type="checkbox"]',
            timeout=1000
        )
    except Exception:
        _logger.debug("Checkbox not found")


def shutdown(signal, frame):
    _logger.info('Shutting down...')
    with open(settings.server_state, "w") as f:
        f.write("stopping")
    global running
    running = False
    time.sleep(5)
    _logger.info('Shutdown complete')
    sys.exit(0)


if __name__ == "__main__":
    with open(settings.server_state, "w") as f:
        f.write("starting")
    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)
    playwright = sync_playwright().start()
    context = launch_context(playwright)
    running = True
    heart_beat()
    with open(settings.server_state, "w") as f:
        f.write("running")
    schedule.every(settings.heart_beat).seconds.do(heart_beat)
    schedule.every(1).seconds.do(checkbox)
    while running:
        schedule.run_pending()
        time.sleep(1)
