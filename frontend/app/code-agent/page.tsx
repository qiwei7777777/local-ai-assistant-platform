import { CodeAgentWorkspace } from "@/components/code-agent/code-agent-workspace";
import { PageHeader } from "@/components/page-header";

export default function CodeAgentPage() {
  return (
    <>
      <PageHeader
        eyebrow="Code Agent"
        title="Agentic Coding Workspace"
        description="Inspect the local repository, generate file drafts, write approved files into the workspace, and run safe validation commands."
        status="Workspace-aware file writer"
      />
      <CodeAgentWorkspace />
    </>
  );
}
