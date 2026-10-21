import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Alert,
  Box,
  Breadcrumbs,
  Button,
  Chip,
  Container,
  Grid,
  Link,
  List,
  ListItem,
  ListItemText,
  Paper,
  Stack,
  Typography,
} from "@mui/material";

import { useSession } from "../session";

const submissionSteps = [
  [
    "Submission confirmed",
    "The portal records the registration and notifies the active users in your company.",
  ],
  [
    "Registration decision",
    "DBGI reviews the registration and may confirm it, reject it, or request changes.",
  ],
  [
    "Price request decision",
    "DBGI reviews requested pricing separately for each product category.",
  ],
];

const registrationStatuses = [
  ["Submitted", "DBGI has received the registration."],
  ["Under review", "A DBGI administrator is reviewing it."],
  [
    "Changes requested",
    "Open the registration, read the reason, and select Edit.",
  ],
  ["Registered", "DBGI confirmed the registration and its opportunity match."],
  [
    "Review required after edit",
    "A confirmed registration changed and must be reviewed again.",
  ],
  ["Rejected", "Open the registration to review DBGI's reason."],
];

function NumberedStep({
  number,
  title,
  children,
}: {
  number: number;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <ListItem
      alignItems="flex-start"
      disableGutters
      sx={{ gap: 1.5, py: 0.75 }}
    >
      <Box
        aria-hidden="true"
        sx={{
          bgcolor: "primary.main",
          borderRadius: "50%",
          color: "primary.contrastText",
          display: "grid",
          flex: "0 0 28px",
          fontSize: 14,
          fontWeight: 700,
          height: 28,
          placeItems: "center",
        }}
      >
        {number}
      </Box>
      <ListItemText
        sx={{ my: 0 }}
        primary={title}
        secondary={children}
        slotProps={{ primary: { fontWeight: 700 } }}
      />
    </ListItem>
  );
}

function GuideSection({
  title,
  children,
  defaultExpanded = false,
}: {
  title: string;
  children: React.ReactNode;
  defaultExpanded?: boolean;
}) {
  return (
    <Accordion defaultExpanded={defaultExpanded} disableGutters>
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Typography fontWeight={700}>{title}</Typography>
      </AccordionSummary>
      <AccordionDetails>{children}</AccordionDetails>
    </Accordion>
  );
}

