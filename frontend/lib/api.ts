import axios from "axios";

import type { ApiErrorResponse, AuditReport } from "@/types/audit";

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000",
  timeout: 15_000,
  headers: { "Content-Type": "application/json" },
});

export async function auditUrl(url: string): Promise<AuditReport> {
  const response = await apiClient.post<AuditReport>("/api/v1/audits", { url });
  return response.data;
}

export function getApiErrorMessage(error: unknown): string {
  if (axios.isAxiosError<ApiErrorResponse>(error)) {
    return error.response?.data.error?.message ?? "We could not complete the audit. Please try again.";
  }

  return "Something unexpected happened. Please try again.";
}
