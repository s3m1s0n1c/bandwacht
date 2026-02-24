"""Application configuration via environment variables."""

from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./bandwacht_web.db"
    recordings_dir: str = "./recordings"
    bandwacht_module_path: str = "../.."
    cors_origins: str = "http://localhost:5173,http://localhost:3416"
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # Notification backends (configured via env vars, not UI)
    notify_gotify_url: str = ""
    notify_gotify_token: str = ""
    notify_telegram_bot_token: str = ""
    notify_telegram_chat_id: str = ""
    notify_ntfy_topic: str = ""
    notify_ntfy_server: str = "https://ntfy.sh"
    notify_webhook_url: str = ""

    # Authentication
    auth_username: str = "oe8yml"
    auth_password_hash: str = "$2b$12$hD9Bu1eFl84XDR/IIofkT.o4YPwo11leMHe3vamW7.nwZMGuR2f5G"
    auth_jwt_secret: str = "ffb6fd1d4976c9354a93ca92124b144cf217a54821b69dbf206040ba65f59a2a"
    auth_jwt_expire_hours: int = 24

    model_config = {"env_prefix": "BANDWACHT_"}

    @property
    def recordings_path(self) -> Path:
        p = Path(self.recordings_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    def configured_notifications(self) -> list[dict]:
        """Return list of notification backends configured via env vars."""
        result = [{"backend": "console", "enabled": True, "configured": True}]
        if self.notify_gotify_url and self.notify_gotify_token:
            result.append({"backend": "gotify", "enabled": True, "configured": True})
        if self.notify_telegram_bot_token and self.notify_telegram_chat_id:
            result.append({"backend": "telegram", "enabled": True, "configured": True})
        if self.notify_ntfy_topic:
            result.append({"backend": "ntfy", "enabled": True, "configured": True})
        if self.notify_webhook_url:
            result.append({"backend": "webhook", "enabled": True, "configured": True})
        return result


settings = Settings()
