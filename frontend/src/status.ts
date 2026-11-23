import type { ChipProps } from "@mui/material";

export type StatusKind = "registration" | "project" | "price";

const STATUS_COLORS: Record<StatusKind, Record<string, ChipProps["color"]>> = {
  registration: {
    submitted: "info",
    under_review: "warning",
    changes_requested: "warning",
    resubmitted: "info",
    eligible_matched: "success",
    review_required: "warning",
    rejected: "error",
    closed: "default",
  },
  project: {
    upcoming: "info",
    active: "primary",
    won: "success",
    won_by_you: "success",
    awarded_to_other: "default",
    awarded: "default",
    lost: "error",
    cancelled: "default",
    on_hold: "warning",
  },
  price: {
    not_requested: "default",
    pending: "warning",
    changes_requested: "warning",
    partially_approved: "info",
    owner_review: "warning",
    approved: "success",
    rejected: "error",
    expired: "error",
  },
};

export function getStatusColor(kind: StatusKind, status: string | null) {
  return STATUS_COLORS[kind][status ?? ""] ?? "default";
}

const STATUS_EXPLANATIONS: Record<StatusKind, Record<string, string>> = {
  registration: {
    submitted:
      "DBGI received this registration. It is waiting for matching or administrator review.",
    under_review: "A DBGI administrator is reviewing this registration.",
    changes_requested:
      "DBGI needs corrections. Open the latest decision, edit the requested information, and submit again.",
    resubmitted:
      "The requested corrections were submitted and are waiting for DBGI review.",
    eligible_matched:
      "DBGI confirmed that this registration belongs to a specific project opportunity.",
    review_required:
      "This registration changed after matching and must be reviewed again by DBGI.",
    rejected:
      "DBGI rejected this registration. Open the decision to read the reason.",
    closed:
      "This deal is cancelled. It left the ranking and cannot change. Only DBGI can reopen it.",
  },
  project: {
    unlinked:
      "This registration is not connected to a shared project opportunity yet. DBGI will review and link it when appropriate.",
    upcoming: "The linked project is expected but has not started yet.",
    active: "The linked project is currently active.",
    won: "The linked project was recorded as won.",
    won_by_you: "DBGI confirmed that your company won this project.",
    awarded_to_other:
      "The project was awarded to another company. Your deal stays on record.",
    awarded:
      "The project was awarded. DBGI has not recorded which company won it.",
    lost: "The linked project was recorded as lost.",
    cancelled: "The linked project was cancelled.",
    on_hold: "Work on the linked project is temporarily on hold.",
  },
  price: {
    not_requested: "No DBGI pricing review is required for this registration.",
    pending:
      "DBGI has not made a final pricing decision for every requested product category.",
    changes_requested:
      "DBGI needs a new price from the company. The company edits the deal, changes the price, and saves.",
    partially_approved:
      "DBGI approved pricing for some requested items or categories, but not all of them.",
    owner_review:
      "The discount is above the admin limit, so the owner decides it. The partner sees it as pending.",
    approved:
      "DBGI approved the displayed prices until the stated validity date.",
    rejected: "DBGI did not approve the requested pricing.",
    expired: "The previously approved pricing is no longer valid.",
  },
};

export function getStatusExplanation(kind: StatusKind, status: string | null) {
  const key =
    kind === "project" && status === null ? "unlinked" : (status ?? "");
  return (
    STATUS_EXPLANATIONS[kind][key] ??
    "Open the Help page for more information about this status."
  );
}
