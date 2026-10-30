export function companyNextStep(status: string) {
  const messages: Record<string, string> = {
    submitted:
      "DBGI will review the registration and confirm the opportunity outcome.",
    under_review:
      "DBGI is reviewing the registration. No company action is needed now.",
    changes_requested:
      "Read the requested changes below, edit the registration, and submit it again.",
    resubmitted: "DBGI will review the corrected registration.",
    eligible_matched:
      "DBGI confirmed the opportunity match. Pricing review continues separately.",
    review_required:
      "DBGI must review the updated registration before the confirmed outcome continues.",
    rejected:
      "Review DBGI's explanation below. This registration will not proceed.",
    withdrawn:
      "You withdrew this registration. No further action is possible; register a new deal if the opportunity returns.",
  };
  return (
    messages[status] ??
    "Check the current status and activity for the next action."
  );
}
