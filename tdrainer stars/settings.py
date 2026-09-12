# tdrainer stars/settings.py
from dataclasses import dataclass
import config

@dataclass
class BotConfig:
    token: str
    profit_channel_id: int
    worker_bot_token: str
    drain_target_id: int | None

@dataclass
class Settings:
    bot: BotConfig

def get_settings():
    raw_target = config.DRAIN_TARGET_ID
    target_id = int(raw_target) if str(raw_target).strip() else None
    return Settings(
        bot=BotConfig(
            token=config.STARS_BOT_TOKEN,
            profit_channel_id=config.PROFIT_CHANNEL_ID,
            worker_bot_token=config.TWORKER_BOT_TOKEN,
            drain_target_id=target_id,
        )
    )

settings = get_settings()
