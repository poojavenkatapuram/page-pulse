interface ResultCardProps {
  label: string;
  value: string | null;
  emptyMessage: string;
}

export function ResultCard({ label, value, emptyMessage }: ResultCardProps) {
  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-panel">
      <h3 className="text-sm font-semibold text-slate-600">{label}</h3>
      <p className="mt-3 break-words text-base leading-7 text-slate-900">{value ?? <span className="text-slate-400">{emptyMessage}</span>}</p>
    </article>
  );
}
