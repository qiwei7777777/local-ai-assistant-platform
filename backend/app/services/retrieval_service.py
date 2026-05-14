import re

from app.core.config import Settings
from app.schemas.retrieval import RetrievalHitData, RetrievalSearchData


class RetrievalService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def split_text(self, text: str) -> list[str]:
        chunk_size = self.settings.rag_chunk_size
        overlap = min(self.settings.rag_chunk_overlap, chunk_size // 2)
        normalized = re.sub(r"\n{3,}", "\n\n", text).strip()
        if not normalized:
            return []

        chunks: list[str] = []
        start = 0
        while start < len(normalized):
            end = min(len(normalized), start + chunk_size)
            chunk = normalized[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end >= len(normalized):
                break
            start = max(end - overlap, start + 1)
        return chunks

    def search(self, *, knowledge_base_id: str, query: str, chunks: list, top_k: int | None = None) -> RetrievalSearchData:
        keywords = self._tokenize_query(query)
        scored_hits: list[RetrievalHitData] = []

        for chunk in chunks:
            haystack = chunk.content.lower()
            score = sum(haystack.count(keyword) for keyword in keywords)
            if score <= 0 and keywords:
                continue
            scored_hits.append(
                RetrievalHitData(
                    chunk_id=chunk.id,
                    file_id=chunk.file_id,
                    file_name=chunk.file.original_name if chunk.file else "unknown",
                    chunk_index=chunk.chunk_index,
                    score=score,
                    content=chunk.content,
                )
            )

        scored_hits.sort(key=lambda item: (-item.score, item.file_name, item.chunk_index))
        limit = top_k or self.settings.rag_top_k
        return RetrievalSearchData(
            knowledge_base_id=knowledge_base_id,
            query=query,
            hits=scored_hits[:limit],
        )

    @staticmethod
    def _tokenize_query(query: str) -> list[str]:
        base_tokens = [token for token in re.findall(r"[\w\u4e00-\u9fff]+", query.lower()) if token]
        expanded: list[str] = []
        for token in base_tokens:
            expanded.append(token)
            if re.fullmatch(r"[\u4e00-\u9fff]+", token) and len(token) > 2:
                expanded.extend(token[index : index + 2] for index in range(len(token) - 1))
        return list(dict.fromkeys(expanded))
