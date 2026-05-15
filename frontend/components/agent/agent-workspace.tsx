"use client";

import { useEffect, useRef, useState } from "react";
import {
  LoaderCircle,
  MessageSquarePlus,
  RefreshCw,
  SendHorizonal,
  Wrench,
  ChevronDown,
  ChevronRight,
  Clock3,
  AlertTriangle,
  Inbox,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { ApiClientError, apiClient } from "@/lib/api-client";
import { appConfig } from "@/lib/config";
import { cn } from "@/lib/utils";
import type { AgentToolCallRecord } from "@/types/api";

type AgentMessage = {
  role: "user" | "assistant";
  content: string;
  toolCalls?: AgentToolCallRecord[];
  model?: string;
  iterations?: number;
  error?: string;
};

const DEFAULT_MESSAGE = "Explore the workspace and tell me about the project structure.";

export function AgentWorkspace() {
  const [messages, setMessages] = useState<AgentMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [expandedTools, setExpandedTools] = useState<Set<number>>(new Set());
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const toggleTool = (index: number) => {
    setExpandedTools((prev) => {
      const next = new Set(prev);
      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }
      return next;
    });
  };

  const sendMessage = async (text?: string) => {
    const messageText = (text ?? input).trim();
    if (!messageText || loading) return;

    setInput("");
    setError(null);

    const userMsg: AgentMessage = { role: "user", content: messageText };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const result = await apiClient.agentChat({
        message: messageText,
        session_id: sessionId ?? undefined,
        model: appConfig.defaultModel,
      });

      if (!sessionId) {
        setSessionId(result.session_id);
      }

      const assistantMsg: AgentMessage = {
        role: "assistant",
        content: result.content,
        toolCalls: result.tool_calls_made,
        model: result.model,
        iterations: result.iterations,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      const message =
        err instanceof ApiClientError ? err.message : "An unexpected error occurred.";
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "", error: message },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const resetSession = () => {
    setMessages([]);
    setSessionId(null);
    setError(null);
    setExpandedTools(new Set());
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  if (messages.length === 0 && !loading) {
    return (
      <Card className="border-dashed">
        <CardContent className="flex min-h-[420px] flex-col items-center justify-center gap-4 text-center">
          <Inbox className="h-10 w-10 text-slate-300" />
          <div className="space-y-2">
            <h3 className="text-lg font-semibold text-slate-800">Agent Chat</h3>
            <p className="max-w-md text-sm leading-6 text-slate-500">
              The agent can list directories, read files, and search code in your
              workspace. It reasons through multiple tool calls before answering.
            </p>
          </div>
          <div className="flex gap-2">
            <Button onClick={() => sendMessage(DEFAULT_MESSAGE)}>
              <RefreshCw className="mr-2 h-4 w-4" />
              Explore Workspace
            </Button>
            <Textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  sendMessage();
                }
              }}
              placeholder="Or type a custom task..."
              className="h-10 min-h-0 w-72 resize-none py-2"
            />
            <Button
              onClick={() => sendMessage()}
              disabled={!input.trim()}
            >
              <SendHorizonal className="h-4 w-4" />
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between py-3">
          <CardTitle className="text-base">Agent Chat</CardTitle>
          <div className="flex items-center gap-2">
            {sessionId && (
              <span className="text-xs text-slate-400">
                Session: {sessionId.slice(0, 8)}...
              </span>
            )}
            <Button variant="secondary" className="h-8 px-3 text-xs" onClick={resetSession}>
              <MessageSquarePlus className="mr-1 h-3.5 w-3.5" />
              New Session
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="max-h-[60vh] space-y-4 overflow-y-auto pr-2">
            {messages.map((msg, i) => (
              <div
                key={i}
                className={cn(
                  "flex gap-3",
                  msg.role === "user" ? "justify-end" : "justify-start",
                )}
              >
                <div
                  className={cn(
                    "max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed",
                    msg.role === "user"
                      ? "bg-slate-900 text-white"
                      : msg.error
                        ? "border border-rose-200 bg-rose-50 text-rose-800"
                        : "border bg-white text-slate-700",
                  )}
                >
                  {msg.error ? (
                    <div className="flex items-start gap-2">
                      <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-rose-500" />
                      <span>{msg.error}</span>
                    </div>
                  ) : (
                    <>
                      <div className="whitespace-pre-wrap">{msg.content}</div>

                      {msg.toolCalls && msg.toolCalls.length > 0 && (
                        <div className="mt-3 space-y-2 border-t pt-3">
                          <p className="text-xs font-medium text-slate-500">
                            Tools used ({msg.toolCalls.length}) &middot;{" "}
                            {msg.iterations} iteration{msg.iterations !== 1 ? "s" : ""}
                          </p>
                          {msg.toolCalls.map((tc, j) => {
                            const globalIndex = i * 100 + j;
                            const isExpanded = expandedTools.has(globalIndex);
                            return (
                              <div
                                key={j}
                                className="rounded-xl border bg-slate-50"
                              >
                                <button
                                  type="button"
                                  onClick={() => toggleTool(globalIndex)}
                                  className="flex w-full items-center gap-2 px-3 py-2 text-left text-xs font-medium text-slate-600 hover:bg-slate-100"
                                >
                                  {isExpanded ? (
                                    <ChevronDown className="h-3.5 w-3.5" />
                                  ) : (
                                    <ChevronRight className="h-3.5 w-3.5" />
                                  )}
                                  <Wrench className="h-3.5 w-3.5" />
                                  <span className="font-mono">{tc.tool_name}</span>
                                  <Clock3 className="ml-auto h-3 w-3 text-slate-400" />
                                  <span className="text-slate-400">
                                    {tc.duration_ms}ms
                                  </span>
                                </button>
                                {isExpanded && (
                                  <div className="border-t px-3 py-2 text-xs">
                                    <div className="mb-1.5">
                                      <span className="font-medium text-slate-500">
                                        Arguments:{" "}
                                      </span>
                                      <code className="text-slate-700">
                                        {JSON.stringify(tc.arguments)}
                                      </code>
                                    </div>
                                    <div>
                                      <span className="font-medium text-slate-500">
                                        Result:{" "}
                                      </span>
                                      <pre className="mt-1 max-h-48 overflow-auto whitespace-pre-wrap rounded bg-slate-100 p-2 text-slate-700">
                                        {tc.result_summary}
                                      </pre>
                                    </div>
                                  </div>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      )}

                      {msg.model && (
                        <div className="mt-2 text-xs text-slate-400">
                          Model: {msg.model}
                        </div>
                      )}
                    </>
                  )}
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex justify-start">
                <div className="flex items-center gap-2 rounded-2xl border bg-white px-4 py-3 text-sm text-slate-500">
                  <LoaderCircle className="h-4 w-4 animate-spin" />
                  Agent is working... this may take 30-90 seconds
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="flex items-end gap-3 py-3">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={loading}
            placeholder="Ask the agent to explore or modify the workspace..."
            className="min-h-[48px] flex-1 resize-none"
            rows={2}
          />
          <Button
            onClick={() => sendMessage()}
            disabled={loading || !input.trim()}
            className="shrink-0"
          >
            {loading ? (
              <LoaderCircle className="h-4 w-4 animate-spin" />
            ) : (
              <SendHorizonal className="h-4 w-4" />
            )}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
