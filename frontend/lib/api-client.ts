import { appConfig } from "@/lib/config";
import type {
  AgentChatData,
  AgentToolCall,
  ApiResponse,
  ChatResult,
  CodeCommandData,
  CodeFileData,
  CodeGenerateData,
  CodeGeneratedFile,
  CodePlanData,
  CodeWriteData,
  CodeWorkspaceData,
  ChatStreamDoneEvent,
  ChatStreamErrorEvent,
  FileListData,
  HealthData,
  KnowledgeBase,
  KnowledgeBaseFile,
  KnowledgeBaseFileListData,
  KnowledgeBaseListData,
  Memory,
  MemoryListData,
  MessageListData,
  ModelsData,
  RetrievalSearchData,
  SessionListData,
  SessionSummary,
} from "@/types/api";

export class ApiClientError extends Error {
  code: string;
  status?: number;
  details?: Record<string, unknown>;

  constructor(
    message: string,
    options?: {
      code?: string;
      status?: number;
      details?: Record<string, unknown>;
    },
  ) {
    super(message);
    this.name = "ApiClientError";
    this.code = options?.code ?? "API_ERROR";
    this.status = options?.status;
    this.details = options?.details;
  }
}

type ChatPayload = {
  session_id?: string;
  message: string;
  knowledge_base_id?: string;
  use_memory?: boolean;
  model?: string;
  temperature?: number;
  max_tokens?: number;
};

const DEFAULT_REQUEST_TIMEOUT_MS = 15000;
const CODE_AGENT_REQUEST_TIMEOUT_MS = 300000;
const DEFAULT_STREAM_START_TIMEOUT_MS = 120000;
const DEFAULT_STREAM_IDLE_TIMEOUT_MS = 60000;

type ApiRequestInit = RequestInit & {
  timeoutMs?: number;
};

function isAbortError(error: unknown) {
  return error instanceof DOMException && error.name === "AbortError";
}

function buildUrl(path: string) {
  if (appConfig.apiBaseUrl === "/api" && path.startsWith("/api/")) {
    return path;
  }

  return `${appConfig.apiBaseUrl}${path}`;
}

function createTimeoutSignal(signal?: AbortSignal, timeoutMs = DEFAULT_REQUEST_TIMEOUT_MS) {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => {
    controller.abort(new DOMException("Request timed out.", "TimeoutError"));
  }, timeoutMs);

  const abortFromParent = () => {
    controller.abort(signal?.reason);
  };

  if (signal) {
    if (signal.aborted) {
      abortFromParent();
    } else {
      signal.addEventListener("abort", abortFromParent, { once: true });
    }
  }

  return {
    signal: controller.signal,
    didTimeout() {
      return controller.signal.aborted && !signal?.aborted;
    },
    cleanup() {
      window.clearTimeout(timeoutId);
      if (signal) {
        signal.removeEventListener("abort", abortFromParent);
      }
    },
  };
}

async function parseErrorResponse(response: Response) {
  try {
    const payload = (await response.json()) as ApiResponse<null>;
    return new ApiClientError(payload.error?.message ?? "Request failed.", {
      code: payload.error?.code ?? "REQUEST_FAILED",
      status: response.status,
      details: payload.error?.details,
    });
  } catch {
    return new ApiClientError("The backend returned an unreadable response.", {
      code: "INVALID_RESPONSE",
      status: response.status,
    });
  }
}

async function request<T>(path: string, init?: ApiRequestInit): Promise<T> {
  let response: Response;
  const { timeoutMs, ...fetchInit } = init ?? {};
  const timeoutSignal = createTimeoutSignal(fetchInit.signal ?? undefined, timeoutMs);

  try {
    response = await fetch(buildUrl(path), {
      ...fetchInit,
      headers: {
        ...(fetchInit.headers ?? {}),
      },
      cache: "no-store",
      signal: timeoutSignal.signal,
    });
  } catch (error) {
    if (timeoutSignal.didTimeout()) {
      throw new ApiClientError("Request timed out while waiting for the backend.", {
        code: "REQUEST_TIMEOUT",
        details: {
          baseUrl: appConfig.apiBaseUrl,
          path,
        },
      });
    }

    throw new ApiClientError("Unable to connect to the backend service.", {
      code: "NETWORK_ERROR",
      details: {
        cause: error instanceof Error ? error.message : "Unknown network error",
        baseUrl: appConfig.apiBaseUrl,
      },
    });
  } finally {
    timeoutSignal.cleanup();
  }

  if (!response.ok) {
    throw await parseErrorResponse(response);
  }

  let payload: ApiResponse<T> | null = null;

  try {
    payload = (await response.json()) as ApiResponse<T>;
  } catch {
    throw new ApiClientError("The backend returned an unreadable response.", {
      code: "INVALID_RESPONSE",
      status: response.status,
    });
  }

  if (!payload.success || payload.data === null) {
    throw new ApiClientError(payload.error?.message ?? "Request failed.", {
      code: payload.error?.code ?? "REQUEST_FAILED",
      status: response.status,
      details: payload.error?.details,
    });
  }

  return payload.data;
}

