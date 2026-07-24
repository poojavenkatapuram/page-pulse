"use client";

import { type FormEvent, useState } from "react";

import { AuditResults } from "@/components/audit-results";
import { EmptyState } from "@/components/empty-state";
import { ErrorAlert } from "@/components/error-alert";
import { Footer } from "@/components/footer";
import { Hero } from "@/components/hero";
import { LoadingState } from "@/components/loading-state";
import { auditUrl, getApiErrorMessage } from "@/lib/api";
import type { AuditReport } from "@/types/audit";

export default function HomePage() {
  const [url, setUrl] = useState("");
  const [report, setReport] = useState<AuditReport | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [validationError, setValidationError] = useState<string>();
  const [requestError, setRequestError] = useState<string>();

  function handleUrlChange(nextUrl: string) {
    setUrl(nextUrl);
    if (validationError) {
      setValidationError(undefined);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedUrl = url.trim();

    if (!trimmedUrl) {
      setValidationError("Enter a URL to start an audit.");
      setRequestError(undefined);
      return;
    }

    setIsLoading(true);
    setValidationError(undefined);
    setRequestError(undefined);

    try {
      const auditReport = await auditUrl(trimmedUrl);
      setReport(auditReport);
    } catch (error) {
      setRequestError(getApiErrorMessage(error));
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen flex-col bg-slate-50">
      <main className="flex-1">
        <Hero
          url={url}
          onUrlChange={handleUrlChange}
          onSubmit={handleSubmit}
          isLoading={isLoading}
          validationError={validationError}
        />
        <section className="mx-auto w-full max-w-6xl px-5 py-10 sm:px-8 sm:py-14" aria-live="polite">
          {isLoading && <LoadingState />}
          {!isLoading && requestError && <ErrorAlert message={requestError} />}
          {!isLoading && !requestError && report && <AuditResults report={report} />}
          {!isLoading && !requestError && !report && <EmptyState />}
        </section>
      </main>
      <Footer />
    </div>
  );
}
