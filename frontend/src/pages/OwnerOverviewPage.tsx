import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Container,
  Grid,
  Link,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import { useEffect, useState, type ReactNode } from "react";

import { getOwnerOverview, type OwnerOverview } from "../api";

const moneyCell = {
  textAlign: "right" as const,
  fontVariantNumeric: "tabular-nums",
};

function money(value: string | number) {
  return Number(value).toLocaleString("en-PH", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function percent(value: string | null, empty: string) {
  return value === null ? empty : `${Number(value).toFixed(2)}%`;
}

function Stat({
  label,
  value,
  detail,
}: {
  label: string;
  value: string;
  detail: string;
}) {
  return (
    <Paper sx={{ p: 2, height: "100%" }}>
      <Typography variant="body2" color="text.secondary">
        {label}
      </Typography>
      <Typography
        variant="h2"
        component="p"
        sx={{ fontVariantNumeric: "tabular-nums", my: 0.5 }}
      >
        {value}
      </Typography>
      <Typography variant="caption" color="text.secondary">
        {detail}
      </Typography>
    </Paper>
  );
}

function Section({
  title,
  empty,
  children,
}: {
  title: string;
  empty: string | null;
  children: ReactNode;
}) {
  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="h2" gutterBottom>
        {title}
      </Typography>
      {empty ? (
        <Typography variant="body2" color="text.secondary">
          {empty}
        </Typography>
      ) : (
        children
      )}
    </Paper>
  );
}

function DealLink({ id, children }: { id: number; children: ReactNode }) {
  return <Link href={`/registrations/${id}/`}>{children}</Link>;
}

// The owner's home: a few numbers and short lists, so he sees what is happening without
// reading every deal.
export default function OwnerOverviewPage() {
  const [data, setData] = useState<OwnerOverview | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    getOwnerOverview(controller.signal)
      .then(setData)
      .catch((failure) => {
        if (!controller.signal.aborted)
          setError(
            failure instanceof Error
              ? failure.message
              : "The overview could not be loaded.",
          );
      });
    return () => controller.abort();
  }, []);

  if (error)
    return (
      <Container sx={{ py: 4 }}>
        <Alert severity="error">{error}</Alert>
      </Container>
    );
  if (!data)
    return (
      <Container sx={{ py: 4 }}>
        <CircularProgress aria-label="Loading" />
      </Container>
    );

  const month = data.month;
  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Stack
        direction={{ xs: "column", sm: "row" }}
        justifyContent="space-between"
        alignItems={{ xs: "flex-start", sm: "center" }}
        spacing={1}
        sx={{ mb: 2 }}
      >
        <Typography variant="h1">Overview</Typography>
        <Button variant="outlined" href="/deals/">
          All deals
        </Button>
      </Stack>

      {data.waiting_for_owner > 0 && (
        <Alert
          severity="warning"
          sx={{ mb: 3 }}
          action={
            <Button color="inherit" size="small" href="/owner-approvals/">
              Open Owner approvals
            </Button>
          }
        >
          {data.waiting_for_owner === 1
            ? "1 price is waiting for your approval."
            : `${data.waiting_for_owner} prices are waiting for your approval.`}
        </Alert>
      )}

      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
        {month.label} so far, compared with last month
      </Typography>
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, sm: 6, md: 4 }}>
          <Stat
            label="New deals"
            value={String(month.new_deals)}
            detail={`Last month: ${month.new_deals_last_month}`}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 4 }}>
          <Stat
            label="Projects won"
            value={`${month.won} | ${money(month.won_value)}`}
            detail={`Last month: ${month.won_last_month} | ${money(month.won_value_last_month)}`}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 4 }}>
          <Stat
            label="Lost or cancelled"
            value={String(month.lost_or_cancelled)}
            detail={`Last month: ${month.lost_or_cancelled_last_month}`}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 4 }}>
          <Stat
            label="Pipeline (open deals)"
            value={money(month.pipeline_value)}
            detail={`${month.pipeline_deals} open deal${month.pipeline_deals === 1 ? "" : "s"}`}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 4 }}>
          <Stat
            label="Average discount approved"
            value={percent(data.average_discount.this_month, "None yet")}
            detail={`Last month: ${percent(data.average_discount.last_month, "none")}`}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 4 }}>
          <Stat
            label={`Win rate, ${data.quarter_label}`}
            value={
              data.win_rate.percent === null
                ? "No results yet"
                : `${data.win_rate.percent}%`
            }
            detail={`${data.win_rate.won} won, ${data.win_rate.lost} lost (cancelled not counted)`}
          />
        </Grid>
      </Grid>

      <Stack spacing={2}>
        <Section
          title="Bids in the next 14 days"
          empty={
            data.upcoming_bids.length ? null : "No bids in the next 14 days."
          }
        >
          <TableContainer>
            <Table size="small" aria-label="Bids in the next 14 days">
              <TableHead>
                <TableRow>
                  <TableCell>Bid date</TableCell>
                  <TableCell>Company</TableCell>
                  <TableCell>Project</TableCell>
                  <TableCell>Price</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {data.upcoming_bids.map((row) => (
                  <TableRow key={row.registration_id}>
                    <TableCell>{row.bid_date}</TableCell>
                    <TableCell>{row.company_name}</TableCell>
                    <TableCell>
                      <DealLink id={row.registration_id}>
                        {row.project_title}
                      </DealLink>
                    </TableCell>
                    <TableCell>
                      <Chip
                        size="small"
                        label={row.price_decided ? "Decided" : "Not decided"}
                        color={row.price_decided ? "success" : "warning"}
                      />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
          {data.upcoming_more > 0 && (
            <Typography variant="caption" color="text.secondary">
              And {data.upcoming_more} more.
            </Typography>
          )}
        </Section>

        <Section
          title="Stuck"
          empty={data.stuck.length ? null : "Nothing is stuck."}
        >
          <Stack spacing={0.5}>
            {data.stuck.map((row) => (
              <Typography
                variant="body2"
                key={`${row.registration_id}-${row.reason}`}
              >
                <DealLink id={row.registration_id}>{row.reference}</DealLink>{" "}
                {row.company_name}: {row.reason}.
              </Typography>
            ))}
          </Stack>
        </Section>

        <Grid container spacing={2}>
          <Grid size={{ xs: 12, md: 6 }}>
            <Section
              title={`Thin margins (less than ${Number(data.thin_margin_percent)}% above landed cost)`}
              empty={data.thin_margins.length ? null : "No thin margins."}
            >
              <TableContainer>
                <Table size="small" aria-label="Thin margins">
                  <TableHead>
                    <TableRow>
                      <TableCell>Company</TableCell>
                      <TableCell>Product</TableCell>
                      <TableCell sx={moneyCell}>Price</TableCell>
                      <TableCell sx={moneyCell}>Landed cost</TableCell>
                      <TableCell sx={moneyCell}>Margin</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {data.thin_margins.map((row) => (
                      <TableRow key={`${row.registration_id}-${row.product}`}>
                        <TableCell>
                          <DealLink id={row.registration_id}>
                            {row.company_name}
                          </DealLink>
                        </TableCell>
                        <TableCell>{row.product}</TableCell>
                        <TableCell sx={moneyCell}>
                          {money(row.approved_price)}
                        </TableCell>
                        <TableCell sx={moneyCell}>
                          {money(row.landed_cost)}
                        </TableCell>
                        <TableCell sx={moneyCell}>
                          {percent(row.margin_percent, "-")}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
              {data.thin_margins_more > 0 && (
                <Typography variant="caption" color="text.secondary">
                  And {data.thin_margins_more} more.
                </Typography>
              )}
            </Section>
          </Grid>
          <Grid size={{ xs: 12, md: 6 }}>
            <Section
              title="Prices ending soon, still bidding"
              empty={
                data.prices_ending.length
                  ? null
                  : "No approved prices end in the next 14 days."
              }
            >
              <TableContainer>
                <Table size="small" aria-label="Prices ending soon">
                  <TableHead>
                    <TableRow>
                      <TableCell>Price ends</TableCell>
                      <TableCell>Company</TableCell>
                      <TableCell>Products</TableCell>
                      <TableCell>Bid date</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {data.prices_ending.map((row) => (
                      <TableRow key={`${row.registration_id}-${row.category}`}>
                        <TableCell>{row.valid_until}</TableCell>
                        <TableCell>
                          <DealLink id={row.registration_id}>
                            {row.company_name}
                          </DealLink>
                        </TableCell>
                        <TableCell>{row.category}</TableCell>
                        <TableCell>{row.bid_date}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
              {data.prices_ending_more > 0 && (
                <Typography variant="caption" color="text.secondary">
                  And {data.prices_ending_more} more.
                </Typography>
              )}
            </Section>
          </Grid>
          <Grid size={{ xs: 12, md: 7 }}>
            <Section
              title="Recent wins"
              empty={data.recent_wins.length ? null : "No wins yet."}
            >
              <TableContainer>
                <Table size="small" aria-label="Recent wins">
                  <TableHead>
                    <TableRow>
                      <TableCell>Won on</TableCell>
                      <TableCell>Company</TableCell>
                      <TableCell sx={moneyCell}>Value</TableCell>
                      <TableCell>Certificates</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {data.recent_wins.map((row) => (
                      <TableRow key={row.registration_id}>
                        <TableCell>{row.won_on ?? "-"}</TableCell>
                        <TableCell>
                          <DealLink id={row.registration_id}>
                            {row.company_name}
                          </DealLink>
                        </TableCell>
                        <TableCell sx={moneyCell}>{money(row.value)}</TableCell>
                        <TableCell>
                          {row.certificates_issued ? "Issued" : "Not yet"}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Section>
          </Grid>
          <Grid size={{ xs: 12, md: 5 }}>
            <Section
              title={`Top partners, ${data.quarter_label}`}
              empty={
                data.top_partners.length ? null : "No deals this quarter yet."
              }
            >
              <TableContainer>
                <Table size="small" aria-label="Top partners">
                  <TableHead>
                    <TableRow>
                      <TableCell>Company</TableCell>
                      <TableCell sx={moneyCell}>Deals</TableCell>
                      <TableCell sx={moneyCell}>Value</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {data.top_partners.map((row) => (
                      <TableRow key={row.company_name}>
                        <TableCell>{row.company_name}</TableCell>
                        <TableCell sx={moneyCell}>{row.deals}</TableCell>
                        <TableCell sx={moneyCell}>{money(row.value)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Section>
          </Grid>
        </Grid>
        <Box>
          <Typography variant="caption" color="text.secondary">
            Won, lost, and cancelled count the outcome reports DBGI confirmed.
            Values use approved prices where there are any, and requested prices
            otherwise.
          </Typography>
        </Box>
      </Stack>
    </Container>
  );
}
