import { KnowledgeBaseWorkspace } from "@/components/knowledge-base/knowledge-base-workspace";
import { PageHeader } from "@/components/page-header";

export default function KnowledgeBasesPage() {
  return (
    <>
      <PageHeader
        eyebrow="Knowledge Base"
        title="Knowledge Bases and Retrieval"
        description="Upload files, inspect parsing status, attach files to local knowledge bases, and test retrieval before using context in chat."
        status="Upload, indexing, and search connected"
      />
      <KnowledgeBaseWorkspace />
    </>
  );
}
