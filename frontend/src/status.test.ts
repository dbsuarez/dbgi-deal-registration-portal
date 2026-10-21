import { describe, expect, it } from "vitest";

import { getStatusExplanation } from "./status";

describe("getStatusExplanation", () => {
  it("explains the example registration statuses in plain language", () => {
    expect(getStatusExplanation("registration", "submitted")).toContain(
      "DBGI received",
    );
    expect(getStatusExplanation("project", null)).toContain(
      "not connected to a shared project opportunity",
    );
    expect(getStatusExplanation("price", "pending")).toContain(
      "has not made a final pricing decision",
    );
  });

  it("provides a safe fallback for a new status", () => {
    expect(getStatusExplanation("registration", "future_status")).toBe(
      "Open the Help page for more information about this status.",
    );
  });
});
