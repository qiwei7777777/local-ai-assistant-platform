"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  Clock3,
  Database,
  LoaderCircle,
  MessageSquarePlus,
  RefreshCw,
  Search,
  SendHorizonal,
  Square,
  Trash2,
} from "lucide-react";

import { ErrorState, LoadingState } from "@/components/state-panels";
import { MessageContent } from "@/components/chat/message-content";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import { ApiClientError, apiClient } from "@/lib/api-client";
import { appConfig } from "@/lib/config";
import { cn } from "@/lib/utils";
import type { KnowledgeBase, Message, ModelInfo, SessionSummary } from "@/types/api";

type ChatMessageView = Message & {
  status?: "waiting" | "streaming" | "stopped" | "error";
  note?: string;
};

type StreamLifecycle = {
  isRequestInFlight: boolean;
  hasReceivedFirstToken: boolean;
  isWaitingForFirstToken: boolean;
  isStreaming: boolean;
  streamFinished: boolean;
  streamAbortedByUser: boolean;
  streamError: string | null;
};

const MODEL_STORAGE_KEY = "local-ai-assistant:selected-model";

function createIdleStreamLifecycle(): StreamLifecycle {
  return {
    isRequestInFlight: false,
    hasReceivedFirstToken: false,
    isWaitingForFirstToken: false,
    isStreaming: false,
    streamFinished: false,
    streamAbortedByUser: false,
    streamError: null,
  };
}

function sortModels(models: ModelInfo[]) {
  return [...models].sort((left, right) => {
    const leftGemma = left.name.startsWith("gemma4:");
    const rightGemma = right.name.startsWith("gemma4:");
    if (leftGemma !== rightGemma) {
      return leftGemma ? -1 : 1;
    }
    if (left.name === "gemma4:e4b") return -1;
    if (right.name === "gemma4:e4b") return 1;
    if (left.name === "gemma4:26b") return -1;
    if (right.name === "gemma4:26b") return 1;
    return left.name.localeCompare(right.name);
  });
}

