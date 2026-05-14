import { AlertTriangle, Inbox, LoaderCircle } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

export function LoadingState({ label }: { label: string }) {
  return (
    <Card className="border-dashed">
      <CardContent className="flex min-h-[220px] flex-col items-center justify-center gap-3 text-center">
        <LoaderCircle className="h-7 w-7 animate-spin text-primary" />
        <p className="text-sm text-slate-500">{label}</p>
      </CardContent>
    </Card>
  );
}

export function EmptyState({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <Card className="border-dashed">
      <CardContent className="flex min-h-[220px] flex-col items-center justify-center gap-3 text-center">
        <Inbox className="h-8 w-8 text-slate-300" />
        <h3 className="text-base font-semibold text-slate-800">{title}</h3>
        <p className="max-w-md text-sm leading-6 text-slate-500">{description}</p>
      </CardContent>
    </Card>
  );
}

export function ErrorState({
  title,
  description,
  onRetry,
}: {
  title: string;
  description: string;
  onRetry?: () => void;
}) {
  return (
    <Card className="border-rose-200 bg-rose-50/70">
      <CardContent className="flex min-h-[220px] flex-col items-center justify-center gap-4 text-center">
        <AlertTriangle className="h-8 w-8 text-rose-500" />
        <div className="space-y-2">
          <h3 className="text-base font-semibold text-rose-900">{title}</h3>
          <p className="max-w-md text-sm leading-6 text-rose-700">{description}</p>
        </div>
        {onRetry ? (
          <Button variant="danger" onClick={onRetry}>
            Retry
          </Button>
        ) : null}
      </CardContent>
    </Card>
  );
}
