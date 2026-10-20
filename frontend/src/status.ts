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
    approved: "success",
    rejected: "error",
  },
  project: {
    upcoming: "info",
    active: "primary",
    won: "success",
    lost: "error",
    cancelled: "default",
    on_hold: "warning",
  },
  price: {
    not_requested: "default",
    pending: "warning",
    changes_requested: "warning",
    partially_approved: "info",
    approved: "success",
    rejected: "error",
    expired: "error",
  },
};

export function getStatusColor(kind: StatusKind, status: string | null) {
  return STATUS_COLORS[kind][status ?? ""] ?? "default";
}
