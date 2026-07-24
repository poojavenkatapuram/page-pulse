import { Activity } from "lucide-react";
import type { FormEventHandler } from "react";

import { UrlInput } from "@/components/url-input";

interface HeroProps {
  url: string;
  onUrlChange: (url: string) => void;
  onSubmit: FormEventHandler<HTMLFormElement>;
  isLoading: boolean;
  validationError?: string;
}

export function Hero({ url, onUrlChange, onSubmit, isLoading, validationError }: HeroProps) {
  return (
    <section className="border-b border-slate-200 bg-white px-5 pb-14 pt-12 sm:px-8 sm:pb-20 sm:pt-16">
      <div className="mx-auto max-w-6xl text-center">
        <div className="inline-flex items-center gap-2 rounded-full border border-blue-100 bg-blue-50 px-3 py-1.5 text-sm font-semibold text-blue-800">
          <Activity aria-hidden="true" className="size-4" />
          Page health, at a glance
        </div>
        <h1 className="mt-6 text-4xl font-bold tracking-tight text-slate-950 sm:text-5xl lg:text-6xl">Page Pulse</h1>
        <p className="mx-auto mt-5 max-w-2xl text-base leading-7 text-slate-600 sm:text-lg">
          Audit the essential on-page signals for any public URL in seconds, from structure and metadata to accessibility basics.
        </p>
        <UrlInput
          value={url}
          onChange={onUrlChange}
          onSubmit={onSubmit}
          isLoading={isLoading}
          error={validationError}
        />
        <p className="mt-3 text-sm text-slate-500">Enter a domain or full URL. We will safely add https:// when needed.</p>
      </div>
    </section>
  );
}
