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
  FormControlLabel,
  Grid,
  IconButton,
  Link,
  List,
  ListItem,
  ListItemText,
  MenuItem,
  Paper,
  Checkbox,
  Snackbar,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import {
  getOpportunityScopes,
  getRegistration,
  refreshMatchingSuggestion,
  reviewRegistration,
  type OpportunityScope,
  type RegistrationDetail,
} from "../api";
import { useSession } from "../session";

const moneyCell = {
  textAlign: "right" as const,
  fontVariantNumeric: "tabular-nums",
};

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
  const [createNewOpportunity, setCreateNewOpportunity] = useState(false);
  const [rationale, setRationale] = useState("");
  const [reviewing, setReviewing] = useState(false);
  const [explanationOpen, setExplanationOpen] = useState(false);

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
    if (!session.is_dbgi_admin) return;
    const controller = new AbortController();
    getOpportunityScopes(controller.signal).then(setScopes).catch(() => undefined);
    return () => controller.abort();
  }, [session.is_dbgi_admin]);

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
          create_new_opportunity: createNewOpportunity,
        },
        session.csrf_token,
      );
      setRegistration(updated);
      setRationale("");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "The review action failed.");
    } finally {
      setReviewing(false);
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
            <Chip
              size="small"
              label={registration.status_label}
              variant="outlined"
            />
            {registration.needs_review && (
              <Chip size="small" label="Review required" color="warning" />
            )}
          </Stack>
          <Typography variant="h1">{registration.project_title}</Typography>
        </Box>
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

      {session.is_dbgi_admin && (
        <Paper sx={{ mb: 3, p: 3 }}>
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
              {registration.matching_suggestion ? (
                <>
                  <Typography>
                    Suggested action: {registration.matching_suggestion.outcome_label}
                  </Typography>
                  <Chip
                    size="small"
                    label={`${registration.matching_suggestion.confidence_label} confidence | ${registration.matching_suggestion.score}%`}
                    color={
                      registration.matching_suggestion.confidence === "high"
                        ? "success"
                        : "default"
                    }
                    sx={{ mt: 1 }}
                  />
                  {registration.matching_suggestion.candidate_scope_label && (
                    <Typography variant="body2" sx={{ mt: 1 }}>
                      Candidate: {registration.matching_suggestion.candidate_scope_label}
                    </Typography>
                  )}
                </>
              ) : (
                <Typography color="text.secondary">
                  No matching suggestion is available.
                </Typography>
              )}
            </Box>
            <Button
              variant="outlined"
              disabled={reviewing}
              onClick={async () => {
                if (!registration) return;
                const suggestion = await refreshMatchingSuggestion(
                  registration.id,
                  session.csrf_token,
                );
                setRegistration({ ...registration, matching_suggestion: suggestion });
                if (suggestion.candidate_scope_id)
                  setScopeId(String(suggestion.candidate_scope_id));
              }}
            >
              Refresh suggestion
            </Button>
          </Stack>

          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid size={{ xs: 12, md: 7 }}>
              <TextField
                fullWidth
                multiline
                required
                minRows={2}
                label="Decision reason"
                value={rationale}
                onChange={(event) => setRationale(event.target.value)}
                helperText="Required for the audit history."
              />
            </Grid>
            <Grid size={{ xs: 12, md: 5 }}>
              <TextField
                select
                fullWidth
                label="Opportunity scope"
                value={scopeId}
                disabled={createNewOpportunity}
                onChange={(event) => setScopeId(event.target.value)}
              >
                <MenuItem value="">Choose a scope</MenuItem>
                {scopes.map((scope) => (
                  <MenuItem key={scope.id} value={scope.id}>
                    {scope.label}
                  </MenuItem>
                ))}
              </TextField>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={createNewOpportunity}
                    onChange={(event) => setCreateNewOpportunity(event.target.checked)}
                  />
                }
                label="Create a new whole opportunity from this registration"
              />
            </Grid>
          </Grid>
          <Stack direction="row" spacing={1} flexWrap="wrap" sx={{ mt: 2 }}>
            {["submitted", "resubmitted", "review_required"].includes(
              registration.status,
            ) && (
              <Button
                variant="contained"
                disabled={reviewing}
                onClick={() => submitReview("start_review")}
              >
                Start review
              </Button>
            )}
            {registration.status === "under_review" && (
              <>
                <Button
                  variant="contained"
                  disabled={
                    reviewing || (!createNewOpportunity && scopeId === "")
                  }
                  onClick={() => submitReview("confirm_match")}
                >
                  Confirm eligible match
                </Button>
                <Button
                  variant="outlined"
                  disabled={reviewing}
                  onClick={() => submitReview("request_changes")}
                >
                  Request changes
                </Button>
                <Button
                  color="error"
                  disabled={reviewing}
                  onClick={() => submitReview("reject")}
                >
                  Reject
                </Button>
              </>
            )}
          </Stack>
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
                <Detail label="End user">{registration.end_user_name}</Detail>
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
          Requested products
        </Typography>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Product</TableCell>
                <TableCell sx={moneyCell}>Quantity</TableCell>
                <TableCell sx={moneyCell}>Requested unit price</TableCell>
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
                    {Number(item.requested_unit_price).toLocaleString("en-PH", {
                      minimumFractionDigits: 2,
                    })}
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

      <Paper sx={{ mt: 3, p: 3 }}>
        <Typography variant="h2" gutterBottom>
          Activity
        </Typography>
        <List>
          {registration.events.map((event) => (
            <ListItem key={event.id} divider>
              <ListItemText
                primary={event.event_type}
                secondary={`${event.actor_name} | ${new Date(event.created_at).toLocaleString("sv-SE", { timeZone: "Asia/Manila", year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" })} | ${event.details}`}
              />
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
      <Dialog open={explanationOpen} onClose={() => setExplanationOpen(false)}>
        <DialogTitle>Why this match was suggested</DialogTitle>
        <DialogContent>
          <Typography paragraph>
            The application compares end-user names, addresses, and catalog product
            overlap. It provides guidance only. A DBGI administrator must confirm every
            matching decision.
          </Typography>
          <Typography variant="h3">Supporting factors</Typography>
          <List dense>
            {(registration.matching_suggestion?.supporting_factors ?? []).map(
              (factor) => (
                <ListItem key={factor}>{factor}</ListItem>
              ),
            )}
          </List>
          <Typography variant="h3">Conflicting factors</Typography>
          <List dense>
            {(registration.matching_suggestion?.conflicting_factors ?? []).map(
              (factor) => (
                <ListItem key={factor}>{factor}</ListItem>
              ),
            )}
          </List>
          <Typography variant="caption" color="text.secondary">
            Rule version: {registration.matching_suggestion?.rule_version ?? "Not available"}
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setExplanationOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}
