"use client";

import { useEffect, useState } from "react";

import {
  DeveloperDashboard,
  getDeveloperStatus,
  loadDeveloperDiagnostics,
  type DeveloperDiagnosticsState,
} from "@/components/developer/developer-dashboard";
import { PageHeader } from "@/components/page-header";

const initialState: DeveloperDiagnosticsState = {
  health: null,
  models: null,
  healthError: null,
  modelsError: null,
  isLoading: true,
};

export default function DeveloperPage() {
  const [state, setState] = useState<DeveloperDiagnosticsState>(initialState);

  async function reload() {
    setState((current) => ({
      ...current,
      isLoading: true,
      healthError: null,
      modelsError: null,
    }));

    const nextState = await loadDeveloperDiagnostics();
    setState({
      ...nextState,
      isLoading: false,
    });
  }

  useEffect(() => {
    void reload();
  }, []);

  return (
    <>
      <PageHeader
        eyebrow="Developer"
        title="Developer Console"
        description="This page verifies whether the frontend can really reach backend health and model endpoints, and shows a clear success or failure state once loading completes."
        status={getDeveloperStatus(state)}
      />
      <DeveloperDashboard {...state} onReload={() => void reload()} />
    </>
  );
}
