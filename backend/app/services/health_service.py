from app.core.config import Settings
from app.db.init_db import check_database
from app.integrations.ollama import OllamaClient
from app.schemas.health import HealthStatus


class HealthService:
    def __init__(self, settings: Settings, ollama_client: OllamaClient) -> None:
        self.settings = settings
        self.ollama_client = ollama_client

    def get_status(self) -> HealthStatus:
        database_status = "ok" if check_database() else "error"
        ollama_status = "ok" if self.ollama_client.healthcheck() else "error"
        return HealthStatus(
            app="ok",
            version=self.settings.app_version,
            environment=self.settings.app_env,
            database=database_status,
            ollama=ollama_status,
            default_model=self.settings.ollama_default_model,
        )
