"use client";

import type { HTMLAttributes, ReactNode } from "react";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { cn } from "@/lib/utils";

type MessageContentProps = {
  content: string;
  role: "user" | "assistant";
  className?: string;
};

type MarkdownCodeProps = HTMLAttributes<HTMLElement> & {
  children?: ReactNode;
  inline?: boolean;
};

function normalizeMessageContent(content: string) {
  return content.trim().replace(/\n{3,}/g, "\n\n");
}

export function MessageContent({
  content,
  role,
  className,
}: MessageContentProps) {
  if (role === "user") {
    return (
      <div className={cn("whitespace-pre-wrap break-words leading-7", className)}>
        {content}
      </div>
    );
  }

  return (
    <div className={cn("chat-markdown", className)}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          a: ({ className: linkClassName, ...props }) => (
            <a
              {...props}
              className={cn(
                "font-medium text-sky-700 underline decoration-sky-300 underline-offset-4 transition hover:text-sky-900",
                linkClassName,
              )}
              target="_blank"
              rel="noreferrer"
            />
          ),
          code: ({ inline, className: codeClassName, children, ...props }: MarkdownCodeProps) => {
            if (!inline) {
              return (
                <code
                  {...props}
                  className={cn(
                    "block min-w-full whitespace-pre text-[13px] leading-6 text-slate-100",
                    codeClassName,
                  )}
                >
                  {children}
                </code>
              );
            }

            return (
              <code
                {...props}
                className={cn(
                  "rounded-md bg-slate-100 px-1.5 py-0.5 font-mono text-[0.92em] text-slate-800",
                  codeClassName,
                )}
              >
                {children}
              </code>
            );
          },
          pre: ({ className: preClassName, ...props }) => (
            <pre
              {...props}
              className={cn(
                "my-4 overflow-x-auto rounded-2xl border border-slate-800 bg-slate-950 px-4 py-3 shadow-sm",
                preClassName,
              )}
            />
          ),
          table: ({ className: tableClassName, ...props }) => (
            <div className="my-4 overflow-x-auto">
              <table
                {...props}
                className={cn("min-w-full border-collapse text-left text-sm", tableClassName)}
              />
            </div>
          ),
          th: ({ className: thClassName, ...props }) => (
            <th
              {...props}
              className={cn(
                "border border-slate-200 bg-slate-100 px-3 py-2 font-semibold text-slate-900",
                thClassName,
              )}
            />
          ),
          td: ({ className: tdClassName, ...props }) => (
            <td
              {...props}
              className={cn("border border-slate-200 px-3 py-2 align-top", tdClassName)}
            />
          ),
        }}
      >
        {normalizeMessageContent(content)}
      </ReactMarkdown>
    </div>
  );
}
