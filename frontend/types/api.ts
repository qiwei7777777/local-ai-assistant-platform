export type ApiError = {
  code: string;
  message: string;
  details: Record<string, unknown>;
};

export type ApiResponse<T> = {
  success: boolean;
  data: T | null;
  error: ApiError | null;
};

export type HealthData = {
  app: string;
  version: string;
  environment: string;
  database: string;
  ollama: string;
  default_model: string;
};

export type ModelInfo = {
  name: string;
  size: number | null;
  modified_at: string | null;
  digest: string | null;
};

export type ModelsData = {
  default_model: string;
  models: ModelInfo[];
};

export type SessionSummary = {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
};

export type SessionListData = {
  sessions: SessionSummary[];
};

export type Message = {
  id: string;
  session_id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
};

export type MessageListData = {
  session_id: string;
  messages: Message[];
};

export type ChatResult = {
  session: SessionSummary;
  user_message: Message;
  assistant_message: Message;
  model: string;
  knowledge_base_id: string | null;
  retrieval_hits_count: number;
  used_memory: boolean;
  memory_hits_count: number;
};

export type ChatStreamChunkEvent = {
  type: "chunk";
  content: string;
};

export type ChatStreamDoneEvent = {
  type: "done";
  data: ChatResult;
};

export type ChatStreamErrorEvent = {
  type: "error";
  error: {
    code: string;
    message: string;
    details: Record<string, unknown>;
  };
};

export type FileRecord = {
  id: string;
  original_name: string;
  stored_path: string;
  mime_type: string | null;
  extension: string | null;
  size: number;
  status: string;
  error_message: string | null;
  extracted_text_length: number;
  created_at: string;
  updated_at: string;
};

export type FileListData = {
  files: FileRecord[];
};

export type KnowledgeBase = {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
};

export type KnowledgeBaseListData = {
  knowledge_bases: KnowledgeBase[];
};

export type KnowledgeBaseFile = {
  id: string;
  knowledge_base_id: string;
  file_id: string;
  created_at: string;
  file: FileRecord;
};

export type KnowledgeBaseFileListData = {
  knowledge_base_id: string;
  files: KnowledgeBaseFile[];
};

export type RetrievalHit = {
  chunk_id: string;
  file_id: string;
  file_name: string;
  chunk_index: number;
  score: number;
  content: string;
};

export type RetrievalSearchData = {
  knowledge_base_id: string;
  query: string;
  hits: RetrievalHit[];
};

export type Memory = {
  id: string;
  content: string;
  source: string;
  created_at: string;
  metadata_json: string | null;
};

export type MemoryListData = {
  memories: Memory[];
};

export type CodeFileSummary = {
  path: string;
  name: string;
  extension: string;
  size: number;
  modified_at: string;
};

export type CodeWorkspaceData = {
  root: string;
  files: CodeFileSummary[];
  ignored_directories: string[];
  allowed_commands: string[];
};

export type CodeFileData = {
  path: string;
  language: string;
  size: number;
  content: string;
};

export type CodePlanData = {
  task: string;
  model: string;
  context_files: CodeFileData[];
  plan: string;
};

export type CodeGeneratedFile = {
  path: string;
  content: string;
  language: string;
  action: string;
  exists: boolean;
};

export type CodeGenerateData = {
  task: string;
  model: string;
  target_directory: string;
  files: CodeGeneratedFile[];
  notes: string;
};

export type CodeWrittenFile = {
  path: string;
  bytes: number;
  created: boolean;
};

export type CodeWriteData = {
  written_files: CodeWrittenFile[];
};

export type CodeCommandData = {
  command: string;
  exit_code: number;
  stdout: string;
  stderr: string;
  duration_ms: number;
};

export type AgentToolCall = {
  name: string;
  arguments: Record<string, unknown>;
};

export type AgentToolCallRecord = {
  tool_name: string;
  arguments: Record<string, unknown>;
  result_summary: string;
  duration_ms: number;
};

export type AgentChatData = {
  session_id: string;
  user_message_id: string;
  assistant_message_id: string;
  model: string;
  content: string;
  tool_calls_made: AgentToolCallRecord[];
  iterations: number;
};
