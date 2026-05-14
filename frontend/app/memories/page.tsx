import { MemoryWorkspace } from "@/components/memory/memory-workspace";
import { PageHeader } from "@/components/page-header";

export default function MemoriesPage() {
  return (
    <>
      <PageHeader
        eyebrow="Memory"
        title="Explicit Long-Term Memory"
        description="Manage durable user preferences and context. Memories are visible, deletable, and used in chat only when enabled."
        status="Explicit, controlled, removable"
      />
      <MemoryWorkspace />
    </>
  );
}
