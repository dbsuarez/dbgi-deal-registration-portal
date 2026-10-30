import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import EditIcon from "@mui/icons-material/Edit";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import {
  Alert,
  Box,
  Breadcrumbs,
  Button,
  Chip,
  CircularProgress,
  Container,
  Divider,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  FormControlLabel,
  FormLabel,
  Grid,
  IconButton,
  Link,
  List,
  ListItem,
  ListItemText,
  MenuItem,
  Paper,
  Radio,
  RadioGroup,
  Snackbar,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import {
  getOpportunityScopes,
  getRegistration,
  refreshMatchingSuggestion,
  reviewRegistration,
  withdrawRegistration,
  type OpportunityScope,
  type RegistrationDetail,
} from "../api";
import { useSession } from "../session";
import { getStatusColor, getStatusExplanation } from "../status";
import { companyNextStep } from "./registrationReview";

const moneyCell = {
  textAlign: "right" as const,
  fontVariantNumeric: "tabular-nums",
};

function formatEventTimestamp(value: string) {
  return new Date(value).toLocaleString("sv-SE", {
    timeZone: "Asia/Manila",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function Detail({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <Box>
      <Typography variant="caption" color="text.secondary">
        {label}
      </Typography>
      <Typography>{children || "Not provided"}</Typography>
    </Box>
  );
}

export default function RegistrationDetailPage() {
  const session = useSession();
  const { id } = useParams();
  const navigate = useNavigate();
  const [registration, setRegistration] = useState<RegistrationDetail | null>(
    null,
  );
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);
  const [scopes, setScopes] = useState<OpportunityScope[]>([]);
  const [scopeId, setScopeId] = useState("");
  const [finalDecision, setFinalDecision] = useState<
    "link_existing" | "create_new" | "request_changes" | "reject"
  >("link_existing");
  const [rationale, setRationale] = useState("");
  const [reviewing, setReviewing] = useState(false);
  const [refreshingSuggestion, setRefreshingSuggestion] = useState(false);
  const [suggestionError, setSuggestionError] = useState("");
  const [explanationOpen, setExplanationOpen] = useState(false);
  const [matchingGuideOpen, setMatchingGuideOpen] = useState(false);
  const [withdrawOpen, setWithdrawOpen] = useState(false);
  const [withdrawReason, setWithdrawReason] = useState("");
  const [withdrawing, setWithdrawing] = useState(false);
  const [withdrawError, setWithdrawError] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    getRegistration(Number(id), controller.signal)
      .then((result) => {
        setRegistration(result);
        if (result.matching_suggestion?.candidate_scope_id)
          setScopeId(String(result.matching_suggestion.candidate_scope_id));
      })
      .catch((reason: Error) => {
        if (reason.name !== "AbortError") setError(reason.message);
      });
    return () => controller.abort();
  }, [id]);

  useEffect(() => {
    if (!session.is_dbgi_admin || registration?.status !== "under_review")
      return;
    const controller = new AbortController();
    getOpportunityScopes(controller.signal)
      .then(setScopes)
      .catch(() => undefined);
    return () => controller.abort();
  }, [registration?.status, session.is_dbgi_admin]);

  const submitReview = async (
    decision: "start_review" | "request_changes" | "confirm_match" | "reject",
  ) => {
    if (!registration || rationale.trim().length < 5) {
      setError("Enter a review reason of at least five characters.");
      return;
    }
    setReviewing(true);
    setError("");
    try {
      const updated = await reviewRegistration(
        registration.id,
        {
          version: registration.version,
          decision,
          rationale: rationale.trim(),
          opportunity_scope_id: scopeId ? Number(scopeId) : null,
          create_new_opportunity: finalDecision === "create_new",
        },
        session.csrf_token,
      );
      setRegistration(updated);
      setRationale("");
    } catch (reason) {
      setError(
        reason instanceof Error ? reason.message : "The review action failed.",
      );
    } finally {
      setReviewing(false);
    }
  };

  const handleWithdraw = async () => {
    if (!registration) return;
    setWithdrawing(true);
    setWithdrawError("");
    try {
      const updated = await withdrawRegistration(
        registration.id,
        { version: registration.version, reason: withdrawReason.trim() },
        session.csrf_token,
      );
      setRegistration(updated);
      setWithdrawOpen(false);
    } catch (reason) {
      setWithdrawError(
        reason instanceof Error ? reason.message : "The withdrawal failed.",
      );
    } finally {
      setWithdrawing(false);
    }
  };

  if (error)
    return (
      <Container sx={{ py: 4 }}>
        <Alert severity="error">{error}</Alert>
      </Container>
    );

  if (!registration)
    return (
      <Box sx={{ display: "grid", minHeight: 400, placeItems: "center" }}>
        <CircularProgress />
      </Box>
    );

  const isPendingReview = [
    "submitted",
    "resubmitted",
    "review_required",
  ].includes(registration.status);
  const isUnderReview = registration.status === "under_review";
  // Events are newest first; the latest match decision says who matched it.
  const latestMatchEvent = registration.events.find((event) =>
    ["Automatically matched", "Confirm eligible match"].includes(
      event.event_type,
    ),
  );
  const isAutomaticallyMatched =
    registration.status === "eligible_matched" &&
    latestMatchEvent?.event_type === "Automatically matched";
  const finalDecisionAction = {
    link_existing: "Link existing opportunity",
    create_new: "Create and link new opportunity",
    request_changes: "Request changes",
    reject: "Reject registration",
  }[finalDecision];

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Breadcrumbs aria-label="Breadcrumb" sx={{ mb: 2 }}>
        <Link href="/">Registrations</Link>
        <Typography color="text.primary">{registration.reference}</Typography>
      </Breadcrumbs>
      <Stack
        direction={{ xs: "column", sm: "row" }}
        spacing={2}
        alignItems="flex-start"
        sx={{ mb: 3 }}
      >
        <Box sx={{ flexGrow: 1 }}>
          <Stack direction="row" spacing={1} alignItems="center">
            <Typography variant="overline">{registration.reference}</Typography>
            <IconButton
              size="small"
              aria-label="Copy registration reference"
              onClick={() =>
                navigator.clipboard
                  .writeText(registration.reference)
                  .then(() => setCopied(true))
              }
            >
              <ContentCopyIcon fontSize="inherit" />
            </IconButton>
            <Tooltip
              arrow
              enterDelay={300}
              title={getStatusExplanation("registration", registration.status)}
            >
              <Chip
                tabIndex={0}
                size="small"
                label={registration.status_label}
                variant="filled"
                color={getStatusColor("registration", registration.status)}
              />
            </Tooltip>
            <Tooltip
              arrow
              enterDelay={300}
              title={getStatusExplanation(
                "project",
                registration.project_status,
              )}
            >
              <Chip
                tabIndex={0}
                size="small"
                label={`Project: ${registration.project_status_label}`}
                variant="filled"
                color={getStatusColor("project", registration.project_status)}
              />
            </Tooltip>
            <Tooltip
              arrow
              enterDelay={300}
              title={getStatusExplanation("price", registration.price_status)}
            >
              <Chip
                tabIndex={0}
                size="small"
                label={`Pricing: ${registration.price_status_label}`}
                variant="filled"
                color={getStatusColor("price", registration.price_status)}
              />
            </Tooltip>
            {registration.needs_review && (
              <Tooltip
                arrow
                enterDelay={300}
                title="The system could not safely finish matching, or important information changed. A DBGI administrator must review this registration."
              >
                <Chip
                  tabIndex={0}
                  size="small"
                  label="Review required"
                  color="warning"
                />
              </Tooltip>
            )}
          </Stack>
          <Typography variant="h1">{registration.project_title}</Typography>
        </Box>
        <Stack direction="row" spacing={1}>
          {registration.can_withdraw && (
            <Button
              variant="outlined"
              color="error"
              onClick={() => {
                setWithdrawReason("");
                setWithdrawError("");
                setWithdrawOpen(true);
              }}
            >
              Withdraw registration
            </Button>
          )}
          {registration.can_edit && (
            <Button
              variant="contained"
              startIcon={<EditIcon />}
              onClick={() => navigate("edit/")}
            >
              Edit registration
            </Button>
          )}
        </Stack>
      </Stack>

      {!session.is_dbgi_admin && (
        <Paper sx={{ mb: 3, p: 2 }}>
          <Typography variant="h2" sx={{ mb: 0.5 }}>
            What happens next?
          </Typography>
          <Typography>{companyNextStep(registration.status)}</Typography>
          {registration.status === "eligible_matched" &&
            registration.opportunity_scope_label && (
              <Typography sx={{ mt: 1 }}>
                Confirmed opportunity: {registration.opportunity_scope_label}
              </Typography>
            )}
        </Paper>
      )}

      {session.is_dbgi_admin && (
        <Paper sx={{ mb: 3, p: 3 }}>
          {isAutomaticallyMatched && (
            <Alert severity="success" sx={{ mb: 2 }}>
              Automatically matched. The system found one exact normalized
              end-user and address match with complete product overlap and no
              conflicts. No administrator action is required.
            </Alert>
          )}
          <Stack
            direction={{ xs: "column", md: "row" }}
            spacing={2}
            justifyContent="space-between"
          >
            <Box>
              <Stack direction="row" spacing={1} alignItems="center">
                <Typography variant="h2">DBGI review</Typography>
                <IconButton
                  aria-label="Explain matching suggestion"
                  onClick={() => setExplanationOpen(true)}
                >
                  <InfoOutlinedIcon />
                </IconButton>
              </Stack>
              <Typography variant="subtitle2" sx={{ mt: 1 }}>
                System recommendation
              </Typography>
              {registration.matching_suggestion ? (
                <>
                  <Typography>
                    {registration.matching_suggestion.outcome_label}
                  </Typography>
                  <Chip
                    size="small"
                    label={`Match score: ${registration.matching_suggestion.score}%`}
                    color={
                      registration.matching_suggestion.confidence === "high"
                        ? "success"
                        : "default"
                    }
                    sx={{ mt: 1 }}
                  />
                  {registration.matching_suggestion.score === 0 && (
                    <Typography variant="body2" sx={{ mt: 1 }}>
                      No likely existing opportunity was found.
                    </Typography>
                  )}
                  {registration.matching_suggestion.candidate_scope_label && (
                    <Typography variant="body2" sx={{ mt: 1 }}>
                      Suggested opportunity scope:{" "}
                      {registration.matching_suggestion.candidate_scope_label}
                    </Typography>
                  )}
                </>
              ) : (
                <Typography color="text.secondary">
                  No matching suggestion is available.
                </Typography>
              )}
            </Box>
            <Stack spacing={1} alignItems={{ xs: "stretch", md: "flex-end" }}>
              <Button
                variant="outlined"
                onClick={() => setMatchingGuideOpen(true)}
              >
                How matching review works
              </Button>
              <Button
                variant="text"
                disabled={reviewing || refreshingSuggestion}
                onClick={async () => {
                  if (!registration || refreshingSuggestion) return;
                  setRefreshingSuggestion(true);
                  setSuggestionError("");
                  try {
                    const suggestion = await refreshMatchingSuggestion(
                      registration.id,
                      session.csrf_token,
                    );
                    const updated = await getRegistration(registration.id);
                    setRegistration(updated);
                    if (suggestion.candidate_scope_id)
                      setScopeId(String(suggestion.candidate_scope_id));
                  } catch (reason) {
                    setSuggestionError(
                      reason instanceof Error
                        ? reason.message
                        : "The suggestion could not be refreshed.",
                    );
                  } finally {
                    setRefreshingSuggestion(false);
                  }
                }}
              >
                {refreshingSuggestion ? "Refreshing..." : "Refresh suggestion"}
              </Button>
            </Stack>
          </Stack>

          {suggestionError && (
            <Alert severity="error" sx={{ mt: 1 }}>
              {suggestionError}
            </Alert>
          )}

          {isPendingReview && (
            <Box sx={{ mt: 2 }}>
              <Typography fontWeight={600}>What should I do?</Typography>
              <Typography color="text.secondary" sx={{ mb: 2 }}>
                Review the system guidance and registration evidence, enter why
                you are starting review, then select Start review. This step
                does not link or create an opportunity.
              </Typography>
              <TextField
                fullWidth
                multiline
                required
                minRows={2}
                label="Review reason"
                value={rationale}
                onChange={(event) => setRationale(event.target.value)}
                helperText="Required for the audit history."
              />
              <Button
                variant="contained"
                disabled={reviewing}
                sx={{ mt: 2 }}
                onClick={() => submitReview("start_review")}
              >
                Start review
              </Button>
            </Box>
          )}

          {isUnderReview && (
            <Box sx={{ mt: 2 }}>
              <Typography fontWeight={600}>What should I do?</Typography>
              <Typography color="text.secondary" sx={{ mb: 2 }}>
                Make the final administrator decision. Select one option, then
                complete only the information required for that outcome.
              </Typography>
              <FormControl fullWidth>
                <FormLabel>Administrator decision</FormLabel>
                <RadioGroup
                  value={finalDecision}
                  onChange={(event) =>
                    setFinalDecision(event.target.value as typeof finalDecision)
                  }
                  sx={{ display: "grid", gap: 1, mt: 1 }}
                >
                  {[
                    [
                      "link_existing",
                      "Link to an existing opportunity",
                      "Choose the existing opportunity scope that this registration belongs to.",
                    ],
                    [
                      "create_new",
                      "Create a new whole opportunity",
                      "Create and link a new Whole opportunity scope from this registration.",
                    ],
                    [
                      "request_changes",
                      "Request changes",
                      "Send exact correction instructions to the company.",
                    ],
                    [
                      "reject",
                      "Reject registration",
                      "Reject this registration with a clear explanation.",
                    ],
                  ].map(([value, label, description]) => (
                    <FormControlLabel
                      key={value}
                      value={value}
                      control={<Radio />}
                      label={
                        <Box>
                          <Typography fontWeight={600}>{label}</Typography>
                          <Typography variant="body2" color="text.secondary">
                            {description}
                          </Typography>
                        </Box>
                      }
                      sx={{
                        alignItems: "flex-start",
                        border: 1,
                        borderColor:
                          finalDecision === value ? "primary.main" : "divider",
                        borderRadius: 1,
                        m: 0,
                        p: 1,
                      }}
                    />
                  ))}
                </RadioGroup>
              </FormControl>

              {finalDecision === "link_existing" && (
                <TextField
                  select
                  required
                  fullWidth
                  label="Opportunity scope"
                  value={scopeId}
                  onChange={(event) => setScopeId(event.target.value)}
                  sx={{ mt: 2 }}
                >
                  <MenuItem value="">Choose a scope</MenuItem>
                  {scopes.map((scope) => (
                    <MenuItem key={scope.id} value={scope.id}>
                      {scope.label}
                    </MenuItem>
                  ))}
                </TextField>
              )}

              <TextField
                fullWidth
                multiline
                required
                minRows={2}
                label={
                  finalDecision === "request_changes"
                    ? "Instructions for company"
                    : finalDecision === "reject"
                      ? "Rejection explanation"
                      : "Decision reason"
                }
                value={rationale}
                onChange={(event) => setRationale(event.target.value)}
                helperText="Required for the audit history."
                sx={{ mt: 2 }}
              />
              <Button
                variant="contained"
                color={finalDecision === "reject" ? "error" : "primary"}
                disabled={
                  reviewing ||
                  (finalDecision === "link_existing" && scopeId === "")
                }
                sx={{ mt: 2 }}
                onClick={() =>
                  submitReview(
                    finalDecision === "request_changes"
                      ? "request_changes"
                      : finalDecision === "reject"
                        ? "reject"
                        : "confirm_match",
                  )
                }
              >
                {finalDecisionAction}
              </Button>
            </Box>
          )}
        </Paper>
      )}

      <Grid container spacing={3}>
        <Grid size={{ xs: 12, md: 7 }}>
          <Paper sx={{ p: 3, height: "100%" }}>
            <Typography variant="h2" gutterBottom>
              Opportunity and contact
            </Typography>
            <Grid container spacing={2}>
              <Grid size={{ xs: 12, sm: 6 }}>
                <Detail label="Partner">{registration.company_name}</Detail>
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <Detail label="End-user">{registration.end_user_name}</Detail>
              </Grid>
              <Grid size={12}>
                <Detail label="Address">{registration.end_user_address}</Detail>
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <Detail label="Bid date">{registration.bid_date}</Detail>
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <Detail label="Delivery date">
                  {registration.delivery_date}
                </Detail>
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <Detail label="Contact">{registration.contact_person}</Detail>
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <Detail label="Designation">
                  {registration.contact_designation}
                </Detail>
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <Detail label="Email">{registration.contact_email}</Detail>
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <Detail label="Phone">{registration.contact_number}</Detail>
              </Grid>
            </Grid>
          </Paper>
        </Grid>
        <Grid size={{ xs: 12, md: 5 }}>
          <Paper sx={{ p: 3, height: "100%" }}>
            <Typography variant="h2" gutterBottom>
              Evidence
            </Typography>
            <Typography sx={{ whiteSpace: "pre-wrap" }}>
              {registration.evidence_description}
            </Typography>
            {registration.evidence_url && (
              <Link
                href={registration.evidence_url}
                target="_blank"
                rel="noopener noreferrer"
              >
                Open evidence link
              </Link>
            )}
            <Divider sx={{ my: 2 }} />
            <List disablePadding>
              {registration.attachments.map((attachment) => (
                <ListItem key={attachment.id} disableGutters>
                  <ListItemText
                    primary={
                      <Link href={attachment.download_url}>
                        {attachment.original_name}
                      </Link>
                    }
                    secondary={attachment.description || "No description"}
                  />
                </ListItem>
              ))}
              {!registration.attachments.length && (
                <Typography color="text.secondary">
                  No files attached.
                </Typography>
              )}
            </List>
          </Paper>
        </Grid>
      </Grid>

      <Paper sx={{ mt: 3, p: 3 }}>
        <Typography variant="h2" gutterBottom>
          Competitor items
        </Typography>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Brand</TableCell>
                <TableCell>Item / model</TableCell>
                <TableCell sx={moneyCell}>Bid price</TableCell>
                <TableCell>Remarks</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {registration.competitor_items.map((item) => (
                <TableRow key={item.id}>
                  <TableCell>{item.brand}</TableCell>
                  <TableCell>{item.item_name}</TableCell>
                  <TableCell sx={moneyCell}>
                    {Number(item.bid_price).toLocaleString("en-PH", {
                      minimumFractionDigits: 2,
                    })}
                  </TableCell>
                  <TableCell>{item.remarks || "Not provided"}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      <Paper sx={{ mt: 3, p: 3 }}>
        <Typography variant="h2" gutterBottom>
          Commercial approvals
        </Typography>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Product category</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Valid until</TableCell>
                <TableCell>Reviewer</TableCell>
                <TableCell>Reason</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {(registration.category_approvals ?? []).map((approval) => (
                <TableRow key={approval.id}>
                  <TableCell>{approval.category}</TableCell>
                  <TableCell>
                    <Chip
                      size="small"
                      label={approval.status_label}
                      variant="filled"
                      color={getStatusColor("price", approval.status)}
                    />
                  </TableCell>
                  <TableCell>{approval.valid_until ?? "Not set"}</TableCell>
                  <TableCell>
                    {approval.reviewed_by ?? "Not reviewed"}
                  </TableCell>
                  <TableCell>{approval.rationale || "Not provided"}</TableCell>
                </TableRow>
              ))}
              {!(registration.category_approvals ?? []).length && (
                <TableRow>
                  <TableCell colSpan={5}>
                    No catalog category requires pricing review.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      <Paper sx={{ mt: 3, p: 3 }}>
        <Typography variant="h2" gutterBottom>
          Requested products
        </Typography>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Product</TableCell>
                <TableCell sx={moneyCell}>Quantity</TableCell>
                <TableCell sx={moneyCell}>List unit price</TableCell>
                <TableCell sx={moneyCell}>Requested unit price</TableCell>
                <TableCell sx={moneyCell}>Requested discount</TableCell>
                <TableCell sx={moneyCell}>Requested total</TableCell>
                <TableCell sx={moneyCell}>Approved unit price</TableCell>
                <TableCell>Justification</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {registration.items.map((item) => (
                <TableRow key={item.id}>
                  <TableCell>{item.display_name}</TableCell>
                  <TableCell sx={moneyCell}>
                    {item.quantity.toLocaleString("en-PH")}
                  </TableCell>
                  <TableCell sx={moneyCell}>
                    {Number(item.list_unit_price ?? 0).toLocaleString("en-PH", {
                      minimumFractionDigits: 2,
                    })}
                  </TableCell>
                  <TableCell sx={moneyCell}>
                    {Number(item.requested_unit_price).toLocaleString("en-PH", {
                      minimumFractionDigits: 2,
                    })}
                  </TableCell>
                  <TableCell sx={moneyCell}>
                    {item.requested_discount_percent == null
                      ? "Not available"
                      : `${Number(item.requested_discount_percent).toLocaleString("en-PH", { minimumFractionDigits: 2 })}%`}
                  </TableCell>
                  <TableCell sx={moneyCell}>
                    {Number(item.requested_total ?? 0).toLocaleString("en-PH", {
                      minimumFractionDigits: 2,
                    })}
                  </TableCell>
                  <TableCell sx={moneyCell}>
                    {item.approved_unit_price == null
                      ? "Pending"
                      : Number(item.approved_unit_price).toLocaleString(
                          "en-PH",
                          {
                            minimumFractionDigits: 2,
                          },
                        )}
                  </TableCell>
                  <TableCell>{item.justification || "Not provided"}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          Requested prices are proposals, not approved prices.
        </Typography>
      </Paper>

      <Paper sx={{ mt: 3, p: 2 }}>
        <Typography variant="h2" gutterBottom>
          Activity
        </Typography>
        <List disablePadding>
          {registration.events.map((event) => (
            <ListItem key={event.id} divider sx={{ px: 0, py: 1 }}>
              <Box sx={{ width: "100%" }}>
                <Stack
                  direction={{ xs: "column", sm: "row" }}
                  spacing={{ xs: 0, sm: 1 }}
                  alignItems={{ xs: "flex-start", sm: "baseline" }}
                >
                  <Typography variant="body1" fontWeight={700}>
                    {event.event_type}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {event.actor_name} |{" "}
                    {formatEventTimestamp(event.created_at)}
                  </Typography>
                </Stack>
                {!!event.details && (
                  <Typography variant="body2" color="text.secondary">
                    {event.details}
                  </Typography>
                )}
                {!!event.changes.length && (
                  <Box
                    component="details"
                    sx={{
                      mt: 0.25,
                      "&[open] > summary": { mb: 0.75 },
                    }}
                  >
                    <Typography
                      component="summary"
                      variant="caption"
                      color="primary"
                      sx={{ cursor: "pointer", width: "fit-content" }}
                    >
                      View {event.changes.length}{" "}
                      {event.changes.length === 1 ? "change" : "changes"}
                    </Typography>
                    <Box
                      sx={{
                        bgcolor: "action.hover",
                        borderRadius: 1,
                        display: "grid",
                        gap: 0.5,
                        gridTemplateColumns: {
                          xs: "1fr",
                          md: "minmax(130px, 0.6fr) 1fr auto 1fr",
                        },
                        p: 1,
                      }}
                    >
                      {event.changes.map((change) => (
                        <Box key={change.label} sx={{ display: "contents" }}>
                          <Typography variant="caption" fontWeight={700}>
                            {change.label}
                          </Typography>
                          {change.previous ? (
                            <>
                              <Typography
                                variant="caption"
                                color="text.secondary"
                              >
                                {change.previous}
                              </Typography>
                              <Typography
                                variant="caption"
                                aria-hidden="true"
                                color="text.secondary"
                                sx={{ display: { xs: "none", md: "block" } }}
                              >
                                to
                              </Typography>
                              <Typography variant="caption">
                                {change.current}
                              </Typography>
                            </>
                          ) : (
                            <Typography
                              variant="caption"
                              sx={{ gridColumn: { md: "2 / 5" } }}
                            >
                              {change.current}
                            </Typography>
                          )}
                        </Box>
                      ))}
                    </Box>
                  </Box>
                )}
              </Box>
            </ListItem>
          ))}
        </List>
      </Paper>
      <Snackbar
        open={copied}
        autoHideDuration={2000}
        onClose={() => setCopied(false)}
        message="Reference copied"
      />
      <Dialog
        open={withdrawOpen}
        onClose={() => !withdrawing && setWithdrawOpen(false)}
        fullWidth
        maxWidth="sm"
      >
        <DialogTitle>Withdraw this registration?</DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            Withdrawal is final. The registration leaves the ranking, can no
            longer be edited, and cannot be restored. DBGI is notified.
          </Alert>
          {withdrawError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {withdrawError}
            </Alert>
          )}
          <TextField
            label="Reason for withdrawing"
            value={withdrawReason}
            onChange={(event) => setWithdrawReason(event.target.value)}
            helperText="DBGI sees this reason. At least 5 characters."
            multiline
            minRows={3}
            fullWidth
            required
            autoFocus
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setWithdrawOpen(false)} disabled={withdrawing}>
            Cancel
          </Button>
          <Button
            variant="contained"
            color="error"
            disabled={withdrawing || withdrawReason.trim().length < 5}
            onClick={handleWithdraw}
          >
            Withdraw registration
          </Button>
        </DialogActions>
      </Dialog>
      <Dialog
        open={matchingGuideOpen}
        onClose={() => setMatchingGuideOpen(false)}
        fullWidth
        maxWidth="sm"
      >
        <DialogTitle>How matching review works</DialogTitle>
        <DialogContent>
          <Typography fontWeight={600}>
            Start review -&gt; Decide opportunity match -&gt; Continue to
            pricing review
          </Typography>
          <List dense>
            <ListItem>
              Start review records that examination began. It does not link or
              create an opportunity.
            </ListItem>
            <ListItem>
              Decide opportunity match by linking an existing scope, creating a
              new whole opportunity, requesting changes, or rejecting the
              registration.
            </ListItem>
            <ListItem>
              Pricing review remains separate and begins only after the
              registration decision allows it.
            </ListItem>
          </List>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setMatchingGuideOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
      <Dialog
        open={explanationOpen}
        onClose={() => setExplanationOpen(false)}
        fullWidth
        maxWidth="sm"
        scroll="paper"
      >
        <DialogTitle>Why this match was suggested</DialogTitle>
        <DialogContent sx={{ overflowWrap: "anywhere" }}>
          <Typography paragraph>
            The application compares end-user names, addresses, and catalog
            product overlap. It provides guidance only. A DBGI administrator
            must confirm every matching decision.
          </Typography>
          <Typography component="h3" variant="subtitle1" fontWeight={600}>
            Supporting factors
          </Typography>
          {(registration.matching_suggestion?.supporting_factors ?? [])
            .length ? (
            <List dense>
              {registration.matching_suggestion?.supporting_factors.map(
                (factor) => (
                  <ListItem key={factor}>{factor}</ListItem>
                ),
              )}
            </List>
          ) : (
            <Typography color="text.secondary" sx={{ my: 1 }}>
              No supporting factors identified.
            </Typography>
          )}
          <Typography
            component="h3"
            variant="subtitle1"
            fontWeight={600}
            sx={{ mt: 2 }}
          >
            Conflicting factors
          </Typography>
          <List dense>
            {(registration.matching_suggestion?.conflicting_factors ?? []).map(
              (factor) => (
                <ListItem key={factor}>{factor}</ListItem>
              ),
            )}
          </List>
          <Typography variant="caption" color="text.secondary">
            Rule version:{" "}
            {registration.matching_suggestion?.rule_version ?? "Not available"}
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setExplanationOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}
