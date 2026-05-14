from app.core.config import Settings
from app.integrations.ollama import OllamaClient
from app.schemas.model import ModelInfo, ModelListData


class ModelService:
    def __init__(self, settings: Settings, ollama_client: OllamaClient) -> None:
        self.settings = settings
        self.ollama_client = ollama_client

    def list_models(self) -> ModelListData:
        models = [
            ModelInfo(
                name=item.get("name", ""),
                size=item.get("size"),
                modified_at=item.get("modified_at"),
                digest=item.get("digest"),
            )
            for item in self.ollama_client.list_models()
        ]
        return ModelListData(default_model=self.settings.ollama_default_model, models=models)
