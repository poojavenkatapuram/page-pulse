import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import HomePage from "@/app/page";
import { auditUrl, getApiErrorMessage } from "@/lib/api";

vi.mock("@/lib/api", () => ({
  auditUrl: vi.fn(),
  getApiErrorMessage: vi.fn(),
}));

const mockedAuditUrl = vi.mocked(auditUrl);
const mockedGetApiErrorMessage = vi.mocked(getApiErrorMessage);

const auditReport = {
  url: "https://example.com/",
  http_status: 200,
  response_time_ms: 241.8,
  title: "Example Domain",
  meta_description: "An example page",
  h1_count: 1,
  images_missing_alt_text: 2,
  approximate_word_count: 42,
};

describe("HomePage", () => {
  beforeEach(() => {
    mockedGetApiErrorMessage.mockReturnValue("The audit request failed.");
  });

  it("shows a validation error without calling the API for an empty URL", async () => {
    const user = userEvent.setup();
    render(<HomePage />);

    await user.click(screen.getByRole("button", { name: /audit page/i }));

    expect(screen.getByRole("alert")).toHaveTextContent("Enter a URL to start an audit.");
    expect(mockedAuditUrl).not.toHaveBeenCalled();
  });

  it("shows loading feedback and disables the button while an audit is pending", async () => {
    let resolveAudit!: (value: typeof auditReport) => void;
    mockedAuditUrl.mockReturnValue(
      new Promise((resolve) => {
        resolveAudit = resolve;
      }),
    );
    render(<HomePage />);

    await submitUrl("example.com");

    expect(screen.getByRole("status")).toHaveTextContent("Auditing your page");
    expect(screen.getByRole("button", { name: /auditing/i })).toBeDisabled();

    resolveAudit!(auditReport);
    expect(await screen.findByRole("heading", { name: /page report/i })).toBeInTheDocument();
  });

  it("renders the successful audit report and metric cards", async () => {
    mockedAuditUrl.mockResolvedValue(auditReport);
    render(<HomePage />);

    await submitUrl("example.com");

    expect(await screen.findByText("Example Domain")).toBeInTheDocument();
    expect(screen.getByText("An example page")).toBeInTheDocument();
    expect(screen.getByText("200")).toBeInTheDocument();
    expect(screen.getByText("242 ms")).toBeInTheDocument();
    expect(screen.getByText("42")).toBeInTheDocument();
    expect(screen.getByText("HTTP status")).toBeInTheDocument();
    expect(screen.getByText("Response time")).toBeInTheDocument();
    expect(screen.getByText("H1 count")).toBeInTheDocument();
    expect(screen.getByText("Missing alt images")).toBeInTheDocument();
    expect(screen.getByText("Word count")).toBeInTheDocument();
  });

  it("renders a readable API error", async () => {
    mockedAuditUrl.mockRejectedValue(new Error("Network failure"));
    render(<HomePage />);

    await submitUrl("example.com");

    expect(await screen.findByRole("alert")).toHaveTextContent("The audit request failed.");
    expect(mockedGetApiErrorMessage).toHaveBeenCalled();
  });

  it("exposes a labelled URL field and the required footer link", () => {
    render(<HomePage />);

    expect(screen.getByLabelText("Website URL")).toHaveAttribute("name", "url");
    expect(screen.getByRole("link", { name: "Built for Digital Heroes Training Task" })).toHaveAttribute(
      "href",
      "https://digitalheroesco.com",
    );
  });
});

async function submitUrl(url: string) {
  const input = screen.getByLabelText("Website URL");
  fireEvent.change(input, { target: { value: url } });
  await userEvent.click(screen.getByRole("button", { name: /audit page/i }));
  await waitFor(() => expect(mockedAuditUrl).toHaveBeenCalledWith(url));
}
