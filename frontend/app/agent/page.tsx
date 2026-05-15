import { AgentWorkspace } from "@/components/agent/agent-workspace";
import { PageHeader } from "@/components/page-header";

export default function AgentPage() {
  return (
    <>
      <PageHeader
        eyebrow="Agent"
        title="Tool-Calling Agent"
        description="A conversational agent that uses tools — listing directories, reading files, and searching code — to explore and reason about your workspace."
        status="Multi-turn tool-calling loop"
      />
      <AgentWorkspace />
    </>
  );
}
