import { Clock3, FileText, Heading1, ImageOff, ListTree, Server } from "lucide-react";

import { MetricCard, type MetricCardProps, type MetricTone } from "@/components/metric-card";
import { ResultCard } from "@/components/result-card";
import type { AuditReport } from "@/types/audit";

interface AuditResultsProps {
  report: AuditReport;
}

export function AuditResults({ report }: AuditResultsProps) {
  const statusTone: MetricTone = report.http_status >= 200 && report.http_status < 400 ? "emerald" : "rose";
  const metrics: MetricCardProps[] = [
    { label: "HTTP status", value: String(report.http_status), description: "Response from the target", icon: Server, tone: statusTone },
    { label: "Response time", value: `${Math.round(report.response_time_ms)} ms`, description: "Time to fetch the page", icon: Clock3, tone: "blue" },
    { label: "H1 count", value: String(report.h1_count), description: "Top-level page headings", icon: Heading1, tone: "violet" },
    { label: "Missing alt images", value: String(report.images_missing_alt_text), description: "Images needing alt text", icon: ImageOff, tone: "amber" },
    { label: "Word count", value: report.approximate_word_count.toLocaleString(), description: "Approximate visible words", icon: ListTree, tone: "rose" },
  ];

  return (
    <section aria-labelledby="audit-results-heading">
      <div className="flex flex-col justify-between gap-2 sm:flex-row sm:items-end">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wider text-blue-700">Audit complete</p>
          <h2 id="audit-results-heading" className="mt-1 text-2xl font-bold tracking-tight text-slate-950">
            Page report
          </h2>
        </div>
        <p className="max-w-full truncate text-sm text-slate-500" title={report.url}>
          {report.url}
        </p>
      </div>

      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        {metrics.map((metric) => (
          <MetricCard key={metric.label} {...metric} />
        ))}
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <ResultCard label="Page title" value={report.title} emptyMessage="No page title found." />
        <ResultCard label="Meta description" value={report.meta_description} emptyMessage="No meta description found." />
      </div>
      <div className="mt-4 flex items-center gap-2 text-sm text-slate-500">
        <FileText aria-hidden="true" className="size-4" />
        Metrics are based on the server-rendered HTML returned by the page.
      </div>
    </section>
  );
}
