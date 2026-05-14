import { PageHeader } from "@/components/page-header";
import { SettingsPanel } from "@/components/settings/settings-panel";

export default function SettingsPage() {
  return (
    <>
      <PageHeader
        eyebrow="Settings"
        title="System Settings"
        description="Review model runtime, default model, and chat parameter structure before adding persisted settings."
        status="Configuration preview"
      />
      <SettingsPanel />
    </>
  );
}
