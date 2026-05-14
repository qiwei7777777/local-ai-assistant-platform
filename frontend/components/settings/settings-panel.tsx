import { Globe, MessageSquareText, SlidersHorizontal } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { appConfig } from "@/lib/config";

export function SettingsPanel() {
  return (
    <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
      <Card>
        <CardHeader>
          <CardTitle>Runtime</CardTitle>
          <CardDescription>
            The settings page currently exposes the active local runtime values used by the app.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">
              Ollama base URL
            </label>
            <Input value="http://127.0.0.1:11434" readOnly />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">
              API base URL
            </label>
            <Input value={appConfig.apiBaseUrl} readOnly />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">
              API base URL source
            </label>
            <Input
              value={
                appConfig.apiBaseUrlSource === "env"
                  ? "NEXT_PUBLIC_API_BASE_URL"
                  : appConfig.apiBaseUrlSource === "window"
                    ? "Inferred from current browser host"
                    : "Localhost fallback"
              }
              readOnly
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">
              API mode
            </label>
            <Input
              value={
                appConfig.apiMode === "same-origin"
                  ? "Same-origin /api via Next.js rewrite"
                  : "Direct backend address"
              }
              readOnly
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">
              Chat mode
            </label>
            <Input
              value={
                appConfig.chatMode === "non_streaming"
                  ? "Non-streaming /api/chat"
                  : "Streaming /api/chat/stream"
              }
              readOnly
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">
              Default model
            </label>
            <Input value="gemma4:e4b" readOnly />
          </div>
          {appConfig.apiBaseUrlWarning ? (
            <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
              {appConfig.apiBaseUrlWarning}
            </div>
          ) : null}
          <Switch checked label="Streaming chat enabled" />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Notes</CardTitle>
          <CardDescription>
            These panels are display-oriented and help with local and LAN demos.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="rounded-3xl border border-border bg-slate-50/80 p-4">
            <div className="flex items-center gap-2 text-sm font-medium text-slate-800">
              <MessageSquareText className="h-4 w-4 text-primary" />
              Chat behavior
            </div>
            <p className="mt-2 text-sm leading-6 text-slate-500">
              The default web experience uses streaming chat. The Python SDK still uses the non-streaming endpoint.
            </p>
          </div>
          <div className="rounded-3xl border border-border bg-slate-50/80 p-4">
            <div className="flex items-center gap-2 text-sm font-medium text-slate-800">
              <SlidersHorizontal className="h-4 w-4 text-primary" />
              API routing
            </div>
            <p className="mt-2 text-sm leading-6 text-slate-500">
              All browser API calls resolve from one environment variable: `NEXT_PUBLIC_API_BASE_URL`.
            </p>
          </div>
          <div className="rounded-3xl border border-border bg-slate-950 p-4 text-slate-100">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-sm font-medium">
                <Globe className="h-4 w-4 text-blue-300" />
                LAN demo
              </div>
              <Badge tone="warning">Manual IP</Badge>
            </div>
            <p className="mt-3 text-sm leading-6 text-slate-300">
              For another device on the same network, open `http://&lt;your-lan-ip&gt;:3000` and point the API base URL at `http://&lt;your-lan-ip&gt;:8000`.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
