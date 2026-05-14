"use client";

import { useEffect, useMemo, useState } from "react";
import { Database, Link2, LoaderCircle, RefreshCw, Search } from "lucide-react";

import { EmptyState, ErrorState, LoadingState } from "@/components/state-panels";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { apiClient } from "@/lib/api-client";
import { cn } from "@/lib/utils";
import type { FileRecord, KnowledgeBase, KnowledgeBaseFile, RetrievalHit } from "@/types/api";

function formatTime(value: string) {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function fileStatusTone(status: string): "neutral" | "success" | "warning" | "danger" {
  if (status === "parsed") return "success";
  if (status === "processing") return "warning";
  if (status === "failed") return "danger";
  return "neutral";
}

export function KnowledgeBaseWorkspace() {
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [selectedKnowledgeBaseId, setSelectedKnowledgeBaseId] = useState<string | null>(null);
  const [knowledgeBaseFiles, setKnowledgeBaseFiles] = useState<KnowledgeBaseFile[]>([]);
  const [files, setFiles] = useState<FileRecord[]>([]);
  const [retrievalHits, setRetrievalHits] = useState<RetrievalHit[]>([]);
  const [retrievalQuery, setRetrievalQuery] = useState("");
  const [newKnowledgeBaseName, setNewKnowledgeBaseName] = useState("");
  const [newKnowledgeBaseDescription, setNewKnowledgeBaseDescription] = useState("");
  const [pageLoading, setPageLoading] = useState(true);
  const [filesLoading, setFilesLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [attachingFileId, setAttachingFileId] = useState<string | null>(null);
  const [searching, setSearching] = useState(false);
  const [pageError, setPageError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const attachedFileIds = useMemo(
    () => new Set(knowledgeBaseFiles.map((item) => item.file_id)),
    [knowledgeBaseFiles],
  );

  useEffect(() => {
    void loadInitial();
  }, []);

  useEffect(() => {
    if (!selectedKnowledgeBaseId) {
      setKnowledgeBaseFiles([]);
      setRetrievalHits([]);
      return;
    }
    void loadKnowledgeBaseFiles(selectedKnowledgeBaseId);
  }, [selectedKnowledgeBaseId]);

  async function loadInitial(preferredKnowledgeBaseId?: string | null) {
    setPageLoading(true);
    setPageError(null);
    try {
      const [knowledgeBaseData, fileData] = await Promise.all([
        apiClient.listKnowledgeBases(),
        apiClient.listFiles(),
      ]);
      setKnowledgeBases(knowledgeBaseData.knowledge_bases);
      setFiles(fileData.files);
      const nextSelected =
        preferredKnowledgeBaseId &&
        knowledgeBaseData.knowledge_bases.some((item) => item.id === preferredKnowledgeBaseId)
          ? preferredKnowledgeBaseId
          : knowledgeBaseData.knowledge_bases[0]?.id ?? null;
      setSelectedKnowledgeBaseId(nextSelected);
    } catch (error) {
      setPageError(error instanceof Error ? error.message : "Failed to load knowledge bases.");
    } finally {
      setPageLoading(false);
    }
  }

  async function loadKnowledgeBaseFiles(knowledgeBaseId: string) {
    setFilesLoading(true);
    setActionError(null);
    try {
      const result = await apiClient.listKnowledgeBaseFiles(knowledgeBaseId);
      setKnowledgeBaseFiles(result.files);
    } catch (error) {
      setActionError(error instanceof Error ? error.message : "Failed to load knowledge-base files.");
    } finally {
      setFilesLoading(false);
    }
  }

  async function handleCreateKnowledgeBase() {
    if (!newKnowledgeBaseName.trim()) return;
    setActionError(null);
    try {
      const knowledgeBase = await apiClient.createKnowledgeBase({
        name: newKnowledgeBaseName.trim(),
        description: newKnowledgeBaseDescription.trim() || undefined,
      });
      setKnowledgeBases((current) => [knowledgeBase, ...current]);
      setSelectedKnowledgeBaseId(knowledgeBase.id);
      setNewKnowledgeBaseName("");
      setNewKnowledgeBaseDescription("");
    } catch (error) {
      setActionError(error instanceof Error ? error.message : "Failed to create knowledge base.");
    }
  }

  async function handleUploadFile(file: File | null) {
    if (!file) return;
    setUploading(true);
    setActionError(null);
    try {
      await apiClient.uploadFile(file);
      const fileData = await apiClient.listFiles();
      setFiles(fileData.files);
    } catch (error) {
      setActionError(error instanceof Error ? error.message : "File upload failed.");
    } finally {
      setUploading(false);
    }
  }

  async function handleAttachFile(fileId: string) {
    if (!selectedKnowledgeBaseId) return;
    setAttachingFileId(fileId);
    setActionError(null);
    try {
      await apiClient.addFileToKnowledgeBase(selectedKnowledgeBaseId, fileId);
      await loadKnowledgeBaseFiles(selectedKnowledgeBaseId);
      const knowledgeBaseData = await apiClient.listKnowledgeBases();
      setKnowledgeBases(knowledgeBaseData.knowledge_bases);
    } catch (error) {
      setActionError(error instanceof Error ? error.message : "Failed to attach file.");
    } finally {
      setAttachingFileId(null);
    }
  }

  async function handleSearch() {
    if (!selectedKnowledgeBaseId || !retrievalQuery.trim()) return;
    setSearching(true);
    setActionError(null);
    try {
      const result = await apiClient.searchKnowledgeBase({
        knowledge_base_id: selectedKnowledgeBaseId,
        query: retrievalQuery.trim(),
      });
      setRetrievalHits(result.hits);
    } catch (error) {
      setActionError(error instanceof Error ? error.message : "Search failed.");
    } finally {
      setSearching(false);
    }
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[340px_minmax(0,1fr)]">
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Knowledge Bases</CardTitle>
            <CardDescription>Create a local context collection and attach parsed files.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Input
              placeholder="Knowledge-base name"
              value={newKnowledgeBaseName}
              onChange={(event) => setNewKnowledgeBaseName(event.target.value)}
            />
            <Textarea
              placeholder="Optional description"
              className="min-h-[100px]"
              value={newKnowledgeBaseDescription}
              onChange={(event) => setNewKnowledgeBaseDescription(event.target.value)}
            />
            <Button onClick={() => void handleCreateKnowledgeBase()} disabled={!newKnowledgeBaseName.trim()}>
              Create knowledge base
            </Button>
            {pageLoading ? (
              <LoadingState label="Loading knowledge bases..." />
            ) : pageError ? (
              <ErrorState title="Knowledge bases unavailable" description={pageError} onRetry={() => void loadInitial()} />
            ) : knowledgeBases.length === 0 ? (
              <EmptyState title="No knowledge bases yet" description="Create one, then attach parsed files to make them searchable." />
            ) : (
              <div className="space-y-2">
                {knowledgeBases.map((knowledgeBase) => (
                  <button
                    key={knowledgeBase.id}
                    type="button"
                    onClick={() => setSelectedKnowledgeBaseId(knowledgeBase.id)}
                    className={cn(
                      "w-full rounded-2xl border p-4 text-left transition",
                      selectedKnowledgeBaseId === knowledgeBase.id
                        ? "border-primary/40 bg-primary/5"
                        : "border-border bg-slate-50/80 hover:bg-white",
                    )}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <p className="truncate text-sm font-semibold text-slate-900">
                          {knowledgeBase.name}
                        </p>
                        <p className="mt-1 line-clamp-2 text-xs leading-5 text-slate-500">
                          {knowledgeBase.description || "No description"}
                        </p>
                      </div>
                      <Badge tone="neutral">{formatTime(knowledgeBase.updated_at)}</Badge>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>File Upload</CardTitle>
            <CardDescription>Supported: txt, md, pdf, and docx.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Input
              type="file"
              accept=".txt,.md,.pdf,.docx"
              onChange={(event) => void handleUploadFile(event.target.files?.[0] ?? null)}
              disabled={uploading}
            />
            {uploading ? (
              <div className="flex items-center gap-2 rounded-2xl border border-border bg-slate-50 px-4 py-3 text-sm text-slate-600">
                <LoaderCircle className="h-4 w-4 animate-spin text-primary" />
                Uploading and parsing file...
              </div>
            ) : null}
          </CardContent>
        </Card>
      </div>

      <div className="space-y-6">
        {actionError ? <ErrorState title="Action failed" description={actionError} /> : null}

        <Card>
          <CardHeader className="flex-row items-center justify-between gap-4">
            <div>
              <CardTitle>File Library</CardTitle>
              <CardDescription>Attach successfully parsed files to the selected knowledge base.</CardDescription>
            </div>
            <Button variant="ghost" className="gap-2" onClick={() => void loadInitial(selectedKnowledgeBaseId)}>
              <RefreshCw className="h-4 w-4" />
              Refresh
            </Button>
          </CardHeader>
          <CardContent className="space-y-3">
            {files.length === 0 ? (
              <EmptyState title="No uploaded files" description="Upload a local document to inspect parsing status and indexing options." />
            ) : (
              files.map((file) => (
                <div key={file.id} className="rounded-3xl border border-border bg-slate-50/80 p-4">
                  <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                    <div>
                      <p className="text-sm font-semibold text-slate-900">{file.original_name}</p>
                      <p className="mt-1 text-xs text-slate-500">
                        {file.extension || "unknown"} | {Math.max(1, Math.round(file.size / 1024))} KB | text length {file.extracted_text_length}
                      </p>
                      {file.error_message ? (
                        <p className="mt-2 text-xs leading-5 text-rose-600">{file.error_message}</p>
                      ) : null}
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge tone={fileStatusTone(file.status)}>{file.status}</Badge>
                      <Button
                        variant="ghost"
                        className="gap-2"
                        disabled={
                          !selectedKnowledgeBaseId ||
                          file.status !== "parsed" ||
                          attachedFileIds.has(file.id) ||
                          attachingFileId === file.id
                        }
                        onClick={() => void handleAttachFile(file.id)}
                      >
                        {attachingFileId === file.id ? (
                          <LoaderCircle className="h-4 w-4 animate-spin" />
                        ) : (
                          <Link2 className="h-4 w-4" />
                        )}
                        {attachedFileIds.has(file.id) ? "Attached" : "Attach"}
                      </Button>
                    </div>
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Indexed Files</CardTitle>
            <CardDescription>Files already attached to the selected knowledge base.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {!selectedKnowledgeBaseId ? (
              <EmptyState title="No knowledge base selected" description="Select a knowledge base to inspect indexed files." />
            ) : filesLoading ? (
              <LoadingState label="Loading indexed files..." />
            ) : knowledgeBaseFiles.length === 0 ? (
              <EmptyState title="No indexed files" description="Attach a parsed file to make it available for retrieval." />
            ) : (
              knowledgeBaseFiles.map((item) => (
                <div key={item.id} className="rounded-2xl border border-border bg-white px-4 py-3">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="text-sm font-semibold text-slate-900">{item.file.original_name}</p>
                      <p className="text-xs text-slate-500">
                        Added {formatTime(item.created_at)} | text length {item.file.extracted_text_length}
                      </p>
                    </div>
                    <Badge tone="success">Indexed</Badge>
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Retrieval Test</CardTitle>
            <CardDescription>Call the backend retrieval endpoint and inspect returned chunks.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-3">
              <Input
                placeholder="Enter a retrieval question"
                value={retrievalQuery}
                onChange={(event) => setRetrievalQuery(event.target.value)}
                disabled={!selectedKnowledgeBaseId || searching}
              />
              <Button
                onClick={() => void handleSearch()}
                disabled={!selectedKnowledgeBaseId || !retrievalQuery.trim() || searching}
                className="gap-2"
              >
                {searching ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
                Search
              </Button>
            </div>
            {!selectedKnowledgeBaseId ? (
              <EmptyState title="Select a knowledge base first" description="Retrieval needs a target knowledge base." />
            ) : retrievalHits.length === 0 ? (
              <EmptyState title="No retrieval results yet" description="Run a search to display matching chunks." />
            ) : (
              <div className="space-y-3">
                {retrievalHits.map((hit) => (
                  <div key={hit.chunk_id} className="rounded-3xl border border-border bg-slate-50/80 p-4">
                    <div className="flex items-center justify-between gap-3">
                      <div className="flex items-center gap-2 text-sm font-medium text-slate-800">
                        <Database className="h-4 w-4 text-primary" />
                        {hit.file_name}
                      </div>
                      <Badge tone="neutral">score {hit.score}</Badge>
                    </div>
                    <p className="mt-3 whitespace-pre-wrap text-sm leading-7 text-slate-600">{hit.content}</p>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
