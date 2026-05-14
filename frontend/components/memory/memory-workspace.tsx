"use client";

import { useEffect, useState } from "react";
import { Brain, LoaderCircle, RefreshCw, Trash2 } from "lucide-react";

import { EmptyState, ErrorState, LoadingState } from "@/components/state-panels";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { apiClient } from "@/lib/api-client";
import type { Memory } from "@/types/api";

function formatTime(value: string) {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

export function MemoryWorkspace() {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [content, setContent] = useState("");
  const [source, setSource] = useState("manual");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void loadMemories();
  }, []);

  async function loadMemories() {
    setLoading(true);
    setError(null);
    try {
      const result = await apiClient.listMemories();
      setMemories(result.memories);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Failed to load memories.");
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateMemory() {
    if (!content.trim()) return;
    setSaving(true);
    setError(null);
    try {
      const memory = await apiClient.createMemory({
        content: content.trim(),
        source: source.trim() || "manual",
      });
      setMemories((current) => [memory, ...current]);
      setContent("");
      setSource("manual");
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Failed to create memory.");
    } finally {
      setSaving(false);
    }
  }

  async function handleDeleteMemory(memoryId: string) {
    setDeletingId(memoryId);
    setError(null);
    try {
      await apiClient.deleteMemory(memoryId);
      setMemories((current) => current.filter((item) => item.id !== memoryId));
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : "Failed to delete memory.");
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
      <Card>
        <CardHeader>
          <CardTitle>Add Explicit Memory</CardTitle>
          <CardDescription>
            Store durable preferences, facts, or project context. Each memory stays visible,
            deletable, and opt-in for chat.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">Source</label>
            <Input value={source} onChange={(event) => setSource(event.target.value)} />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">Memory content</label>
            <Textarea
              className="min-h-[180px]"
              placeholder="Example: The user prefers concise answers and likes the sign-off word starlight."
              value={content}
              onChange={(event) => setContent(event.target.value)}
            />
          </div>
          <Button onClick={() => void handleCreateMemory()} disabled={saving || !content.trim()}>
            {saving ? <LoaderCircle className="mr-2 h-4 w-4 animate-spin" /> : null}
            Save memory
          </Button>
          {error ? (
            <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
              {error}
            </div>
          ) : null}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex-row items-start justify-between gap-4">
          <div>
            <CardTitle>Memory List</CardTitle>
            <CardDescription>
              When chat memory is enabled, the backend matches relevant records and injects
              them as local context.
            </CardDescription>
          </div>
          <Button variant="ghost" className="gap-2" onClick={() => void loadMemories()}>
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
        </CardHeader>
        <CardContent>
          {loading ? (
            <LoadingState label="Loading memories..." />
          ) : error && memories.length === 0 ? (
            <ErrorState title="Memories unavailable" description={error} onRetry={() => void loadMemories()} />
          ) : memories.length === 0 ? (
            <EmptyState title="No memories yet" description="Add an explicit memory, then enable memory from the chat workspace." />
          ) : (
            <div className="space-y-3">
              {memories.map((memory) => (
                <div key={memory.id} className="rounded-3xl border border-border bg-slate-50/80 p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <Brain className="h-4 w-4 text-primary" />
                        <p className="text-sm font-semibold text-slate-900">{memory.source}</p>
                        <Badge tone="neutral">{formatTime(memory.created_at)}</Badge>
                      </div>
                      <p className="mt-3 whitespace-pre-wrap text-sm leading-7 text-slate-600">
                        {memory.content}
                      </p>
                    </div>
                    <Button
                      variant="ghost"
                      className="px-2 py-2"
                      disabled={deletingId === memory.id}
                      onClick={() => void handleDeleteMemory(memory.id)}
                    >
                      {deletingId === memory.id ? (
                        <LoaderCircle className="h-4 w-4 animate-spin" />
                      ) : (
                        <Trash2 className="h-4 w-4" />
                      )}
                    </Button>
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