function parseSseEvent(block: string) {
  const lines = block
    .split(/\r?\n/)
    .map((line) => line.trimEnd())
    .filter(Boolean);

  let eventName = "message";
  const dataLines: string[] = [];

  for (const line of lines) {
    if (line.startsWith("event:")) {
      eventName = line.slice("event:".length).trim();
      continue;
    }

    if (line.startsWith("data:")) {
      dataLines.push(line.slice("data:".length).trim());
    }
  }

  if (!dataLines.length) {
    return null;
  }

  return {
    event: eventName,
    data: JSON.parse(dataLines.join("\n")) as Record<string, unknown>,
  };
}

function handleStreamEvent(
  block: string,
  handlers: {
    onChunk: (content: string) => void;
    onDone: (data: ChatResult) => void;
    onFirstToken?: () => void;
  },
  streamState: {
    hasReceivedFirstToken: boolean;
  },
) {
  const parsedEvent = parseSseEvent(block);
  if (!parsedEvent) {
    return false;
  }

  if (parsedEvent.event === "chunk" && typeof parsedEvent.data.content === "string") {
    if (parsedEvent.data.content.length > 0 && !streamState.hasReceivedFirstToken) {
      streamState.hasReceivedFirstToken = true;
      handlers.onFirstToken?.();
    }
    handlers.onChunk(parsedEvent.data.content);
    return false;
  }

  if (parsedEvent.event === "done") {
    handlers.onDone(parsedEvent.data as ChatStreamDoneEvent["data"]);
    return true;
  }

  if (parsedEvent.event === "error") {
    const errorEvent = parsedEvent.data as ChatStreamErrorEvent["error"];
    throw new ApiClientError(errorEvent.message, {
      code: errorEvent.code,
      details: errorEvent.details,
    });
  }

  return false;
}

async function readWithTimeout(
  reader: ReadableStreamDefaultReader<Uint8Array>,
  timeoutMs: number,
  timeoutError: ApiClientError,
) {
  let timeoutId: number | undefined;

  try {
    return await Promise.race([
      reader.read(),
      new Promise<never>((_, reject) => {
        timeoutId = window.setTimeout(() => reject(timeoutError), timeoutMs);
      }),
    ]);
  } finally {
    if (timeoutId !== undefined) {
      window.clearTimeout(timeoutId);
    }
  }
}

