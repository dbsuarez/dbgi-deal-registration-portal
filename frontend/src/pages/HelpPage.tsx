import {
  Alert,
  Box,
  Breadcrumbs,
  Container,
  Grid,
  Link,
  Paper,
  Stack,
  Typography,
} from "@mui/material";

const steps = [
  {
    number: 1,
    title: "Submission confirmed",
    description:
      "After a registration is submitted, the portal records it for DBGI review and notifies all active users in the submitting company.",
  },
  {
    number: 2,
    title: "Registration decision",
    description:
      "DBGI reviews the registration and its matching evidence. Your company is notified when DBGI confirms it, rejects it, or requests changes.",
  },
  {
    number: 3,
    title: "Price request decision",
    description:
      "DBGI reviews each requested product category. Your company is notified when pricing is approved, partially approved, rejected, or returned for changes.",
  },
];

export default function HelpPage() {
  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Breadcrumbs aria-label="Breadcrumb" sx={{ mb: 2 }}>
        <Link href="/">Registrations</Link>
        <Typography color="text.primary">Help</Typography>
      </Breadcrumbs>
      <Typography variant="h1" gutterBottom>
        What happens after submission?
      </Typography>
      <Typography color="text.secondary" sx={{ mb: 3 }}>
        The portal keeps your company informed as a registration moves through
        review.
      </Typography>
      <Grid container spacing={2} sx={{ mb: 3 }}>
        {steps.map((step) => (
          <Grid key={step.number} size={{ xs: 12, md: 4 }}>
            <Paper variant="outlined" sx={{ height: "100%", p: 2.5 }}>
              <Stack direction="row" spacing={2} alignItems="flex-start">
                <Box
                  aria-hidden="true"
                  sx={{
                    bgcolor: "primary.main",
                    borderRadius: "50%",
                    color: "primary.contrastText",
                    display: "grid",
                    flex: "0 0 40px",
                    fontWeight: 700,
                    height: 40,
                    placeItems: "center",
                  }}
                >
                  {step.number}
                </Box>
                <Box>
                  <Typography variant="h2" sx={{ mb: 1 }}>
                    {step.title}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {step.description}
                  </Typography>
                </Box>
              </Stack>
            </Paper>
          </Grid>
        ))}
      </Grid>
      <Alert severity="info">
        The Notifications page is the authoritative record of these updates.
        Email delivery will be added only after DBGI approves the recipient and
        delivery policies.
      </Alert>
    </Container>
  );
}
