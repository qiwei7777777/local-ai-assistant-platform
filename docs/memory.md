# Explicit Memory

The memory system stores user-approved facts and preferences locally in SQLite. Memory is explicit by design: the user creates, views, deletes, and opts into using it during chat.

## Flow

1. Create memory through the UI or `POST /api/memories`.
2. Send a chat request with `use_memory=true`.
3. Backend searches relevant memories.
4. Matching memories are injected as system context.
5. Chat response includes `used_memory` and `memory_hits_count`.

## Why Explicit

- Easier to explain in a portfolio demo
- Avoids surprising automatic memory capture
- Keeps privacy and local-first behavior clear
- Gives a clean future path for automatic memory suggestions

## Future Upgrade

- Add memory categories
- Add confidence scores
- Add review-before-save memory suggestions
- Add import/export for user profile portability
