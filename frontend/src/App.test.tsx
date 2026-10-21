import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import App from "./App";

const session = {
  username: "dealer-a",
  display_name: "Dealer A",
  is_dbgi_admin: false,
  csrf_token: "test-token",
};

beforeEach(() => {
  window.history.pushState({}, "", "/");
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("App", () => {
  it("renders the registration list returned by the API", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValueOnce(
          new Response(JSON.stringify(session), { status: 200 }),
        )
        .mockResolvedValueOnce(
          new Response(
            JSON.stringify({
              items: [
                {
                  id: 1,
                  reference: "DBGI-000001",
                  project_title: "Municipal printer project",
                  company_name: "North Dealer",
                  end_user_name: "Sample municipality",
                  status: "submitted",
                  status_label: "Submitted",
                  needs_review: false,
                  created_at: "2026-10-19T01:00:00Z",
                  version: 1,
                },
              ],
              total: 1,
              page: 1,
              page_size: 25,
            }),
            { status: 200 },
          ),
        ),
    );

    render(<App />);

    expect(
      await screen.findByText(
        "Municipal printer project",
        {},
        { timeout: 5000 },
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("DBGI-000001")).toBeInTheDocument();
    expect(
      screen.getByText(/^Build: \d{4}-\d{2}-\d{2} \d{2}:\d{2}$/),
    ).toBeInTheDocument();
  });

  it("renders a useful page for an unknown route", async () => {
    window.history.pushState({}, "", "/missing-page/");
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify(session), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      ),
    );

    render(<App />);

    expect(
      await screen.findByRole("heading", { name: "Page not found" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Go to registrations" }),
    ).toHaveAttribute("href", "/");
  });

  it("renders the current user's notification inbox", async () => {
    window.history.pushState({}, "", "/notifications/");
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValueOnce(
          new Response(JSON.stringify(session), { status: 200 }),
        )
        .mockResolvedValueOnce(
          new Response(
            JSON.stringify({
              items: [
                {
                  id: 7,
                  registration_id: 1,
                  registration_reference: "DBGI-000001",
                  event_type: "submission_confirmed",
                  event_type_label: "Submission confirmed",
                  title: "Submission confirmed",
                  message: "DBGI-000001 was submitted successfully.",
                  is_read: false,
                  created_at: "2026-10-21T07:00:00Z",
                },
              ],
              total: 1,
              unread_count: 1,
              page: 1,
              page_size: 25,
            }),
            { status: 200 },
          ),
        ),
    );

    render(<App />);

    expect(
      await screen.findByRole("heading", { name: "Notifications" }),
    ).toBeInTheDocument();
    expect(screen.getByText("DBGI-000001")).toBeInTheDocument();
    expect(screen.getByText("Unread")).toBeInTheDocument();
  });

  it("explains the post-submission procedure on the help page", async () => {
    window.history.pushState({}, "", "/help/");
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify(session), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      ),
    );

    render(<App />);

    expect(
      await screen.findByRole("heading", {
        name: "Help and user guide",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Create your first registration"),
    ).toBeInTheDocument();
    expect(screen.getByText("Choose the End-user")).toBeInTheDocument();
    expect(screen.getByText("Submission confirmed")).toBeInTheDocument();
    expect(screen.getByText("Registration decision")).toBeInTheDocument();
    expect(screen.getByText("Price request decision")).toBeInTheDocument();
    expect(screen.getByText("If something goes wrong")).toBeInTheDocument();
  });

  it("shows operational guidance to DBGI administrators", async () => {
    window.history.pushState({}, "", "/help/");
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            ...session,
            is_dbgi_admin: true,
            display_name: "DBGI Admin",
          }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" },
          },
        ),
      ),
    );

    render(<App />);

    expect(
      await screen.findByRole("heading", { name: "Help and user guide" }),
    ).toBeInTheDocument();
    expect(screen.getByText("DBGI administrator workflow")).toBeInTheDocument();
    expect(
      screen.getByText("Administrator daily checklist"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("How to make a pricing decision"),
    ).toBeInTheDocument();
    expect(
      screen.queryByText("Create your first registration"),
    ).not.toBeInTheDocument();
  });
});
