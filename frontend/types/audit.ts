export interface AuditReport {
  url: string;
  http_status: number;
  response_time_ms: number;
  title: string | null;
  meta_description: string | null;
  h1_count: number;
  images_missing_alt_text: number;
  approximate_word_count: number;
}

interface ApiErrorDetail {
  code: string;
  message: string;
}

export interface ApiErrorResponse {
  error: ApiErrorDetail;
}
