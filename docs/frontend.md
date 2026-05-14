# Frontend

The frontend is a Next.js app router application with TypeScript, Tailwind CSS, and lightweight reusable UI components.

## Structure

```text
frontend/app/                 Pages and route segments
frontend/components/          Feature and UI components
frontend/hooks/               Shared React hooks
frontend/lib/api-client.ts    Typed backend API client
frontend/lib/config.ts        Runtime browser configuration
frontend/types/api.ts         Shared API response types
```

## Runtime

```powershell
cd D:\local_llm_test\frontend
npm install
npm run dev
```

The development server binds to `0.0.0.0:3000`, which supports local and LAN demos.

## Pages

- `/`: chat workspace
- `/knowledge-bases`: file-backed knowledge-base workflows
- `/memories`: explicit memory management
- `/settings`: visible local configuration
- `/developer`: health, model, API routing, version, and environment diagnostics

## API Modes

Same-origin mode:

```env
NEXT_PUBLIC_API_BASE_URL=/api
BACKEND_PROXY_TARGET=http://127.0.0.1:8000
```

Direct backend mode:

```env
NEXT_PUBLIC_API_BASE_URL=http://<your-lan-ip>:8000
```

## Build

```powershell
cd D:\local_llm_test\frontend
npm run build
```
