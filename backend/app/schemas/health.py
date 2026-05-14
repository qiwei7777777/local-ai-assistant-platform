from pydantic import BaseModel


class HealthStatus(BaseModel):
    app: str
    version: str
    environment: str
    database: str
    ollama: str
    default_model: str
