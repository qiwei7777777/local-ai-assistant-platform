import { Badge } from "@/components/ui/badge";

type PageHeaderProps = {
  eyebrow: string;
  title: string;
  description: string;
  status?: string;
};

export function PageHeader({
  eyebrow,
  title,
  description,
  status,
}: PageHeaderProps) {
  return (
    <section className="rounded-[1.8rem] border border-border/80 bg-white/80 p-6 shadow-soft backdrop-blur md:p-8">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-primary">
            {eyebrow}
          </p>
          <h1 className="mt-3 text-3xl font-semibold tracking-tight text-slate-950 md:text-4xl">
            {title}
          </h1>
          <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-500 md:text-base">
            {description}
          </p>
        </div>
        {status ? <Badge tone="neutral">{status}</Badge> : null}
      </div>
    </section>
  );
}
