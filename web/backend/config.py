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

    model_config = {"env_prefix": "BANDWACHT_"}

    @property
    def recordings_path(self) -> Path:
        p = Path(self.recordings_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
