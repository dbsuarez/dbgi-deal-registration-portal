import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import EditIcon from "@mui/icons-material/Edit";
import {
  Alert,
  Box,
  Breadcrumbs,
  Button,
  Chip,
  CircularProgress,
  Container,
  Divider,
  Grid,
  IconButton,
  Link,
  List,
  ListItem,
  ListItemText,
  Paper,
  Snackbar,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { getRegistration, type RegistrationDetail } from "../api";

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
  const { id } = useParams();
  const navigate = useNavigate();
  const [registration, setRegistration] = useState<RegistrationDetail | null>(
    null,
  );
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    getRegistration(Number(id), controller.signal)
      .then(setRegistration)
      .catch((reason: Error) => {
        if (reason.name !== "AbortError") setError(reason.message);
      });
    return () => controller.abort();
  }, [id]);

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
    </Container>
  );
}
