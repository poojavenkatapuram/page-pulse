import { ScanSearch } from "lucide-react";

export function EmptyState() {
  return (
    <div className="rounded-2xl border border-dashed border-slate-300 bg-white px-6 py-12 text-center shadow-panel">
      <div className="mx-auto grid size-11 place-items-center rounded-xl bg-slate-100 text-slate-600">
        <ScanSearch aria-hidden="true" className="size-5" />
      </div>
      <h2 className="mt-4 text-lg font-bold text-slate-900">Your audit will appear here</h2>
      <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-slate-600">
        Enter a website above to see its HTTP status, structure, metadata, and accessibility signals.
      </p>
    </div>
  );
}
