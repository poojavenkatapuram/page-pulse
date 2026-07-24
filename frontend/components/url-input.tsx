import { ArrowRight } from "lucide-react";
import type { FormEventHandler } from "react";

interface UrlInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: FormEventHandler<HTMLFormElement>;
  isLoading: boolean;
  error?: string;
}

export function UrlInput({ value, onChange, onSubmit, isLoading, error }: UrlInputProps) {
  const errorId = "url-input-error";

  return (
    <form className="mx-auto mt-8 w-full max-w-3xl" onSubmit={onSubmit} noValidate>
      <label className="mb-2 block text-sm font-semibold text-slate-700" htmlFor="audit-url">
        Website URL
      </label>
      <div className="flex flex-col gap-3 rounded-2xl border border-slate-200 bg-white p-2 shadow-panel sm:flex-row">
        <input
          id="audit-url"
          name="url"
          type="url"
          inputMode="url"
          autoComplete="url"
          placeholder="example.com"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          aria-invalid={Boolean(error)}
          aria-describedby={error ? errorId : undefined}
          disabled={isLoading}
          className="min-h-12 flex-1 rounded-xl border border-transparent bg-transparent px-4 text-base text-slate-950 outline-none placeholder:text-slate-400 focus:border-blue-500 focus:ring-4 focus:ring-blue-100 disabled:cursor-not-allowed disabled:opacity-70"
        />
        <button
          type="submit"
          disabled={isLoading}
          className="inline-flex min-h-12 items-center justify-center gap-2 rounded-xl bg-blue-700 px-5 text-sm font-semibold text-white transition-colors hover:bg-blue-800 focus:outline-none focus:ring-4 focus:ring-blue-200 disabled:cursor-not-allowed disabled:bg-blue-400"
        >
          {isLoading ? "Auditing…" : "Audit page"}
          {!isLoading && <ArrowRight aria-hidden="true" className="size-4" />}
        </button>
      </div>
      {error && (
        <p id={errorId} className="mt-2 text-sm font-medium text-rose-700" role="alert">
          {error}
        </p>
      )}
    </form>
  );
}
