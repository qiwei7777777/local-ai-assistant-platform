import { ChatWorkspace } from "@/components/chat/chat-workspace";
import { PageHeader } from "@/components/page-header";

export default function HomePage() {
  return (
    <>
      <PageHeader
        eyebrow="Chat Workspace"
        title="Local AI Assistant Workspace"
        description="A local-first chat surface backed by FastAPI, SQLite, Ollama, optional knowledge-base retrieval, and explicit memory."
        status="Production demo ready"
      />
      <ChatWorkspace />
    </>
  );
}
