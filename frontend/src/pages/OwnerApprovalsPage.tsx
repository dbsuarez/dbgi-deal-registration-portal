import {
  Alert,
  Box,
  Button,
  Checkbox,
  CircularProgress,
  Container,
  FormControlLabel,
  Link,
  Paper,
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

import {
  RequestError,
  decideCategoryPrice,
  getOwnerApprovals,
  type OwnerApproval,
} from "../api";
import { useSession } from "../session";

const moneyCell = {
  textAlign: "right" as const,
  fontVariantNumeric: "tabular-nums",
};

function money(value: string | number | null) {
  if (value === null || value === "") return "-";
  return Number(value).toLocaleString("en-PH", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

// One waiting price, decided right here: the owner never needs the deal page or Django Admin.
function ApprovalCard({
  row,
  canDecide,
  csrfToken,
  onDone,
}: {
  row: OwnerApproval;
  canDecide: boolean;
  csrfToken: string;
  onDone: (message: string) => void;
}) {
  const [prices, setPrices] = useState<Record<number, string>>(() =>
    Object.fromEntries(
      row.items.map((item) => [item.item_id, item.proposed_price ?? ""]),
    ),
  );
  const [note, setNote] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [costWarnings, setCostWarnings] = useState<string[]>([]);
  const [costConfirmed, setCostConfirmed] = useState(false);
  const [rankWarnings, setRankWarnings] = useState<string[]>([]);
  const [rankConfirmed, setRankConfirmed] = useState(false);

  const discount = (list: string | null, price: string) =>
    !list || !price.trim()
      ? null
      : ((Number(list) - Number(price)) * 100) / Number(list);

  const decide = async (approve: boolean) => {
    setSaving(true);
    setError("");
    try {
      await decideCategoryPrice(
        row.approval_id,
        {
          version: row.version,
          status: approve ? row.proposed_status : "rejected",
          rationale: note.trim(),
          valid_until: null,
          approved_prices: approve
            ? Object.fromEntries(
                row.items
                  .filter((item) => prices[item.item_id]?.trim())
                  .map((item) => [
                    String(item.item_id),
                    prices[item.item_id].trim(),
                  ]),
              )
            : {},
          rank_exception_confirmed: rankConfirmed,
          below_cost_confirmed: costConfirmed,
        },
        csrfToken,
      );
      onDone(
        approve
          ? `${row.reference}: approved. The company is told.`
          : `${row.reference}: declined. The company is told.`,
      );
    } catch (failure) {
      const messages =
        failure instanceof RequestError
          ? (failure.details ?? []).map((detail) => detail.message)
          : [];
      if (
        failure instanceof RequestError &&
        failure.code === "below_cost_needs_confirmation"
      ) {
        setCostWarnings(messages);
      } else if (
        failure instanceof RequestError &&
        failure.code === "rank_rule_needs_confirmation"
      ) {
        setRankWarnings(messages);
      } else {
        setError(
          failure instanceof Error
            ? failure.message
            : "That could not be saved.",
        );
      }
    } finally {
      setSaving(false);
    }
  };

  const ready =
    note.trim().length >= 5 &&
    !saving &&
    (costWarnings.length === 0 || costConfirmed) &&
    (rankWarnings.length === 0 || rankConfirmed);

  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="h2">
        {row.company_name}: {row.category}
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
        {row.project_title} | Bid date {row.bid_date} |{" "}
        <Link href={`/registrations/${row.registration_id}/`}>
          {row.reference}
        </Link>
      </Typography>
      <Typography variant="body2" sx={{ mb: 1 }}>
        <strong>{row.proposed_by_name ?? "An admin"}</strong> proposed this
        price{row.rationale ? `: "${row.rationale}"` : "."}
      </Typography>
      <TableContainer>
        <Table size="small" aria-label={`Prices for ${row.reference}`}>
          <TableHead>
            <TableRow>
              <TableCell>Product</TableCell>
              <TableCell sx={moneyCell}>Quantity</TableCell>
              <TableCell sx={moneyCell}>List price</TableCell>
              <TableCell sx={moneyCell}>Landed cost</TableCell>
              <TableCell sx={moneyCell}>Price to approve</TableCell>
              <TableCell sx={moneyCell}>Discount</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {row.items.map((item) => {
              const price = prices[item.item_id] ?? "";
              const off = discount(item.list_price, price);
              const belowCost =
                Boolean(item.landed_cost) &&
                Boolean(price.trim()) &&
                Number(price) < Number(item.landed_cost);
              return (
                <TableRow key={item.item_id}>
                  <TableCell>{item.name}</TableCell>
                  <TableCell sx={moneyCell}>{item.quantity}</TableCell>
                  <TableCell sx={moneyCell}>{money(item.list_price)}</TableCell>
                  <TableCell sx={moneyCell}>
                    {money(item.landed_cost)}
                  </TableCell>
                  <TableCell sx={moneyCell}>
                    {canDecide ? (
                      <TextField
                        size="small"
                        type="number"
                        error={belowCost}
                        value={price}
                        onChange={(event) => {
                          setPrices((current) => ({
                            ...current,
                            [item.item_id]: event.target.value,
                          }));
                          setCostWarnings([]);
                          setCostConfirmed(false);
                          setRankWarnings([]);
                          setRankConfirmed(false);
                        }}
                        slotProps={{
                          htmlInput: {
                            min: 0,
                            step: "0.01",
                            style: { textAlign: "right" },
                            "aria-label": `Price to approve for ${item.name}`,
                          },
                        }}
                      />
                    ) : (
                      money(item.proposed_price)
                    )}
                  </TableCell>
                  <TableCell sx={moneyCell}>
                    {off === null ? "-" : `${off.toFixed(2)}%`}
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </TableContainer>
      {canDecide && (
        <Stack spacing={1.5} sx={{ mt: 2 }}>
          {costWarnings.length > 0 && (
            <Alert severity="error">
              {costWarnings.map((warning) => (
                <div key={warning}>{warning}</div>
              ))}
              <FormControlLabel
                control={
                  <Checkbox
                    checked={costConfirmed}
                    onChange={(event) => setCostConfirmed(event.target.checked)}
                  />
                }
                label="This is not a typo. I approve selling below the landed cost."
              />
            </Alert>
          )}
          {rankWarnings.length > 0 && (
            <Alert severity="warning">
              {rankWarnings.map((warning) => (
                <div key={warning}>{warning}</div>
              ))}
              <FormControlLabel
                control={
                  <Checkbox
                    checked={rankConfirmed}
                    onChange={(event) => setRankConfirmed(event.target.checked)}
                  />
                }
                label="I confirm this exception to the rank rule."
              />
            </Alert>
          )}
          {error && <Alert severity="error">{error}</Alert>}
          <TextField
            required
            fullWidth
            multiline
            minRows={2}
            label="Your note"
            helperText="At least 5 characters. The company reads it when you approve or decline."
            placeholder="For example: Approved for this bid."
            slotProps={{ inputLabel: { shrink: true } }}
            value={note}
            onChange={(event) => setNote(event.target.value)}
          />
          <Stack direction="row" spacing={1}>
            <Button
              variant="contained"
              disabled={!ready}
              onClick={() => decide(true)}
            >
              Approve
            </Button>
            <Button
              variant="outlined"
              color="error"
              disabled={!ready}
              onClick={() => decide(false)}
            >
              Decline
            </Button>
          </Stack>
        </Stack>
      )}
    </Paper>
  );
}

// Prices an admin approved with a discount above their limit, waiting for the owner.
export default function OwnerApprovalsPage() {
  const session = useSession();
  const [rows, setRows] = useState<OwnerApproval[] | null>(null);
  const [error, setError] = useState("");
  const [done, setDone] = useState<string[]>([]);

  useEffect(() => {
    const controller = new AbortController();
    getOwnerApprovals(controller.signal)
      .then(setRows)
      .catch((failure) => {
        if (!controller.signal.aborted)
          setError(
            failure instanceof Error
              ? failure.message
              : "The list could not be loaded.",
          );
      });
    return () => controller.abort();
  }, []);

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h1" gutterBottom>
        Owner approvals
      </Typography>
      <Typography color="text.secondary" sx={{ mb: 3 }}>
        {session.is_owner
          ? "These prices have a discount above what admins can approve. Check each one, change the price if needed, write a short note, then click Approve or Decline."
          : "Prices with a discount above the admin limit, waiting for the owner. Only the owner can approve or decline them."}
      </Typography>
      {done.map((message) => (
        <Alert severity="success" key={message} sx={{ mb: 1 }}>
          {message}
        </Alert>
      ))}
      {error && <Alert severity="error">{error}</Alert>}
      {!rows && !error && (
        <Box>
          <CircularProgress aria-label="Loading" />
        </Box>
      )}
      {rows && rows.length === 0 && (
        <Alert severity="info">Nothing is waiting for approval.</Alert>
      )}
      <Stack spacing={2}>
        {(rows ?? []).map((row) => (
          <ApprovalCard
            key={row.approval_id}
            row={row}
            canDecide={Boolean(session.is_owner)}
            csrfToken={session.csrf_token}
            onDone={(message) => {
              setDone((current) => [...current, message]);
              setRows((current) =>
                (current ?? []).filter(
                  (other) => other.approval_id !== row.approval_id,
                ),
              );
            }}
          />
        ))}
      </Stack>
    </Container>
  );
}
