import { CircleAlert } from "lucide-react";

interface ErrorAlertProps {
  message: string;
}

export function ErrorAlert({ message }: ErrorAlertProps) {
  return (
    <div className="flex gap-3 rounded-2xl border border-rose-200 bg-rose-50 px-5 py-4" role="alert">
      <CircleAlert aria-hidden="true" className="mt-0.5 size-5 shrink-0 text-rose-700" />
      <div>
        <p className="font-semibold text-rose-950">We could not audit this URL</p>
        <p className="mt-1 text-sm leading-6 text-rose-800">{message}</p>
      </div>
    </div>
  );
}
