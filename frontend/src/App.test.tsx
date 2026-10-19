import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import App from "./App";

const session = {
  username: "dealer-a",
  display_name: "Dealer A",
  is_dbgi_admin: false,
  csrf_token: "test-token",
};

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
  });
});