function formatTime(value: string) {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function getStreamErrorMessage(error: unknown, hasReceivedFirstToken: boolean) {
  if (!(error instanceof ApiClientError)) {
    return hasReceivedFirstToken
      ? "Generation was interrupted during streaming."
      : "The model could not start responding.";
  }

  switch (error.code) {
    case "REQUEST_ABORTED":
      return "Generation stopped.";
    case "FIRST_TOKEN_TIMEOUT":
      return "Model took too long to start responding.";
    case "STREAM_IDLE_TIMEOUT":
      return "Generation was interrupted during streaming.";
    case "EMPTY_MODEL_RESPONSE":
      return "The model finished without producing any text.";
    case "STREAM_INTERRUPTED":
      return hasReceivedFirstToken
        ? "Generation was interrupted during streaming."
        : "The stream ended before the model started responding.";
    default:
      return error.message;
  }
}

function getRequestErrorMessage(error: unknown) {
  if (!(error instanceof ApiClientError)) {
    return "Message failed.";
  }

  switch (error.code) {
    case "REQUEST_TIMEOUT":
      return "Request timed out while waiting for the model.";
    case "EMPTY_MODEL_RESPONSE":
      return "The model did not return a response.";
    default:
      return error.message;
  }
}

export function ChatWorkspace() {
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessageView[]>([]);
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [selectedKnowledgeBaseId, setSelectedKnowledgeBaseId] = useState<string>("");
  const [input, setInput] = useState("");
  const [search, setSearch] = useState("");
  const [useMemory, setUseMemory] = useState(false);
  const [workspaceLoading, setWorkspaceLoading] = useState(true);
  const [messagesLoading, setMessagesLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [sidebarError, setSidebarError] = useState<string | null>(null);
  const [chatError, setChatError] = useState<string | null>(null);
  const [lastFailedMessage, setLastFailedMessage] = useState<string | null>(null);
  const [lastRetrievalHitsCount, setLastRetrievalHitsCount] = useState(0);
  const [lastMemoryHitsCount, setLastMemoryHitsCount] = useState(0);
  const [stopRequested, setStopRequested] = useState(false);
  const [availableModels, setAvailableModels] = useState<ModelInfo[]>([]);
  const [selectedModel, setSelectedModel] = useState(appConfig.defaultModel);
  const [modelsLoading, setModelsLoading] = useState(true);
  const [modelsError, setModelsError] = useState<string | null>(null);
  const [streamLifecycle, setStreamLifecycle] = useState<StreamLifecycle>(
    createIdleStreamLifecycle(),
  );
  const abortControllerRef = useRef<AbortController | null>(null);
  const streamStoppedByUserRef = useRef(false);
  const streamedAssistantContentRef = useRef("");
  const hasReceivedFirstTokenRef = useRef(false);
  const modelPreferenceReadyRef = useRef(false);

  const filteredSessions = useMemo(() => {
    const keyword = search.trim().toLowerCase();
    if (!keyword) return sessions;
    return sessions.filter((session) =>
      session.title.toLowerCase().includes(keyword),
    );
  }, [search, sessions]);

  useEffect(() => {
    void loadSessions();
    void loadKnowledgeBases();
    void loadModels();
  }, []);

  useEffect(() => {
    if (typeof window === "undefined" || !modelPreferenceReadyRef.current) return;
    window.localStorage.setItem(MODEL_STORAGE_KEY, selectedModel);
  }, [selectedModel]);

  useEffect(() => {
    if (!selectedSessionId) {
      setMessages([]);
      return;
    }

    void loadMessages(selectedSessionId);
  }, [selectedSessionId]);

  async function loadSessions(preferredSessionId?: string | null) {
    setWorkspaceLoading(true);
    setSidebarError(null);

    try {
      const data = await apiClient.listSessions();
      setSessions(data.sessions);
      const nextSelected =
        preferredSessionId && data.sessions.some((item) => item.id === preferredSessionId)
          ? preferredSessionId
          : data.sessions[0]?.id ?? null;
      setSelectedSessionId(nextSelected);
    } catch (error) {
      setSidebarError(error instanceof Error ? error.message : "Failed to load sessions.");
    } finally {
      setWorkspaceLoading(false);
    }
  }

  async function loadKnowledgeBases() {
    try {
      const result = await apiClient.listKnowledgeBases();
      setKnowledgeBases(result.knowledge_bases);
      setSelectedKnowledgeBaseId((current) => {
        if (!current) return result.knowledge_bases[0]?.id ?? "";
        return result.knowledge_bases.some((item) => item.id === current) ? current : "";
      });
    } catch {
      setKnowledgeBases([]);
    }
  }

  async function loadModels() {
    setModelsLoading(true);
    setModelsError(null);

    try {
      const result = await apiClient.getModels();
      const sortedModels = sortModels(result.models);
      const savedModel =
        typeof window !== "undefined"
          ? window.localStorage.getItem(MODEL_STORAGE_KEY)
          : null;

      setAvailableModels(sortedModels);
      setSelectedModel((current) => {
        const preferredModel =
          (current && current !== appConfig.defaultModel ? current : null) ||
          savedModel ||
          result.default_model ||
          appConfig.defaultModel;
        return sortedModels.some((model) => model.name === preferredModel)
          ? preferredModel
          : sortedModels[0]?.name ?? result.default_model ?? appConfig.defaultModel;
      });
    } catch (error) {
      setAvailableModels([]);
      setSelectedModel((current) => current || appConfig.defaultModel);
      setModelsError(error instanceof Error ? error.message : "Failed to load models.");
    } finally {
      modelPreferenceReadyRef.current = true;
      setModelsLoading(false);
    }
  }

  async function loadMessages(sessionId: string) {
    setMessagesLoading(true);
    setChatError(null);

    try {
      const data = await apiClient.getSessionMessages(sessionId);
      setMessages(data.messages);
    } catch (error) {
      setChatError(error instanceof Error ? error.message : "Failed to load messages.");
    } finally {
      setMessagesLoading(false);
    }
  }

  async function handleCreateSession() {
    setSidebarError(null);

    try {
      const session = await apiClient.createSession();
      setSessions((current) => [session, ...current]);
      setSelectedSessionId(session.id);
      setMessages([]);
      setChatError(null);
    } catch (error) {
      setSidebarError(error instanceof Error ? error.message : "Failed to create session.");
    }
  }

  async function handleDeleteSession(sessionId: string) {
    const nextSessions = sessions.filter((item) => item.id !== sessionId);

    try {
      await apiClient.deleteSession(sessionId);
      setSessions(nextSessions);

      if (selectedSessionId === sessionId) {
        const nextSelected = nextSessions[0]?.id ?? null;
        setSelectedSessionId(nextSelected);
        if (!nextSelected) {
          setMessages([]);
        }
      }
    } catch (error) {
      setSidebarError(error instanceof Error ? error.message : "Failed to delete session.");
    }
  }

  function beginStreamLifecycle() {
    hasReceivedFirstTokenRef.current = false;
    setStreamLifecycle({
      isRequestInFlight: true,
      hasReceivedFirstToken: false,
      isWaitingForFirstToken: true,
      isStreaming: false,
      streamFinished: false,
      streamAbortedByUser: false,
      streamError: null,
    });
  }

  function markFirstTokenReceived() {
    hasReceivedFirstTokenRef.current = true;
    setStreamLifecycle((current) => ({
      ...current,
      hasReceivedFirstToken: true,
      isWaitingForFirstToken: false,
      isStreaming: true,
    }));
  }

  function cleanupStreamingState(options?: {
    finished?: boolean;
    abortedByUser?: boolean;
    error?: string | null;
  }) {
    abortControllerRef.current = null;
    streamStoppedByUserRef.current = false;
    setStopRequested(false);
    setSending(false);
    setStreamLifecycle((current) => ({
      ...current,
      isRequestInFlight: false,
      isWaitingForFirstToken: false,
      isStreaming: false,
      streamFinished: options?.finished ?? false,
      streamAbortedByUser: options?.abortedByUser ?? false,
      streamError: options?.error ?? null,
      hasReceivedFirstToken: current.hasReceivedFirstToken,
    }));
  }

  function resetRequestState() {
    abortControllerRef.current = null;
    streamStoppedByUserRef.current = false;
    hasReceivedFirstTokenRef.current = false;
    streamedAssistantContentRef.current = "";
    setStopRequested(false);
    setSending(false);
    setStreamLifecycle(createIdleStreamLifecycle());
  }

  async function handleSendMessageNonStreaming(
    finalMessage: string,
    optimisticUserMessage: ChatMessageView,
  ) {
    setMessages((current) => [...current, optimisticUserMessage]);

    try {
      const result = await apiClient.chat({
        session_id: selectedSessionId ?? undefined,
        message: finalMessage,
        knowledge_base_id: selectedKnowledgeBaseId || undefined,
        use_memory: useMemory,
        model: selectedModel || undefined,
      });

      setLastFailedMessage(null);
      setLastRetrievalHitsCount(result.retrieval_hits_count);
      setLastMemoryHitsCount(result.memory_hits_count);
      setSelectedSessionId(result.session.id);
      setMessages((current) => {
        const withoutTemporary = current.filter(
          (message) => message.id !== optimisticUserMessage.id,
        );
        return [...withoutTemporary, result.user_message, result.assistant_message];
      });
      setSessions((current) => {
        const withoutCurrent = current.filter((item) => item.id !== result.session.id);
        return [result.session, ...withoutCurrent];
      });
      resetRequestState();
    } catch (error) {
      const errorMessage = getRequestErrorMessage(error);

      setInput(finalMessage);
      setChatError(errorMessage);
      setLastFailedMessage(finalMessage);
      setMessages((current) =>
        current.filter((message) => message.id !== optimisticUserMessage.id),
      );
      setStreamLifecycle((current) => ({
        ...current,
        streamError: errorMessage,
      }));
      resetRequestState();
    }
  }

  async function handleSendMessageStreaming(
    finalMessage: string,
    optimisticUserMessage: ChatMessageView,
    streamingAssistantMessage: ChatMessageView,
    abortController: AbortController,
  ) {
    streamStoppedByUserRef.current = false;
    streamedAssistantContentRef.current = "";
    abortControllerRef.current = abortController;
    beginStreamLifecycle();
    setMessages((current) => [...current, optimisticUserMessage, streamingAssistantMessage]);

    try {
      await apiClient.chatStream(
        {
          session_id: selectedSessionId ?? undefined,
          message: finalMessage,
          knowledge_base_id: selectedKnowledgeBaseId || undefined,
          use_memory: useMemory,
          model: selectedModel || undefined,
        },
        {
          onFirstToken() {
            markFirstTokenReceived();
            setMessages((current) =>
              current.map((message) =>
                message.id === streamingAssistantMessage.id
                  ? { ...message, status: "streaming" }
                  : message,
              ),
            );
          },
          onChunk(content) {
            streamedAssistantContentRef.current += content;
            setMessages((current) =>
              current.map((message) =>
                message.id === streamingAssistantMessage.id
                  ? {
                      ...message,
                      content: `${message.content}${content}`,
                      status:
                        content.length > 0 || message.content.length > 0
                          ? "streaming"
                          : message.status,
                    }
                  : message,
              ),
            );
          },
          onDone(result) {
            streamedAssistantContentRef.current = result.assistant_message.content;
            setLastFailedMessage(null);
            setLastRetrievalHitsCount(result.retrieval_hits_count);
            setLastMemoryHitsCount(result.memory_hits_count);
            setSelectedSessionId(result.session.id);
            setMessages((current) => {
              const withoutTemporary = current.filter(
                (message) =>
                  message.id !== streamingAssistantMessage.id &&
                  message.id !== optimisticUserMessage.id,
              );
              return [...withoutTemporary, result.user_message, result.assistant_message];
            });
            setSessions((current) => {
              const withoutCurrent = current.filter((item) => item.id !== result.session.id);
              return [result.session, ...withoutCurrent];
            });
            cleanupStreamingState({ finished: true });
          },
        },
        {
          signal: abortController.signal,
        },
      );
    } catch (error) {
      const hadVisibleContent = Boolean(streamedAssistantContentRef.current.trim());
      const hasReceivedFirstToken = hasReceivedFirstTokenRef.current || hadVisibleContent;
      const errorMessage = getStreamErrorMessage(error, hasReceivedFirstToken);

      if (error instanceof ApiClientError && error.code === "REQUEST_ABORTED") {
        setMessages((current) => {
          if (!hadVisibleContent) {
            return current.filter((message) => message.id !== streamingAssistantMessage.id);
          }

          return current.map((message) =>
            message.id === streamingAssistantMessage.id
              ? {
                  ...message,
                  status: "stopped",
                  note: "Generation stopped.",
                }
              : message,
          );
        });
        setLastFailedMessage(null);
        cleanupStreamingState({ abortedByUser: true });
        return;
      }

      setInput(finalMessage);
      setChatError(errorMessage);
      setLastFailedMessage(finalMessage);
      setMessages((current) =>
        current.map((message) =>
          message.id === streamingAssistantMessage.id
            ? {
                ...message,
                status: "error",
                content: message.content || errorMessage,
                note: errorMessage,
              }
            : message,
        ),
      );
      cleanupStreamingState({ error: errorMessage });
    }
  }

  async function handleSendMessage(messageText?: string) {
    const finalMessage = (messageText ?? input).trim();
    if (!finalMessage || sending) return;

    const timestamp = Date.now();
    const optimisticUserMessage: ChatMessageView = {
      id: `temp-user-${timestamp}`,
      session_id: selectedSessionId ?? "pending-session",
      role: "user",
      content: finalMessage,
      created_at: new Date().toISOString(),
    };
    const streamingAssistantMessage: ChatMessageView = {
      id: `temp-assistant-${timestamp}`,
      session_id: selectedSessionId ?? "pending-session",
      role: "assistant",
      content: "",
      created_at: new Date().toISOString(),
      status: "waiting",
    };

    setSending(true);
    setStopRequested(false);
    setChatError(null);
    setLastFailedMessage(null);
    setInput("");
    if (appConfig.chatMode === "non_streaming") {
      setStreamLifecycle((current) => ({
        ...current,
        isRequestInFlight: true,
      }));
      await handleSendMessageNonStreaming(finalMessage, optimisticUserMessage);
      return;
    }

    const abortController = new AbortController();
    await handleSendMessageStreaming(
      finalMessage,
      optimisticUserMessage,
      streamingAssistantMessage,
      abortController,
    );
  }

  function handleStopGeneration() {
    if (appConfig.chatMode !== "streaming") {
      return;
    }

    if (!abortControllerRef.current || streamStoppedByUserRef.current) {
      return;
    }

    streamStoppedByUserRef.current = true;
    setStopRequested(true);
    abortControllerRef.current.abort();
  }

  const generationBadgeLabel = streamLifecycle.isWaitingForFirstToken
    ? "Preparing"
    : sending
      ? "Generating"
      : "Ready";
  const isStreamingMode = appConfig.chatMode === "streaming";
  const statusDescription = isStreamingMode
    ? streamLifecycle.isWaitingForFirstToken
      ? "The model is preparing a response. Slow first-token starts are handled without treating them as failures."
      : selectedSessionId
        ? "The current session is connected to persisted history."
        : "A new session will be created automatically."
    : selectedSessionId
      ? "Non-streaming demo mode is enabled. Replies appear after the full response is ready."
      : "Non-streaming demo mode is enabled. A new session will be created automatically.";

  return (
    <section className="grid gap-6 xl:grid-cols-[320px_minmax(0,1fr)]">
      <Card className="h-full">
        <CardHeader>
          <div className="flex items-center justify-between gap-3">
            <CardTitle>Sessions</CardTitle>
            <Button variant="secondary" className="gap-2" onClick={handleCreateSession}>
              <MessageSquarePlus className="h-4 w-4" />
              New
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <Input
              className="pl-10"
              placeholder="Search sessions"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
          </div>

          {workspaceLoading ? (
            <LoadingState label="Loading sessions..." />
          ) : sidebarError ? (
            <ErrorState
              title="Session list unavailable"
              description={sidebarError}
              onRetry={() => void loadSessions(selectedSessionId)}
            />
          ) : filteredSessions.length === 0 ? (
            <Card className="border-dashed">
              <CardContent className="flex min-h-[360px] flex-col items-center justify-center gap-3 text-center">
                <p className="text-base font-medium text-slate-800">No sessions yet</p>
                <p className="max-w-xs text-sm leading-6 text-slate-500">
                  Create a new session or send a message from the chat panel to create one automatically.
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-2">
              {filteredSessions.map((session) => (
                <div
                  key={session.id}
                  onClick={() => setSelectedSessionId(session.id)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" || event.key === " ") {
                      event.preventDefault();
                      setSelectedSessionId(session.id);
                    }
                  }}
                  role="button"
                  tabIndex={0}
                  className={cn(
                    "w-full cursor-pointer rounded-2xl border p-4 text-left transition",
                    selectedSessionId === session.id
                      ? "border-primary/40 bg-primary/5"
                      : "border-border bg-slate-50/80 hover:border-primary/20 hover:bg-white",
                  )}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium text-slate-900">
                        {session.title}
                      </p>
                      <div className="mt-2 flex items-center gap-2 text-xs text-slate-500">
                        <Clock3 className="h-3.5 w-3.5" />
                        <span>{formatTime(session.updated_at)}</span>
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      className="px-2 py-2"
                      onClick={(event) => {
                        event.stopPropagation();
                        void handleDeleteSession(session.id);
                      }}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Card className="flex min-h-[760px] flex-col">
        <CardHeader className="border-b border-border/80">
          <div className="flex items-center justify-between gap-4">
            <div>
              <CardTitle>Chat Workspace</CardTitle>
              <p className="mt-1 text-sm text-slate-500">
                {isStreamingMode
                  ? "Streaming replies are shown live and finalized messages remain persisted after refresh."
                  : "Non-streaming replies return as complete messages and remain persisted after refresh."}
              </p>
            </div>
            <div className="flex items-center gap-2">
              {selectedKnowledgeBaseId ? (
                <Badge tone="neutral">
                  KB {knowledgeBases.find((item) => item.id === selectedKnowledgeBaseId)?.name ?? "Enabled"}
                </Badge>
              ) : null}
                {sending ? (
                  <Badge tone="warning">{generationBadgeLabel}</Badge>
                ) : (
                  <Badge tone="success">Ready</Badge>
                )}
              <Button
                variant="ghost"
                className="gap-2"
                onClick={() =>
                  selectedSessionId ? void loadMessages(selectedSessionId) : void loadSessions(selectedSessionId)
                }
              >
                <RefreshCw className="h-4 w-4" />
                Refresh
              </Button>
            </div>
          </div>
        </CardHeader>

        <CardContent className="flex flex-1 flex-col gap-4 pt-6">
          <div className="grid gap-4 rounded-3xl border border-border bg-slate-50/80 p-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_minmax(0,1fr)_auto] lg:items-end">
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700">Model</label>
              <div className="space-y-2">
                <select
                  className="h-11 w-full rounded-xl border border-border bg-white px-4 text-sm text-slate-900 outline-none focus:border-primary focus:ring-4 focus:ring-primary/10 disabled:cursor-not-allowed disabled:bg-slate-100"
                  value={selectedModel}
                  onChange={(event) => setSelectedModel(event.target.value)}
                  disabled={sending || modelsLoading || availableModels.length === 0}
                >
                  {availableModels.length === 0 ? (
                    <option value={selectedModel}>
                      {modelsLoading ? "Loading models..." : selectedModel}
                    </option>
                  ) : (
                    availableModels.map((model) => (
                      <option key={model.name} value={model.name}>
                        {model.name}
                      </option>
                    ))
                  )}
                </select>
                <div className="text-xs text-slate-500">
                  {modelsError
                    ? `Model list unavailable. Falling back to ${selectedModel}.`
                    : modelsLoading
                      ? "Loading local Ollama models..."
                      : `Using ${selectedModel}`}
                </div>
              </div>
            </div>
            <div className="space-y-2">
              <label className="flex items-center gap-2 text-sm font-medium text-slate-700">
                <Database className="h-4 w-4 text-primary" />
                Knowledge base
              </label>
              <select
                className="h-11 w-full rounded-xl border border-border bg-white px-4 text-sm text-slate-900 outline-none focus:border-primary focus:ring-4 focus:ring-primary/10"
                value={selectedKnowledgeBaseId}
                onChange={(event) => setSelectedKnowledgeBaseId(event.target.value)}
                disabled={sending}
              >
                <option value="">Disabled</option>
                {knowledgeBases.map((knowledgeBase) => (
                  <option key={knowledgeBase.id} value={knowledgeBase.id}>
                    {knowledgeBase.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700">Explicit memory</label>
              <div className="rounded-xl border border-border bg-white px-4 py-3">
                <Switch
                  checked={useMemory}
                  label="Enable explicit memory"
                  disabled={sending}
                  onCheckedChange={setUseMemory}
                />
              </div>
            </div>
            <div className="text-sm text-slate-500">
              <div>
                {modelsError ? "Using default model fallback." : `Selected model: ${selectedModel}`}
              </div>
              <div>
                {selectedKnowledgeBaseId
                  ? `Last KB hit count: ${lastRetrievalHitsCount}`
                  : "Knowledge base is disabled."}
              </div>
              <div className="mt-1">
                {useMemory
                  ? `Last memory hit count: ${lastMemoryHitsCount}`
                  : "Explicit memory is disabled."}
              </div>
            </div>
          </div>

          {chatError ? (
            <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
              <div className="font-medium">Message failed</div>
              <div className="mt-1">{chatError}</div>
              {lastFailedMessage ? (
                <Button
                  variant="danger"
                  className="mt-3"
                  onClick={() => void handleSendMessage(lastFailedMessage)}
                  disabled={sending}
                >
                  Retry last message
                </Button>
              ) : null}
            </div>
          ) : null}

          <div className="flex-1 rounded-[1.5rem] bg-slate-50/90 p-4">
                {messagesLoading ? (
              <LoadingState label="Loading messages..." />
            ) : messages.length === 0 ? (
              <div className="flex h-full min-h-[420px] flex-col items-center justify-center text-center">
                <p className="text-base font-medium text-slate-800">Start a new conversation</p>
                <p className="mt-2 max-w-md text-sm leading-6 text-slate-500">
                  {isStreamingMode
                    ? "The assistant streams its reply live and stores the final result in SQLite after completion."
                    : "The assistant returns a complete reply after generation finishes and stores the result in SQLite."}
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={cn(
                      "max-w-3xl rounded-[1.35rem] px-4 py-3 text-sm leading-7 shadow-sm",
                      message.role === "assistant"
                        ? "border border-border bg-white text-slate-800"
                        : "ml-auto bg-slate-950 text-white",
                    )}
                  >
                    <MessageContent content={message.content} role={message.role} />
                    {message.status === "waiting" ? (
                      <div className="mt-2 flex items-center gap-2 text-xs text-amber-600">
                        <LoaderCircle className="h-3.5 w-3.5 animate-spin" />
                        Model is preparing a response...
                      </div>
                    ) : null}
                    {message.status === "streaming" ? (
                      <div className="mt-2 flex items-center gap-2 text-xs text-amber-600">
                        <LoaderCircle className="h-3.5 w-3.5 animate-spin" />
                        Streaming reply
                      </div>
                    ) : null}
                    {message.status === "stopped" ? (
                      <div className="mt-2 text-xs text-slate-500">
                        {message.note ?? "Generation stopped"}
                      </div>
                    ) : null}
                    {message.status === "error" ? (
                      <div className="mt-2 text-xs text-rose-500">
                        {message.note ?? "Generation interrupted"}
                      </div>
                    ) : null}
                    <div
                      className={cn(
                        "mt-2 text-xs",
                        message.role === "assistant" ? "text-slate-400" : "text-white/70",
                      )}
                    >
                      {formatTime(message.created_at)}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="rounded-[1.6rem] border border-border bg-white p-4 shadow-soft">
            <Textarea
              placeholder="Type a message and press Ctrl/Cmd + Enter or click Send."
              className="min-h-[140px] resize-none"
              value={input}
              onChange={(event) => setInput(event.target.value)}
              disabled={sending}
              onKeyDown={(event) => {
                if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
                  event.preventDefault();
                  void handleSendMessage();
                }
              }}
            />
            <div className="mt-4 flex flex-col gap-3 border-t border-border pt-4 md:flex-row md:items-center md:justify-between">
              <div className="text-sm text-slate-500">
                {statusDescription}
              </div>
              <Button
                className="gap-2"
                variant={sending && isStreamingMode ? "secondary" : "primary"}
                onClick={() =>
                  sending && isStreamingMode ? handleStopGeneration() : void handleSendMessage()
                }
                disabled={sending ? (isStreamingMode ? stopRequested : true) : !input.trim()}
              >
                {sending && isStreamingMode ? (
                  <Square className="h-4 w-4" />
                ) : (
                  <SendHorizonal className="h-4 w-4" />
                )}
                {sending
                  ? isStreamingMode
                    ? stopRequested
                      ? "Stopping..."
                      : "Stop generation"
                    : "Generating..."
                  : "Send message"}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </section>
  );
}
