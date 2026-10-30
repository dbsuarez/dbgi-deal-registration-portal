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
    "Returned for changes",
    "Open the registration, read the reason, and select Edit.",
  ],
  ["Registered", "DBGI confirmed the registration and its opportunity match."],
  [
    "Review required after edit",
    "A confirmed registration changed and must be reviewed again.",
  ],
  ["Rejected", "Open the registration to review DBGI's reason."],
];

type PracticeScenario = {
  title: string;
  actor: string;
  before: string;
  steps: string[];
  expected: string;
};

const companyScenarios: PracticeScenario[] = [
  {
    title: "Submit a new registration",
    actor: "Company user",
    before:
      "Prepare the End-user, project dates, contact, attachment description, one competitor item, and one requested product.",
    steps: [
      "Open Registrations and select Create a registration.",
      "Select the End-user and complete every required project and contact field.",
      "Describe the attachment and confirm that you are authorized to share it.",
      "Add at least one competitor item and one requested product with quantity, requested price, and justification.",
      "Review the values and submit the registration.",
      "Open Notifications and select the Submission confirmed message.",
    ],
    expected:
      "A DBGI reference is created, the status is Submitted or a safe automatic-match result, an Activity entry is recorded, and active company users receive a portal notification and configured email.",
  },
  {
    title: "Correct a registration after DBGI requests changes",
    actor: "Company user",
    before:
      "Use a registration with status Returned for changes and read the administrator's reason.",
    steps: [
      "Open the notification for the requested change.",
      "Open the registration and identify the exact fields DBGI asked you to correct.",
      "Select Edit, change only the necessary information, and review the complete record.",
      "Submit the corrected registration.",
      "Open Activity and select View changes to confirm the previous and current values.",
    ],
    expected:
      "The version increases, the edit is audited, and the registration returns to DBGI for review. The previous decision is not silently retained.",
  },
  {
    title: "Verify an approved price",
    actor: "Company user",
    before:
      "Use a registration for which DBGI has completed a category pricing decision.",
    steps: [
      "Open Notifications and select the price-request decision.",
      "Open the registration and check the Pricing status badge.",
      "Review the category decision, validity date, and approved unit price for each covered item.",
      "Do not use requested prices for categories or items that do not show approval.",
    ],
    expected:
      "The approved terms and validity are visible in the portal. Email contains only a summary and does not replace the portal record.",
  },
];

