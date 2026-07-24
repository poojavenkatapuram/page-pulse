import type { LucideIcon } from "lucide-react";

export type MetricTone = "blue" | "emerald" | "amber" | "rose" | "violet";

export interface MetricCardProps {
  label: string;
  value: string;
  description: string;
  icon: LucideIcon;
  tone?: MetricTone;
}

const toneClasses = {
  blue: "bg-blue-50 text-blue-700",
  emerald: "bg-emerald-50 text-emerald-700",
  amber: "bg-amber-50 text-amber-700",
  rose: "bg-rose-50 text-rose-700",
  violet: "bg-violet-50 text-violet-700",
};

export function MetricCard({ label, value, description, icon: Icon, tone = "blue" }: MetricCardProps) {
  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-panel">
      <div className="flex items-start justify-between gap-4">
        <p className="text-sm font-semibold text-slate-600">{label}</p>
        <div className={`grid size-9 place-items-center rounded-xl ${toneClasses[tone]}`}>
          <Icon aria-hidden="true" className="size-4" />
        </div>
      </div>
      <p className="mt-5 text-3xl font-bold tracking-tight text-slate-950">{value}</p>
      <p className="mt-1 text-sm text-slate-500">{description}</p>
    </article>
  );
}