export default function HelpPage() {
  const session = useSession();

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Breadcrumbs aria-label="Breadcrumb" sx={{ mb: 2 }}>
        <Link href="/">Registrations</Link>
        <Typography color="text.primary">Help</Typography>
      </Breadcrumbs>
      <Typography variant="h1" gutterBottom>
        Help and user guide
      </Typography>
      <Typography color="text.secondary" sx={{ mb: 2 }}>
        Follow this guide from your first registration through DBGI review and
        pricing approval.
      </Typography>
      <Alert severity="info" sx={{ mb: 3 }}>
        You are signed in as {session.display_name}. This guide is showing the{" "}
        {session.is_dbgi_admin ? "DBGI administrator" : "company user"}{" "}
        workflow.
      </Alert>

      <Paper variant="outlined" sx={{ mb: 3, p: 2 }}>
        <Typography variant="h2" gutterBottom>
          Start here
        </Typography>
        <Stack
          direction={{ xs: "column", sm: "row" }}
          spacing={1}
          sx={{ mb: 1.5 }}
        >
          <Button variant="contained" href="/">
            View registrations
          </Button>
          {!session.is_dbgi_admin && (
            <Button variant="outlined" href="/registrations/new/">
              Create a registration
            </Button>
          )}
          <Button variant="outlined" href="/notifications/">
            Check notifications
          </Button>
        </Stack>
        <Typography variant="body2" color="text.secondary">
          A registration is your company's claim for a specific End-user
          procurement opportunity. Requested prices are proposals until DBGI
          approves them.
        </Typography>
      </Paper>

      {!session.is_dbgi_admin ? (
        <Stack spacing={1.5} sx={{ mb: 3 }}>
          <GuideSection title="Create your first registration" defaultExpanded>
            <List disablePadding>
              <NumberedStep number={1} title="Select Create a registration">
                Start from the Registrations page. Do not create a second record
                for the same opportunity just to correct information.
              </NumberedStep>
              <NumberedStep number={2} title="Choose the End-user">
                Search the shared directory. If the organization is missing, use
                Add missing End-user. Pending End-users cannot be automatically
                matched until DBGI verifies them.
              </NumberedStep>
              <NumberedStep
                number={3}
                title="Enter the project and contact details"
              >
                Add the project title, bid and delivery dates, and the person
                DBGI may contact about the opportunity.
              </NumberedStep>
              <NumberedStep number={4} title="Describe your evidence">
                Explain how you learned about the opportunity and confirm that
                you are authorized to share the information. Add supporting
                files when available.
              </NumberedStep>
              <NumberedStep number={5} title="Add competitor information">
                Add at least one competitor brand, item or model, bid price, and
                useful remarks. This is private to your company and DBGI.
              </NumberedStep>
              <NumberedStep
                number={6}
                title="Add requested products and prices"
              >
                Add at least one catalog or non-catalog product, quantity,
                requested unit price, and justification. A requested price is
                not an approved price.
              </NumberedStep>
              <NumberedStep number={7} title="Review and submit">
                Check the details carefully, then submit. The portal creates a
                reference such as DBGI-000123 and sends a notification.
              </NumberedStep>
            </List>
          </GuideSection>
          <GuideSection title="Track and respond to your registration">
            <List disablePadding>
              <NumberedStep number={1} title="Open Notifications">
                Portal notifications are the official record. Email provides a
                summary and links back to the portal.
              </NumberedStep>
              <NumberedStep number={2} title="Open the registration">
                The badges at the top separately show registration, project, and
                pricing status. They do not mean the same thing.
              </NumberedStep>
              <NumberedStep number={3} title="Respond to requested changes">
                Read DBGI's reason, select Edit, correct the requested fields,
                and submit again. Editing a confirmed record sends it back for
                review.
              </NumberedStep>
              <NumberedStep number={4} title="Review pricing decisions">
                Check the category pricing table and approved unit prices. Never
                treat the requested price as approved before a DBGI decision
                appears.
              </NumberedStep>
            </List>
          </GuideSection>
        </Stack>
      ) : (
        <Stack spacing={1.5} sx={{ mb: 3 }}>
          <GuideSection title="DBGI administrator workflow" defaultExpanded>
            <List disablePadding>
              <NumberedStep
                number={1}
                title="Open a registration that needs review"
              >
                Confirm the company, End-user, evidence, requested products,
                competitor information, and matching suggestion.
              </NumberedStep>
              <NumberedStep number={2} title="Start review">
                Starting review records the reviewer action without making a
                final decision.
              </NumberedStep>
              <NumberedStep number={3} title="Decide the registration">
                Confirm the match, request changes with a clear reason, or
                reject it. Company users are notified automatically.
              </NumberedStep>
              <NumberedStep number={4} title="Decide pricing separately">
                Review each product category, enter approved unit prices where
                required, set validity, and record the rationale.
              </NumberedStep>
              <NumberedStep number={5} title="Maintain governed data">
                Use Administration for companies, users, End-users, products,
                competitor brands, notification templates, and delivery retries.
              </NumberedStep>
            </List>
          </GuideSection>
          <GuideSection title="Administrator daily checklist">
            <List disablePadding>
              <NumberedStep
                number={1}
                title="Review new and changed registrations"
              >
                Prioritize Submitted, Changes requested responses, and Review
                required after edit. Open Activity to see exactly what changed.
              </NumberedStep>
              <NumberedStep number={2} title="Resolve matching suggestions">
                Check the normalized End-user, address, requested products,
                supporting factors, and conflicts. Never confirm a match from
                the score alone.
              </NumberedStep>
              <NumberedStep
                number={3}
                title="Complete pending pricing decisions"
              >
                Review each category independently. Confirm approved prices and
                validity before saving the decision.
              </NumberedStep>
              <NumberedStep number={4} title="Check notification failures">
                Open Administration, then Notification deliveries. Failed email
                can be retried, but the portal notification remains valid.
              </NumberedStep>
              <NumberedStep number={5} title="Maintain review queues">
                Check expiring approvals, renewal requests, and project-status
                updates so company users see current information.
              </NumberedStep>
            </List>
          </GuideSection>
          <GuideSection title="How to make a registration decision">
            <List dense disablePadding>
              <ListItem disableGutters>
                <ListItemText
                  primary="Start review"
                  secondary="Use when examination has begun. This records the reviewer and moves the registration into review without approving it."
                />
              </ListItem>
              <ListItem disableGutters>
                <ListItemText
                  primary="Confirm match"
                  secondary="Use only when the evidence supports the selected opportunity scope. Create a new opportunity only when no existing scope correctly represents it."
                />
              </ListItem>
              <ListItem disableGutters>
                <ListItemText
                  primary="Request changes"
                  secondary="State exactly what the company must correct. The company can edit and resubmit the registration."
                />
              </ListItem>
              <ListItem disableGutters>
                <ListItemText
                  primary="Reject"
                  secondary="Provide a clear business reason. Rejection is a registration decision, not a statement that the procurement project was cancelled."
                />
              </ListItem>
            </List>
          </GuideSection>
          <GuideSection title="How to make a pricing decision">
            <List disablePadding>
              <NumberedStep
                number={1}
                title="Verify the category and requested items"
              >
                Pricing decisions are category-specific. Mixed outcomes can
                exist on one registration.
              </NumberedStep>
              <NumberedStep number={2} title="Choose the decision">
                Approve, partially approve, reject, or request changes according
                to the reviewed commercial terms.
              </NumberedStep>
              <NumberedStep number={3} title="Enter approved unit prices">
                Enter prices only for the items covered by the approval.
                Requested prices remain proposals.
              </NumberedStep>
              <NumberedStep number={4} title="Set validity and rationale">
                Record when the terms expire and why the decision was made. The
                company notification excludes detailed sensitive pricing.
              </NumberedStep>
            </List>
          </GuideSection>
          <GuideSection title="Administration and master data">
            <List dense disablePadding>
              <ListItem disableGutters>
                <ListItemText
                  primary="Users and companies"
                  secondary="Assign company users to the correct company. Company membership controls tenant access and must be checked carefully."
                />
              </ListItem>
              <ListItem disableGutters>
                <ListItemText
                  primary="End-users"
                  secondary="Verify pending proposals against an authoritative source, correct the official record, and add useful aliases instead of creating duplicates."
                />
              </ListItem>
              <ListItem disableGutters>
                <ListItemText
                  primary="Products"
                  secondary="Maintain catalog identity and approved list-price data. Existing registration snapshots are historical records."
                />
              </ListItem>
              <ListItem disableGutters>
                <ListItemText
                  primary="Competitor brands"
                  secondary="Maintain canonical brands and aliases. For example, Hewlett Packard resolves to HP."
                />
              </ListItem>
              <ListItem disableGutters>
                <ListItemText
                  primary="Notification settings"
                  secondary="Enable email per event and edit the subject and body templates. Always check the preview before saving."
                />
              </ListItem>
            </List>
          </GuideSection>
        </Stack>
      )}

      <Typography variant="h2" gutterBottom>
        What happens after submission?
      </Typography>
      <Grid container spacing={2} sx={{ mb: 3 }}>
        {submissionSteps.map(([title, description], index) => (
          <Grid key={title} size={{ xs: 12, md: 4 }}>
            <Paper variant="outlined" sx={{ height: "100%", p: 2 }}>
              <Stack direction="row" spacing={1.5} alignItems="flex-start">
                <Chip color="primary" label={index + 1} size="small" />
                <Box>
                  <Typography fontWeight={700}>{title}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    {description}
                  </Typography>
                </Box>
              </Stack>
            </Paper>
          </Grid>
        ))}
      </Grid>

      <GuideSection title="Understand registration statuses">
        <Stack spacing={1}>
          {registrationStatuses.map(([status, meaning]) => (
            <Box
              key={status}
              sx={{
                display: "grid",
                gap: 1,
                gridTemplateColumns: { xs: "1fr", sm: "180px 1fr" },
              }}
            >
              <Typography variant="body2" fontWeight={700}>
                {status}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {meaning}
              </Typography>
            </Box>
          ))}
        </Stack>
      </GuideSection>

      <GuideSection title="How to read a registration page">
        <List dense disablePadding>
          <ListItem disableGutters>
            <ListItemText
              primary="Registration status"
              secondary="DBGI's decision about your company's registration claim."
            />
          </ListItem>
          <ListItem disableGutters>
            <ListItemText
              primary="Project status"
              secondary="What is happening to the procurement project, such as upcoming, active, won, lost, cancelled, or on hold."
            />
          </ListItem>
          <ListItem disableGutters>
            <ListItemText
              primary="Pricing status"
              secondary="Whether requested terms are pending, approved, partially approved, rejected, or expired."
            />
          </ListItem>
          <ListItem disableGutters>
            <ListItemText
              primary="Activity"
              secondary="Who changed or decided something and when. Select View changes to inspect previous and current values."
            />
          </ListItem>
        </List>
      </GuideSection>

      <GuideSection title="If something goes wrong">
        <List dense disablePadding>
          <ListItem disableGutters>
            <ListItemText
              primary="You cannot edit"
              secondary="The current workflow status may be locked. Check the status and DBGI decision before contacting support."
            />
          </ListItem>
          <ListItem disableGutters>
            <ListItemText
              primary="An End-user is missing"
              secondary="Use Add missing End-user from the form instead of entering a different spelling elsewhere."
            />
          </ListItem>
          <ListItem disableGutters>
            <ListItemText
              primary="Email did not arrive"
              secondary="Check Notifications first. Portal notifications remain authoritative even when email delivery fails."
            />
          </ListItem>
          <ListItem disableGutters>
            <ListItemText
              primary="The page reports a conflict"
              secondary="Someone changed the record after you opened it. Reload the latest version before entering your changes again."
            />
          </ListItem>
        </List>
      </GuideSection>
    </Container>
  );
}
