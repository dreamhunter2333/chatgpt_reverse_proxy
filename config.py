import logging
from pydantic import BaseSettings

_logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s: %(levelname)s: %(name)s: %(message)s",
    level=logging.INFO
)


class Settings(BaseSettings):
    base_url: str = "https://chat.openai.com"
    proxy: str = ""
    auto_refersh_access_token: bool = False
    user_data_dir: str = "tmp/.playwright"
    browser_server: str = "http://localhost:9999"
    headless: bool = False
    heart_beat: int = 600
    timeout: int = 10000
    navigation_timeout: int = 10000
    checkbox_timeout: int = 30000
    server_state: str = "/tmp/server_state"

    class Config:
        env_file = ".env"


settings = Settings()
_logger.info(settings)
