export function LoadingState() {
  return (
    <div className="rounded-2xl border border-blue-100 bg-blue-50 px-6 py-10 text-center" role="status" aria-live="polite">
      <div className="mx-auto size-8 animate-spin rounded-full border-4 border-blue-200 border-t-blue-700" aria-hidden="true" />
      <p className="mt-4 font-semibold text-slate-900">Auditing your page</p>
      <p className="mt-1 text-sm text-slate-600">Fetching and analyzing the page signals...</p>
    </div>
  );
}