const adminScenarios: PracticeScenario[] = [
  {
    title: "Review and confirm a registration match",
    actor: "DBGI administrator",
    before:
      "Use a Submitted registration with complete attachments and a matching suggestion.",
    steps: [
      "Open the registration and compare the End-user, address, requested products, supporting factors, and conflicts.",
      "Select Start review and enter a useful rationale.",
      "Recheck whether an existing opportunity scope is correct.",
      "Select Confirm match, choose the correct scope, or create a new opportunity only when no existing scope is valid.",
      "Open Activity and verify the reviewer, decision, rationale, and resulting status.",
    ],
    expected:
      "The registration becomes Registered, its opportunity scope is recorded, ranking can be calculated, and company users receive a registration-decision notification.",
  },
  {
    title: "Request corrections and review the resubmission",
    actor: "DBGI administrator, then company user",
    before:
      "Use a registration whose attachments or business details need a specific correction.",
    steps: [
      "Start review as the DBGI administrator.",
      "Select Request changes and write an exact, actionable reason.",
      "Sign in as the company user, open the notification, edit the requested fields, and submit again.",
      "Sign back in as the administrator and compare Activity's previous and current values.",
      "Start review again and make the appropriate final decision.",
    ],
    expected:
      "Both sides see a complete audit trail. The company can correct the record, and DBGI makes a new decision from the latest version.",
  },
  {
    title: "Approve category pricing",
    actor: "DBGI administrator",
    before:
      "Use a reviewed registration with requested catalog products and a Pending category approval.",
    steps: [
      "Open the registration and verify the requested products, list-price snapshots, requested prices, and justification.",
      "Open the category pricing decision.",
      "Choose Approved or Partially approved as appropriate.",
      "Enter approved unit prices only for covered items, set Valid until, and write the rationale.",
      "Save and reopen the registration to confirm the category and item results.",
    ],
    expected:
      "Approved prices and validity are saved separately from requested prices, an Activity entry is recorded, and company users receive a price-decision notification without detailed prices in email.",
  },
  {
    title: "Resolve a failed notification email",
    actor: "DBGI administrator",
    before:
      "Use a delivery showing Failed under Administration, Notification deliveries.",
    steps: [
      "Open the failed delivery and read the captured error without copying credentials into notes.",
      "Confirm that the recipient email address is correct and the portal notification exists.",
      "Correct the mailbox or SMTP configuration if needed.",
      "Return to Notification deliveries, select the failed record, and run Retry selected failed email deliveries.",
      "Refresh the record and confirm Sent status, attempt count, and sent time.",
    ],
    expected:
      "The email is retried and delivery history remains visible. The portal notification was available throughout the failure.",
  },
  {
    title: "Verify a proposed End-user",
    actor: "DBGI administrator",
    before: "Use a Pending End-user proposed by a company.",
    steps: [
      "Open Administration, End-users, and select the pending organization.",
      "Compare the name and address with an authoritative source.",
      "Correct the official name and address, add useful aliases, and avoid creating a duplicate.",
      "Record source information when available and verify the End-user.",
      "Return to the linked registration and refresh matching review.",
    ],
    expected:
      "The shared End-user becomes verified, aliases resolve to the canonical record, and eligible registrations can proceed through matching review.",
  },
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

function ScenarioCard({ scenario }: { scenario: PracticeScenario }) {
  return (
    <Accordion disableGutters variant="outlined">
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Box>
          <Typography fontWeight={700}>{scenario.title}</Typography>
          <Typography variant="caption" color="text.secondary">
            Actor: {scenario.actor}
          </Typography>
        </Box>
      </AccordionSummary>
      <AccordionDetails>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          <strong>Before you start:</strong> {scenario.before}
        </Typography>
        <List disablePadding>
          {scenario.steps.map((step, index) => (
            <NumberedStep key={step} number={index + 1} title={step}>
              {" "}
            </NumberedStep>
          ))}
        </List>
        <Alert severity="success" sx={{ mt: 1 }}>
          <strong>Expected result:</strong> {scenario.expected}
        </Alert>
      </AccordionDetails>
    </Accordion>
  );
}

export default function HelpPage() {
  const session = useSession();
  const isStandalone =
    new URLSearchParams(window.location.search).get("standalone") === "1";

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {!isStandalone && (
        <Breadcrumbs aria-label="Breadcrumb" sx={{ mb: 2 }}>
          <Link href="/">Registrations</Link>
          <Typography color="text.primary">Help</Typography>
        </Breadcrumbs>
      )}
      <Typography variant="h1" gutterBottom>
        Help and user guide
      </Typography>
      <Typography color="text.secondary" sx={{ mb: 2 }}>
        You do not need to memorize the system. Keep this page open and follow
        one numbered step at a time.
      </Typography>
      <Alert severity="info" sx={{ mb: 3 }}>
        You are signed in as {session.display_name}. This guide is showing the{" "}
        {session.is_dbgi_admin ? "DBGI administrator" : "company user"}{" "}
        workflow.
      </Alert>

      <Paper variant="outlined" sx={{ mb: 3, p: 2 }}>
        <Typography variant="h2" gutterBottom>
          How to use this guide
        </Typography>
        <List disablePadding>
          <NumberedStep number={1} title="Choose what you need to do">
            Open the section with the name that matches your task. You can close
            the other sections.
          </NumberedStep>
          <NumberedStep number={2} title="Keep Help beside the portal">
            {isStandalone
              ? "Move this Help window to one side of your screen and keep the portal on the other side."
              : "From the Help menu, choose Open in new window. Move Help to one side of your screen and the portal to the other side."}
          </NumberedStep>
          <NumberedStep number={3} title="Do one step, then come back here">
            Finish the current numbered step in the portal. Return to this guide
            and continue with the next number.
          </NumberedStep>
          <NumberedStep number={4} title="Check the expected result">
            When you finish, compare what you see with the expected result. If
            they are different, open If something goes wrong.
          </NumberedStep>
        </List>
      </Paper>

      <Paper variant="outlined" sx={{ mb: 3, p: 2 }}>
        <Typography variant="h2" gutterBottom>
          Start here
        </Typography>
        {!isStandalone && (
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
        )}
        <Typography variant="body2" color="text.secondary">
          A registration tells DBGI that your company is working on a customer
          project and wants DBGI to review it. A price you ask for is only a
          request until DBGI approves it.
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
              <NumberedStep number={4} title="Describe your attachment">
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
                Confirm the company, End-user, attachments, requested products,
                competitor information, and matching suggestion.
              </NumberedStep>
              <NumberedStep number={2} title="Start review">
                Review the system recommendation, match score, supporting and
                conflicting factors, and the registration attachments. Enter the
                review reason and select Start review. This step records that
                examination began but does not link or create an opportunity.
              </NumberedStep>
              <NumberedStep number={3} title="Decide the registration">
                After the status becomes Under review, select exactly one final
                decision: link an existing opportunity scope, create a new whole
                opportunity, request changes with exact instructions, or reject
                with a clear explanation. Company users are notified
                automatically.
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
                Prioritize Submitted, Returned for changes responses, and Review
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
                  secondary="Use when examination has begun. It moves the registration into review without linking or creating an opportunity."
                />
              </ListItem>
              <ListItem disableGutters>
                <ListItemText
                  primary="Link to an existing opportunity"
                  secondary="Choose the correct Opportunity scope only when the attachments show this registration belongs to an existing procurement opportunity."
                />
              </ListItem>
              <ListItem disableGutters>
                <ListItemText
                  primary="Create a new whole opportunity"
                  secondary="Use only when no existing Opportunity scope correctly represents the registration. The system creates and links a Whole scope."
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
                  secondary="Assign company users to the correct company and maintain their name, designation, email, and phone. New registrations use these values as editable contact defaults. Company membership controls tenant access and must be checked carefully."
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
                  primary="Competitor brands and models"
                  secondary="Maintain canonical brands, aliases, and model suggestions. For example, Hewlett Packard resolves to HP. Company users can enter a missing brand or model when registering a deal; it is then added to this catalog for later use. Archive outdated choices instead of deleting historical registration details."
                />
              </ListItem>
              <ListItem disableGutters>
                <ListItemText
                  primary="Notification settings"
                  secondary="Enable email per event and edit the subject and body templates. Always check the preview before saving."
                />
              </ListItem>
              <ListItem disableGutters>
                <ListItemText
                  primary="Danger Zone"
                  secondary="Only a Django superuser can open it. It permanently deletes every registration and related transaction after an exact confirmation, but preserves users and master data. Verify a backup before using it."
                />
              </ListItem>
            </List>
          </GuideSection>
        </Stack>
      )}

      <Box sx={{ mb: 3 }}>
        <Typography variant="h2" gutterBottom>
          End-to-end practice scenarios
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Use development or training data for practice. Do not experiment with
          a live business registration.
        </Typography>
        <Stack spacing={2}>
          {(session.is_dbgi_admin ? adminScenarios : companyScenarios).map(
            (scenario) => (
              <ScenarioCard key={scenario.title} scenario={scenario} />
            ),
          )}
        </Stack>
      </Box>

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
