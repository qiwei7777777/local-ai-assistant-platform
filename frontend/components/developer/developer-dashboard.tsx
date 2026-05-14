"use client";

import { Activity, Database, RefreshCw, Server } from "lucide-react";

import { EmptyState, ErrorState, LoadingState } from "@/components/state-panels";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { apiClient } from "@/lib/api-client";
import { appConfig } from "@/lib/config";
import type { HealthData, ModelsData } from "@/types/api";

export type DeveloperDiagnosticsState = {
  health: HealthData | null;
  models: ModelsData | null;
  healthError: string | null;
  modelsError: string | null;
  isLoading: boolean;
};

type DeveloperDashboardProps = DeveloperDiagnosticsState & {
  onReload: () => void;
};

function formatModelSize(size: number | null) {
  if (!size) return "Unknown size";
  return `${(size / 1024 / 1024 / 1024).toFixed(1)} GB`;
}

function statusTone(status: string) {
  return status === "ok" ? "success" : "danger";
}

export async function loadDeveloperDiagnostics() {
  const [healthResult, modelsResult] = await Promise.allSettled([
    apiClient.getHealth(),
    apiClient.getModels(),
  ]);

  return {
    health: healthResult.status === "fulfilled" ? healthResult.value : null,
    models: modelsResult.status === "fulfilled" ? modelsResult.value : null,
    healthError:
      healthResult.status === "rejected"
        ? healthResult.reason instanceof Error
          ? healthResult.reason.message
          : "Failed to load /api/health."
        : null,
    modelsError:
      modelsResult.status === "rejected"
        ? modelsResult.reason instanceof Error
          ? modelsResult.reason.message
          : "Failed to load /api/models."
        : null,
  };
}

export function getDeveloperStatus(state: DeveloperDiagnosticsState) {
  if (state.isLoading) {
    return "Checking /api/health and /api/models";
  }

  if (state.health && state.models) {
    return "Connected: /api/health and /api/models";
  }

  if (state.health || state.models) {
    return "Partial connectivity";
  }

  return "Backend unavailable";
}

export function DeveloperDashboard({
  health,
  models,
  healthError,
  modelsError,
  isLoading,
  onReload,
}: DeveloperDashboardProps) {
  if (isLoading) {
    return <LoadingState label="Checking backend connectivity and model availability..." />;
  }

  if (healthError && modelsError) {
    return (
      <ErrorState
        title="Backend diagnostics are unavailable"
        description={`${healthError} ${modelsError} Base URL: ${appConfig.apiBaseUrl}`}
        onRetry={onReload}
      />
    );
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
      <div className="space-y-6">
        <Card>
          <CardHeader className="flex-row items-start justify-between gap-4">
            <div>
              <CardTitle>Backend Health</CardTitle>
              <CardDescription>
                Live request to `/api/health` for backend, database, and Ollama status.
              </CardDescription>
            </div>
            <Button variant="ghost" onClick={onReload} className="gap-2">
              <RefreshCw className="h-4 w-4" />
              Refresh
            </Button>
          </CardHeader>
          <CardContent>
            {healthError || !health ? (
              <ErrorState
                title="Health check failed"
                description={healthError ?? "No health data returned."}
                onRetry={onReload}
              />
            ) : (
              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                {[
                  { label: "App", value: health.app, icon: Activity },
                  { label: "Version", value: health.version, icon: Activity },
                  { label: "Environment", value: health.environment, icon: Server },
                  { label: "Database", value: health.database, icon: Database },
                  { label: "Ollama", value: health.ollama, icon: Server },
                  { label: "Default model", value: health.default_model, icon: Activity },
                ].map((item) => {
                  const Icon = item.icon;
                  return (
                    <div
                      key={item.label}
                      className="rounded-3xl border border-border bg-slate-50/80 p-4"
                    >
                      <div className="flex items-center gap-2 text-sm font-medium text-slate-800">
                        <Icon className="h-4 w-4 text-primary" />
                        {item.label}
                      </div>
                      <div className="mt-3 flex items-center gap-2">
                        <p className="text-lg font-semibold text-slate-950">{item.value}</p>
                        {["App", "Database", "Ollama"].includes(item.label) ? (
                          <Badge tone={statusTone(item.value) as "success" | "danger"}>
                            {item.value}
                          </Badge>
                        ) : null}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>API Connectivity</CardTitle>
            <CardDescription>
              Frontend API base URL and current endpoint reachability.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-slate-600">
            <div className="rounded-2xl border border-border bg-slate-50/80 px-4 py-3">
              Base URL: <span className="font-medium text-slate-900">{appConfig.apiBaseUrl}</span>
            </div>
            <div className="rounded-2xl border border-border bg-white px-4 py-3">
              Source:{" "}
              <span className="font-medium text-slate-900">
                {appConfig.apiBaseUrlSource === "env"
                  ? "NEXT_PUBLIC_API_BASE_URL"
                  : appConfig.apiBaseUrlSource === "window"
                    ? "inferred from current browser host"
                    : "localhost fallback"}
              </span>
            </div>
            <div className="rounded-2xl border border-border bg-white px-4 py-3">
              Mode:{" "}
              <span className="font-medium text-slate-900">
                {appConfig.apiMode === "same-origin"
                  ? "same-origin /api via Next.js rewrite"
                  : "direct backend address"}
              </span>
            </div>
            <div className="rounded-2xl border border-border bg-white px-4 py-3">
              Chat mode:{" "}
              <span className="font-medium text-slate-900">
                {appConfig.chatMode === "non_streaming"
                  ? "non-streaming /api/chat"
                  : "streaming /api/chat/stream"}
              </span>
            </div>
            {appConfig.apiBaseUrlWarning ? (
              <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-amber-900">
                {appConfig.apiBaseUrlWarning}
              </div>
            ) : null}
            <div className="rounded-2xl border border-border bg-white px-4 py-3">
              <div>`/api/health`: {health ? "connected" : healthError ?? "unavailable"}</div>
              <div className="mt-1">`/api/models`: {models ? "connected" : modelsError ?? "unavailable"}</div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="flex-row items-start justify-between gap-4">
          <div>
            <CardTitle>Local Models</CardTitle>
            <CardDescription>
              Live request to `/api/models` to inspect the actual Ollama model list.
            </CardDescription>
          </div>
          <Button variant="ghost" onClick={onReload} className="gap-2">
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
        </CardHeader>
        <CardContent>
          {modelsError ? (
            <ErrorState
              title="Unable to load model list"
              description={modelsError}
              onRetry={onReload}
            />
          ) : !models || models.models.length === 0 ? (
            <EmptyState
              title="No local models found"
              description="If Ollama is running but the list is empty, pull a local model such as `gemma4:e4b` first."
            />
          ) : (
            <div className="space-y-3">
              {models.models.map((model) => (
                <div
                  key={model.name}
                  className="rounded-3xl border border-border bg-slate-50/80 p-4"
                >
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="text-base font-semibold text-slate-950">{model.name}</p>
                      <p className="mt-1 text-sm text-slate-500">{formatModelSize(model.size)}</p>
                    </div>
                    <Badge tone={model.name === models.default_model ? "success" : "neutral"}>
                      {model.name === models.default_model ? "Default" : "Local"}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