export const apiClient = {
  getHealth() {
    return request<HealthData>("/api/health");
  },
  getModels() {
    return request<ModelsData>("/api/models");
  },
  listSessions() {
    return request<SessionListData>("/api/sessions");
  },
  createSession(title = "New Chat") {
    return request<SessionSummary>("/api/sessions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ title }),
    });
  },
  deleteSession(sessionId: string) {
    return request<{ deleted: boolean; session_id: string }>(`/api/sessions/${sessionId}`, {
      method: "DELETE",
    });
  },
  getSessionMessages(sessionId: string) {
    return request<MessageListData>(`/api/sessions/${sessionId}/messages`);
  },
  chat(payload: ChatPayload) {
    return request<ChatResult>("/api/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });
  },
  async chatStream(
    payload: ChatPayload,
    handlers: {
      onChunk: (content: string) => void;
      onDone: (data: ChatResult) => void;
      onFirstToken?: () => void;
    },
    options?: {
      signal?: AbortSignal;
      firstTokenTimeoutMs?: number;
      streamIdleTimeoutMs?: number;
    },
  ) {
    let response: Response;
    const timeoutSignal = createTimeoutSignal(options?.signal ?? undefined);
    const firstTokenTimeoutMs = options?.firstTokenTimeoutMs ?? DEFAULT_STREAM_START_TIMEOUT_MS;
    const streamIdleTimeoutMs = options?.streamIdleTimeoutMs ?? DEFAULT_STREAM_IDLE_TIMEOUT_MS;

    try {
      response = await fetch(buildUrl("/api/chat/stream"), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "text/event-stream",
        },
        body: JSON.stringify(payload),
        cache: "no-store",
        signal: timeoutSignal.signal,
      });
    } catch (error) {
      if (timeoutSignal.didTimeout()) {
        throw new ApiClientError("Streaming request timed out before the backend responded.", {
          code: "REQUEST_TIMEOUT",
          details: {
            baseUrl: appConfig.apiBaseUrl,
            path: "/api/chat/stream",
          },
        });
      }

      if (isAbortError(error)) {
        throw new ApiClientError("Request cancelled by user.", {
          code: "REQUEST_ABORTED",
        });
      }

      throw new ApiClientError("Unable to connect to the backend service.", {
        code: "NETWORK_ERROR",
        details: {
          cause: error instanceof Error ? error.message : "Unknown network error",
          baseUrl: appConfig.apiBaseUrl,
        },
      });
    } finally {
      timeoutSignal.cleanup();
    }

    if (!response.ok) {
      throw await parseErrorResponse(response);
    }

    if (!response.body) {
      throw new ApiClientError("Streaming response body is unavailable.", {
        code: "STREAM_UNAVAILABLE",
        status: response.status,
      });
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    const streamState = {
      hasReceivedFirstToken: false,
    };
    let buffer = "";

    try {
      while (true) {
        let readResult: ReadableStreamReadResult<Uint8Array>;
        try {
          readResult = await readWithTimeout(
            reader,
            streamState.hasReceivedFirstToken ? streamIdleTimeoutMs : firstTokenTimeoutMs,
            new ApiClientError(
              streamState.hasReceivedFirstToken
                ? "Generation stopped receiving stream updates for too long."
                : "Model took too long to start responding.",
              {
                code: streamState.hasReceivedFirstToken
                  ? "STREAM_IDLE_TIMEOUT"
                  : "FIRST_TOKEN_TIMEOUT",
                details: {
                  model: payload.model ?? appConfig.defaultModel,
                  first_token_timeout_ms: firstTokenTimeoutMs,
                  stream_idle_timeout_ms: streamIdleTimeoutMs,
                },
              },
            ),
          );
        } catch (error) {
          if (isAbortError(error)) {
            throw new ApiClientError("Request cancelled by user.", {
              code: "REQUEST_ABORTED",
            });
          }
          throw error;
        }

        const { value, done } = readResult;
        buffer += decoder.decode(value ?? new Uint8Array(), { stream: !done });

        const blocks = buffer.split("\n\n");
        buffer = blocks.pop() ?? "";

        for (const block of blocks) {
          if (handleStreamEvent(block, handlers, streamState)) {
            return;
          }
        }

        if (done) {
          if (buffer.trim() && handleStreamEvent(buffer, handlers, streamState)) {
            return;
          }
          break;
        }
      }
    } finally {
      reader.releaseLock();
    }

    throw new ApiClientError(
      streamState.hasReceivedFirstToken
        ? "Streaming response ended before completion."
        : "The stream ended before the model started responding.",
      {
        code: "STREAM_INTERRUPTED",
        details: {
          model: payload.model ?? appConfig.defaultModel,
          has_received_first_token: streamState.hasReceivedFirstToken,
        },
      },
    );
  },
  listFiles() {
    return request<FileListData>("/api/files");
  },
  uploadFile(file: File) {
    const formData = new FormData();
    formData.append("file", file);
    return request<{ id: string; [key: string]: unknown }>("/api/files/upload", {
      method: "POST",
      body: formData,
    });
  },
  listKnowledgeBases() {
    return request<KnowledgeBaseListData>("/api/knowledge-bases");
  },
  createKnowledgeBase(payload: { name: string; description?: string }) {
    return request<KnowledgeBase>("/api/knowledge-bases", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });
  },
  addFileToKnowledgeBase(knowledgeBaseId: string, fileId: string) {
    return request<KnowledgeBaseFile>(`/api/knowledge-bases/${knowledgeBaseId}/files`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ file_id: fileId }),
    });
  },
  listKnowledgeBaseFiles(knowledgeBaseId: string) {
    return request<KnowledgeBaseFileListData>(`/api/knowledge-bases/${knowledgeBaseId}/files`);
  },
  searchKnowledgeBase(payload: { knowledge_base_id: string; query: string; top_k?: number }) {
    return request<RetrievalSearchData>("/api/retrieval/search", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });
  },
  listMemories() {
    return request<MemoryListData>("/api/memories");
  },
  createMemory(payload: { content: string; source?: string }) {
    return request<Memory>("/api/memories", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });
  },
  deleteMemory(memoryId: string) {
    return request<{ deleted: boolean; memory_id: string }>(`/api/memories/${memoryId}`, {
      method: "DELETE",
    });
  },
  inspectCodeWorkspace() {
    return request<CodeWorkspaceData>("/api/code-agent/workspace");
  },
  readCodeFile(path: string) {
    return request<CodeFileData>("/api/code-agent/read", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ path }),
    });
  },
  createCodePlan(payload: { task: string; file_paths: string[]; model?: string }) {
    return request<CodePlanData>("/api/code-agent/plan", {
      method: "POST",
      timeoutMs: CODE_AGENT_REQUEST_TIMEOUT_MS,
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });
  },
  generateCodeFiles(payload: { task: string; target_directory: string; file_paths: string[]; model?: string }) {
    return request<CodeGenerateData>("/api/code-agent/generate", {
      method: "POST",
      timeoutMs: CODE_AGENT_REQUEST_TIMEOUT_MS,
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });
  },
  writeCodeFiles(payload: { files: CodeGeneratedFile[]; overwrite?: boolean }) {
    return request<CodeWriteData>("/api/code-agent/write", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });
  },
  runCodeCommand(command: string) {
    return request<CodeCommandData>("/api/code-agent/command", {
      method: "POST",
      timeoutMs: CODE_AGENT_REQUEST_TIMEOUT_MS,
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ command }),
    });
  },
  agentChat(payload: {
    message: string;
    session_id?: string;
    model?: string;
    temperature?: number;
    max_tokens?: number;
  }) {
    return request<AgentChatData>("/api/agent/chat", {
      method: "POST",
      timeoutMs: CODE_AGENT_REQUEST_TIMEOUT_MS,
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });
  },
};
