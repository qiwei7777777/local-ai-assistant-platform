# Retrieval and Knowledge Bases

The current RAG layer is intentionally lightweight so the project stays easy to run on a laptop.

## Flow

1. Upload a supported text-bearing file through `POST /api/files/upload`.
2. The backend extracts text and stores file metadata.
3. Create a knowledge base through `POST /api/knowledge-bases`.
4. Attach a file to the knowledge base.
5. The backend chunks extracted text and stores chunks in SQLite.
6. Query chunks through `POST /api/retrieval/search`.
7. Chat can inject top matching chunks when `knowledge_base_id` is provided.

## Supported Files

- Plain text
- Markdown
- PDF
- Word documents

## Current Boundary

Retrieval uses local chunk scoring rather than embeddings. This makes the demo self-contained and keeps the future vector-store upgrade obvious.

## Future Upgrade

- Add embedding generation
- Add a vector store adapter
- Store source page/section metadata
- Add structured citations in assistant responses
