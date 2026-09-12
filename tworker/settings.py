# tworker/settings.py
from dataclasses import dataclass
import config

@dataclass
class BotConfig:
    token: str
    channel_id: int
    super_admin_id: int
    bot_enabled: bool
    drainer_status: bool

@dataclass
class LinksConfig:
    manuals: str
    chat: str
    payouts: str
    connections: str
    info_channel: str
    cryptobot: str
    main_image: str
    drainer_instruction: str

@dataclass
class Settings:
    bot: BotConfig
    links: LinksConfig

def get_settings():
    return Settings(
        bot=BotConfig(
            token=config.TWORKER_BOT_TOKEN,
            channel_id=config.CHANNEL_ID,
            super_admin_id=config.SUPER_ADMIN_ID,
            bot_enabled=config.BOT_ENABLED,
            drainer_status=config.DRAINER_STATUS,
        ),
        links=LinksConfig(
            manuals=config.MANUALS_URL,
            chat=config.CHAT_URL,
            payouts=config.PAYOUTS_URL,
            connections=config.CONNECTIONS_URL,
            info_channel=config.INFO_CHANNEL_URL,
            cryptobot=config.CRYPTOBOT_URL,
            main_image=config.MAIN_IMAGE_URL,
            drainer_instruction=config.DRAINER_INSTRUCTION_URL,
        ),
    )

settings = get_settings()
