from pydantic import BaseModel, Field


class RetrievalSearchRequest(BaseModel):
    knowledge_base_id: str
    query: str = Field(min_length=1)
    top_k: int | None = Field(default=None, gt=0, le=20)


class RetrievalHitData(BaseModel):
    chunk_id: str
    file_id: str
    file_name: str
    chunk_index: int
    score: int
    content: str


class RetrievalSearchData(BaseModel):
    knowledge_base_id: str
    query: str
    hits: list[RetrievalHitData]
