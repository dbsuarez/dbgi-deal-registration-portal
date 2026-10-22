import { describe, expect, it } from "vitest";

import { companyNextStep } from "./registrationReview";

describe("companyNextStep", () => {
  it("gives company users a simple next step without matching internals", () => {
    expect(companyNextStep("under_review")).toBe(
      "DBGI is reviewing the registration. No company action is needed now.",
    );
    expect(companyNextStep("eligible_matched")).toBe(
      "DBGI confirmed the opportunity match. Pricing review continues separately.",
    );
    expect(companyNextStep("changes_requested")).toContain(
      "edit the registration",
    );
  });
});
