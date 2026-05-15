"use client";

import { useEffect, useMemo, useState } from "react";
import { FileCode2, LoaderCircle, Play, RefreshCw, Save, ShieldCheck, Wand2 } from "lucide-react";

import { EmptyState, ErrorState, LoadingState } from "@/components/state-panels";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { apiClient } from "@/lib/api-client";
import { cn } from "@/lib/utils";
import type {
  CodeCommandData,
  CodeFileData,
  CodeFileSummary,
  CodeGenerateData,
  CodeWorkspaceData,
  CodeWriteData,
} from "@/types/api";

function formatSize(size: number) {
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / 1024 / 1024).toFixed(1)} MB`;
}

export function CodeAgentWorkspace() {
  const [workspace, setWorkspace] = useState<CodeWorkspaceData | null>(null);
  const [selectedPaths, setSelectedPaths] = useState<string[]>(["README.md"]);
  const [activeFile, setActiveFile] = useState<CodeFileData | null>(null);
  const [task, setTask] = useState("Add a small feature and explain the implementation plan.");
  const [targetDirectory, setTargetDirectory] = useState("agent-output/demo-page");
  const [plan, setPlan] = useState("");
  const [generation, setGeneration] = useState<CodeGenerateData | null>(null);
  const [writeResult, setWriteResult] = useState<CodeWriteData | null>(null);
  const [commandResult, setCommandResult] = useState<CodeCommandData | null>(null);
  const [selectedCommand, setSelectedCommand] = useState("git status --short");
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [planning, setPlanning] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [writing, setWriting] = useState(false);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void loadWorkspace();
  }, []);

  const filteredFiles = useMemo(() => {
    if (!workspace) return [];
    const normalized = query.trim().toLowerCase();
    if (!normalized) return workspace.files;
    return workspace.files.filter((file) => file.path.toLowerCase().includes(normalized));
  }, [query, workspace]);

  async function loadWorkspace() {
    setLoading(true);
    setError(null);
    try {
      const result = await apiClient.inspectCodeWorkspace();
      setWorkspace(result);
      setSelectedCommand(result.allowed_commands[0] ?? "git status --short");
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Failed to inspect workspace.");
    } finally {
      setLoading(false);
    }
  }

  function togglePath(path: string) {
    setSelectedPaths((current) =>
      current.includes(path)
        ? current.filter((item) => item !== path)
        : [...current, path].slice(-8),
    );
  }

  async function openFile(file: CodeFileSummary) {
    setError(null);
    try {
      const result = await apiClient.readCodeFile(file.path);
      setActiveFile(result);
      if (!selectedPaths.includes(file.path)) {
        togglePath(file.path);
      }
    } catch (readError) {
      setError(readError instanceof Error ? readError.message : "Failed to read file.");
    }
  }

  async function createPlan() {
    if (!task.trim()) return;
    setPlanning(true);
    setPlan("");
    setError(null);
    try {
      const result = await apiClient.createCodePlan({
        task: task.trim(),
        file_paths: selectedPaths,
      });
      setPlan(result.plan);
    } catch (planError) {
      setError(planError instanceof Error ? planError.message : "Failed to create code plan.");
    } finally {
      setPlanning(false);
    }
  }

  async function generateFiles() {
    if (!task.trim() || !targetDirectory.trim()) return;
    setGenerating(true);
    setGeneration(null);
    setWriteResult(null);
    setError(null);
    try {
      const result = await apiClient.generateCodeFiles({
        task: task.trim(),
        target_directory: targetDirectory.trim(),
        file_paths: selectedPaths,
      });
      setGeneration(result);
    } catch (generateError) {
      setError(generateError instanceof Error ? generateError.message : "Failed to generate files.");
    } finally {
      setGenerating(false);
    }
  }

  async function writeGeneratedFiles(overwrite = false) {
    if (!generation?.files.length) return;
    setWriting(true);
    setWriteResult(null);
    setError(null);
    try {
      const result = await apiClient.writeCodeFiles({
        files: generation.files,
        overwrite,
      });
      setWriteResult(result);
      await loadWorkspace();
    } catch (writeError) {
      setError(writeError instanceof Error ? writeError.message : "Failed to write generated files.");
    } finally {
      setWriting(false);
    }
  }

  async function runCommand() {
    setRunning(true);
    setCommandResult(null);
    setError(null);
    try {
      const result = await apiClient.runCodeCommand(selectedCommand);
      setCommandResult(result);
    } catch (commandError) {
      setError(commandError instanceof Error ? commandError.message : "Command failed.");
    } finally {
      setRunning(false);
    }
  }

  if (loading) {
    return <LoadingState label="Inspecting code workspace..." />;
  }

  if (error && !workspace) {
    return <ErrorState title="Code workspace unavailable" description={error} onRetry={() => void loadWorkspace()} />;
  }

  if (!workspace) {
    return <EmptyState title="No workspace" description="The backend did not return a code workspace." />;
  }

  return (
    <section className="grid gap-6 xl:grid-cols-[360px_minmax(0,1fr)]">
      <Card className="h-fit">
        <CardHeader className="flex-row items-start justify-between gap-4">
          <div>
            <CardTitle>Repository Files</CardTitle>
            <CardDescription>{workspace.files.length} readable files under {workspace.root}</CardDescription>
          </div>
          <Button variant="ghost" className="px-3" onClick={() => void loadWorkspace()}>
            <RefreshCw className="h-4 w-4" />
          </Button>
        </CardHeader>
        <CardContent className="space-y-4">
          <Input placeholder="Search files" value={query} onChange={(event) => setQuery(event.target.value)} />
          <div className="max-h-[720px] space-y-2 overflow-auto pr-1">
            {filteredFiles.slice(0, 180).map((file) => {
              const selected = selectedPaths.includes(file.path);
              return (
                <button
                  type="button"
                  key={file.path}
                  onClick={() => void openFile(file)}
                  className={cn(
                    "w-full rounded-2xl border p-3 text-left transition",
                    selected ? "border-primary/40 bg-primary/5" : "border-border bg-slate-50/80 hover:bg-white",
                  )}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <FileCode2 className="h-4 w-4 text-primary" />
                        <p className="truncate text-sm font-medium text-slate-900">{file.name}</p>
                      </div>
                      <p className="mt-1 truncate text-xs text-slate-500">{file.path}</p>
                    </div>
                    <Badge tone={selected ? "success" : "neutral"}>{formatSize(file.size)}</Badge>
                  </div>
                </button>
              );
            })}
          </div>
        </CardContent>
      </Card>

      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Agent Task</CardTitle>
            <CardDescription>
              Select up to eight files as context. The model can plan changes or generate files you can write into the local workspace.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Textarea
              className="min-h-[130px]"
              value={task}
              onChange={(event) => setTask(event.target.value)}
              placeholder="Describe the coding task, page, or small project to create..."
            />
            <div className="grid gap-3 md:grid-cols-[minmax(0,1fr)_auto_auto] md:items-end">
              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-700">Write target directory</label>
                <Input
                  value={targetDirectory}
                  onChange={(event) => setTargetDirectory(event.target.value)}
                  placeholder="agent-output/demo-page"
                />
              </div>
              <Button className="gap-2" onClick={() => void createPlan()} disabled={planning || !task.trim()}>
                {planning ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <Wand2 className="h-4 w-4" />}
                Plan
              </Button>
              <Button
                className="gap-2"
                onClick={() => void generateFiles()}
                disabled={generating || !task.trim() || !targetDirectory.trim()}
              >
                {generating ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <FileCode2 className="h-4 w-4" />}
                Generate files
              </Button>
            </div>
            <div className="flex flex-wrap gap-2">
              {selectedPaths.map((path) => (
                <button
                  key={path}
                  type="button"
                  onClick={() => togglePath(path)}
                  className="rounded-full border border-primary/20 bg-primary/5 px-3 py-1 text-xs font-medium text-primary"
                >
                  {path}
                </button>
              ))}
            </div>
          </CardContent>
        </Card>

        {error ? <ErrorState title="Code Agent Error" description={error} /> : null}

        <div className="grid gap-6 2xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
          <Card>
            <CardHeader>
              <CardTitle>Selected File Preview</CardTitle>
              <CardDescription>{activeFile ? activeFile.path : "Open a file from the repository list."}</CardDescription>
            </CardHeader>
            <CardContent>
              {activeFile ? (
                <pre className="max-h-[620px] overflow-auto rounded-2xl bg-slate-950 p-4 text-xs leading-6 text-slate-100">
                  <code>{activeFile.content}</code>
                </pre>
              ) : (
                <EmptyState title="No file selected" description="Open a file to inspect source code and add it to agent context." />
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Agent Plan</CardTitle>
              <CardDescription>Audit-friendly output for review before editing.</CardDescription>
            </CardHeader>
            <CardContent>
              {planning ? (
                <LoadingState label="The local model is reasoning over selected files..." />
              ) : plan ? (
                <pre className="max-h-[620px] overflow-auto whitespace-pre-wrap rounded-2xl bg-slate-950 p-4 text-sm leading-7 text-slate-100">
                  {plan}
                </pre>
              ) : (
                <EmptyState title="No plan yet" description="Generate a plan to get code-level implementation guidance." />
              )}
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Generated Files</CardTitle>
            <CardDescription>
              Review the model output, then write it into the local workspace. Existing files require explicit overwrite.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {generating ? (
              <LoadingState label="The local model is creating file contents..." />
            ) : generation ? (
              <>
                {generation.notes ? (
                  <div className="rounded-2xl border border-border bg-slate-50 p-4 text-sm leading-6 text-slate-600">
                    {generation.notes}
                  </div>
                ) : null}
                <div className="grid gap-4 lg:grid-cols-2">
                  {generation.files.map((file) => (
                    <div key={file.path} className="overflow-hidden rounded-2xl border border-border bg-white">
                      <div className="flex items-center justify-between gap-3 border-b border-border bg-slate-50 px-4 py-3">
                        <div className="min-w-0">
                          <p className="truncate text-sm font-semibold text-slate-900">{file.path}</p>
                          <p className="text-xs text-slate-500">{file.language} - {file.action}</p>
                        </div>
                        <Badge tone={file.exists ? "warning" : "success"}>{file.exists ? "Exists" : "New"}</Badge>
                      </div>
                      <pre className="max-h-[320px] overflow-auto bg-slate-950 p-4 text-xs leading-6 text-slate-100">
                        {file.content}
                      </pre>
                    </div>
                  ))}
                </div>
                <div className="flex flex-wrap gap-3">
                  <Button className="gap-2" onClick={() => void writeGeneratedFiles(false)} disabled={writing}>
                    {writing ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                    Write new files
                  </Button>
                  <Button variant="secondary" onClick={() => void writeGeneratedFiles(true)} disabled={writing}>
                    Overwrite if needed
                  </Button>
                </div>
                {writeResult ? (
                  <div className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
                    Wrote {writeResult.written_files.length} file(s): {writeResult.written_files.map((file) => file.path).join(", ")}
                  </div>
                ) : null}
              </>
            ) : (
              <EmptyState
                title="No files generated"
                description="Describe a small page, script, or feature, then use Generate files to create writable file drafts."
              />
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <ShieldCheck className="h-5 w-5 text-emerald-600" />
              <CardTitle>Safe Command Runner</CardTitle>
            </div>
            <CardDescription>
              Commands are backend-whitelisted so the demo can prove validation without granting arbitrary shell access.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-col gap-3 md:flex-row">
              <select
                className="h-11 flex-1 rounded-xl border border-border bg-white px-4 text-sm text-slate-900 outline-none focus:border-primary focus:ring-4 focus:ring-primary/10"
                value={selectedCommand}
                onChange={(event) => setSelectedCommand(event.target.value)}
              >
                {workspace.allowed_commands.map((command) => (
                  <option key={command} value={command}>
                    {command}
                  </option>
                ))}
              </select>
              <Button className="gap-2" onClick={() => void runCommand()} disabled={running}>
                {running ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
                Run
              </Button>
            </div>
            {commandResult ? (
              <div className="grid gap-4 lg:grid-cols-3">
                <div className="rounded-2xl border border-border bg-slate-50 p-4">
                  <p className="text-xs uppercase text-slate-500">Exit code</p>
                  <p className="mt-2 text-2xl font-semibold text-slate-950">{commandResult.exit_code}</p>
                  <p className="mt-1 text-xs text-slate-500">{commandResult.duration_ms} ms</p>
                </div>
                <pre className="max-h-[260px] overflow-auto rounded-2xl bg-slate-950 p-4 text-xs leading-6 text-slate-100 lg:col-span-2">
                  {commandResult.stdout || commandResult.stderr || "Command produced no output."}
                </pre>
              </div>
            ) : null}
          </CardContent>
        </Card>
      </div>
    </section>
  );
}
