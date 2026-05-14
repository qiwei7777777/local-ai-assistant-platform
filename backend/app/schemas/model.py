from pydantic import BaseModel


class ModelInfo(BaseModel):
    name: str
    size: int | None = None
    modified_at: str | None = None
    digest: str | None = None


class ModelListData(BaseModel):
    default_model: str
    models: list[ModelInfo]
