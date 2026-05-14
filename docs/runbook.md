# Runbook

## Start Locally

1. Copy environment files:

```powershell
Copy-Item D:\local_llm_test\.env.example D:\local_llm_test\.env
Copy-Item D:\local_llm_test\frontend\.env.example D:\local_llm_test\frontend\.env.local
```

2. Start Ollama and pull the default model:

```powershell
ollama serve
ollama pull gemma4:e4b
```

3. Start the backend:

```powershell
powershell -ExecutionPolicy Bypass -File D:\local_llm_test\scripts\dev-backend.ps1
```

4. Start the frontend:

```powershell
powershell -ExecutionPolicy Bypass -File D:\local_llm_test\scripts\dev-frontend.ps1
```

5. Open:

```text
http://127.0.0.1:3000
http://127.0.0.1:8000/docs
```

## Verify

```powershell
cd D:\local_llm_test\backend
python -m pip install -e ".[dev]"

cd D:\local_llm_test
python -m unittest discover -s tests -p "test_*.py"

cd D:\local_llm_test\frontend
npm install
npm run build
```

Or run:

```powershell
powershell -ExecutionPolicy Bypass -File D:\local_llm_test\scripts\smoke-test.ps1
```

## LAN Demo

1. Find your LAN IP:

```powershell
ipconfig
```

2. Edit `frontend/.env.local`:

```env
NEXT_PUBLIC_API_BASE_URL=http://<your-lan-ip>:8000
```

3. Edit root `.env`:

```env
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://<your-lan-ip>:3000
```

4. Restart frontend and backend.
5. Open `http://<your-lan-ip>:3000` from another device on the same network.

## Single-URL External Demo

Use this when sharing with ngrok or a similar tunnel.

1. Keep `frontend/.env.local` as:

```env
NEXT_PUBLIC_API_BASE_URL=/api
BACKEND_PROXY_TARGET=http://127.0.0.1:8000
NEXT_PUBLIC_CHAT_MODE=non_streaming
```

2. Start backend and frontend.
3. Expose only the frontend:

```powershell
ngrok http 3000
```

4. Open the public URL and verify `/developer` reports same-origin `/api` mode.

## Regression Checklist

- `/developer` loads health and model diagnostics
- `/api/health` reports `app`, `version`, `environment`, `database`, `ollama`, and `default_model`
- Model dropdown loads actual Ollama models or shows a clear fallback
- New chat creates a session and persists messages
- Streaming mode emits visible chunks and finishes cleanly
- Stop generation returns the UI to idle and keeps partial content when available
- File upload parses supported text-bearing files
- Knowledge-base search returns at least one relevant hit for a seeded document
- Explicit memory can be created, used in chat, and deleted
- Code Agent can inspect the repository, read a selected file, generate a plan, and run `git status --short`
- SDK example can call `/api/chat`

## Troubleshooting

### Frontend loads but backend calls fail

- Check `frontend/.env.local`
- Check root `.env` CORS settings
- Open browser developer tools and inspect the actual request URL
- Open `http://127.0.0.1:8000/docs`

### Ollama is unavailable

- Run `ollama list`
- Run `ollama pull gemma4:e4b`
- Confirm `OLLAMA_BASE_URL=http://127.0.0.1:11434`
- Check `/developer` for the `/api/models` result

### LAN device cannot open the app

- Confirm backend and frontend are bound to `0.0.0.0`
- Confirm both devices are on the same network
- Check Windows Firewall prompts for Python and Node
- Try direct backend health from the second device: `http://<your-lan-ip>:8000/api/health`

### Streaming appears stuck

- Switch `NEXT_PUBLIC_CHAT_MODE=non_streaming` for public demos
- Use `/developer` to verify model availability
- Increase `OLLAMA_REQUEST_TIMEOUT` for slower models
- Check backend logs for `OLLAMA_STREAM_FAILED` or timeout messages
