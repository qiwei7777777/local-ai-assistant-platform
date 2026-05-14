import { CodeAgentWorkspace } from "@/components/code-agent/code-agent-workspace";
import { PageHeader } from "@/components/page-header";

export default function CodeAgentPage() {
  return (
    <>
      <PageHeader
        eyebrow="Code Agent"
        title="Agentic Coding Workspace"
        description="Inspect the local repository, select files as context, ask the model for implementation plans, and run safe validation commands."
        status="Workspace-aware and audit-friendly"
      />
      <CodeAgentWorkspace />
    </>
  );
}
