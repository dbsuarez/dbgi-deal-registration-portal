import {
  Alert,
  Box,
  Button,
  Checkbox,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
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
import { useState } from "react";

import {
  decideRepeatOrder,
  getRegistration,
  requestRepeatOrder,
  type RegistrationDetail,
  type RepeatOrder,
} from "../api";

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

function formatTimestamp(value: string) {
  return new Date(value).toLocaleString("sv-SE", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

type Props = {
  registration: RegistrationDetail;
  isDbgiAdmin: boolean;
  csrfToken: string;
  oneWorkingDayEnds?: string;
  onChange: (updated: RegistrationDetail) => void;
};

export default function RepeatOrdersSection({
  registration,
  isDbgiAdmin,
  csrfToken,
  oneWorkingDayEnds,
  onChange,
}: Props) {
  const orders = registration.repeat_orders ?? [];
  const choices = registration.repeat_order_choices ?? [];

  const [requestOpen, setRequestOpen] = useState(false);
  const [quantities, setQuantities] = useState<Record<number, string>>({});
  const [noa, setNoa] = useState<File | null>(null);
  const [ntp, setNtp] = useState<File | null>(null);
  const [confirmed, setConfirmed] = useState(false);
  const [note, setNote] = useState("");
  const [decision, setDecision] = useState<{
    order: RepeatOrder;
    accept: boolean;
  } | null>(null);
  const [reason, setReason] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  if (orders.length === 0 && choices.length === 0) return null;

  const lines = choices
    .map((choice) => ({
      item_id: choice.item_id,
      quantity: Number(quantities[choice.item_id] ?? 0),
    }))
    .filter((line) => line.quantity > 0);
  const quantitiesValid = choices.every((choice) => {
    const value = quantities[choice.item_id];
    return !value || (Number.isInteger(Number(value)) && Number(value) >= 0);
  });
  const canSend =
    lines.length > 0 && quantitiesValid && noa && ntp && confirmed && !saving;

  const openRequest = () => {
    setQuantities({});
    setNoa(null);
    setNtp(null);
    setConfirmed(false);
    setNote("");
    setError("");
    setRequestOpen(true);
  };

  const sendRequest = async () => {
    if (!noa || !ntp) return;
    setSaving(true);
    setError("");
    try {
      await requestRepeatOrder(
        registration.id,
        { noa, ntp, lines, note: note.trim() },
        csrfToken,
      );
      onChange(await getRegistration(registration.id));
      setRequestOpen(false);
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "The repeat order could not be sent.",
      );
    } finally {
      setSaving(false);
    }
  };

  const saveDecision = async () => {
    if (!decision) return;
    setSaving(true);
    setError("");
    try {
      await decideRepeatOrder(
        decision.order.id,
        { accept: decision.accept, reason: reason.trim() },
        csrfToken,
      );
      onChange(await getRegistration(registration.id));
      setDecision(null);
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "The decision could not be saved.",
      );
    } finally {
      setSaving(false);
    }
  };

  return (
    <Paper sx={{ mt: 3, p: 2 }}>
      <Stack
        direction="row"
        justifyContent="space-between"
        alignItems="center"
        sx={{ mb: 1 }}
      >
        <Typography variant="h2">Repeat orders</Typography>
        {!isDbgiAdmin && choices.length > 0 && (
          <Button onClick={openRequest}>Request repeat order</Button>
        )}
      </Stack>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
        A repeat order is when the same buyer orders more of the same item
        without a new bidding. It can use the approved price if the buyer&apos;s
        Notice of Award and Notice to Proceed say it is a repeat order.
      </Typography>
      {orders.length > 0 && (
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Requested</TableCell>
                <TableCell>Products</TableCell>
                <TableCell sx={moneyCell}>Total (with VAT)</TableCell>
                <TableCell>Letters</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>DBGI&apos;s reason</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {orders.map((order) => (
                <TableRow key={order.id}>
                  <TableCell>{formatTimestamp(order.requested_at)}</TableCell>
                  <TableCell>
                    {order.lines.map((line) => (
                      <Typography
                        key={line.product_name}
                        variant="body2"
                        component="div"
                      >
                        {line.product_name}: {line.quantity} at{" "}
                        {money(line.approved_unit_price)}
                      </Typography>
                    ))}
                    {order.note && (
                      <Typography variant="caption" color="text.secondary">
                        {order.note}
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell sx={moneyCell}>{money(order.total)}</TableCell>
                  <TableCell>
                    <Box>
                      <Link href={order.noa_url}>NOA</Link>
                    </Box>
                    <Box>
                      <Link href={order.ntp_url}>NTP</Link>
                    </Box>
                  </TableCell>
                  <TableCell>{order.status_label}</TableCell>
                  <TableCell>
                    {order.decision_reason}
                    {order.can_decide && (
                      <>
                        <Button
                          size="small"
                          onClick={() => {
                            setDecision({ order, accept: true });
                            setReason("");
                            setError("");
                          }}
                        >
                          Accept
                        </Button>
                        <Button
                          size="small"
                          color="error"
                          onClick={() => {
                            setDecision({ order, accept: false });
                            setReason("");
                            setError("");
                          }}
                        >
                          Decline
                        </Button>
                      </>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      <Dialog
        open={requestOpen}
        onClose={() => !saving && setRequestOpen(false)}
        fullWidth
        maxWidth="sm"
      >
        <DialogTitle>Request a repeat order</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            This uses your approved price again. The order must be from{" "}
            {registration.end_user_name}. Please allow at least one working day
            for DBGI to review your request
            {oneWorkingDayEnds ? `, up to ${oneWorkingDayEnds}` : ""}.
          </Typography>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          <Stack spacing={2}>
            {choices.map((choice) => (
              <TextField
                key={choice.item_id}
                type="number"
                label={`Quantity of ${choice.product_name}`}
                helperText={`Approved price ${money(choice.approved_unit_price)}, valid until ${choice.valid_until ?? "not set"}. Leave blank if not ordered.`}
                value={quantities[choice.item_id] ?? ""}
                onChange={(event) =>
                  setQuantities((current) => ({
                    ...current,
                    [choice.item_id]: event.target.value,
                  }))
                }
                slotProps={{
                  htmlInput: { min: 0, style: { textAlign: "right" } },
                }}
              />
            ))}
            <Stack direction="row" spacing={2} alignItems="center">
              <Button component="label" variant="outlined">
                Notice of Award (NOA)
                <input
                  hidden
                  type="file"
                  aria-label="Notice of Award file"
                  onChange={(event) => setNoa(event.target.files?.[0] ?? null)}
                />
              </Button>
              <Typography variant="body2">
                {noa?.name ?? "No file chosen"}
              </Typography>
            </Stack>
            <Stack direction="row" spacing={2} alignItems="center">
              <Button component="label" variant="outlined">
                Notice to Proceed (NTP)
                <input
                  hidden
                  type="file"
                  aria-label="Notice to Proceed file"
                  onChange={(event) => setNtp(event.target.files?.[0] ?? null)}
                />
              </Button>
              <Typography variant="body2">
                {ntp?.name ?? "No file chosen"}
              </Typography>
            </Stack>
            <FormControlLabel
              control={
                <Checkbox
                  checked={confirmed}
                  onChange={(event) => setConfirmed(event.target.checked)}
                />
              }
              label={`Both letters are from ${registration.end_user_name} and say this is a repeat order.`}
            />
            <TextField
              fullWidth
              multiline
              minRows={2}
              label="Note (optional)"
              value={note}
              onChange={(event) => setNote(event.target.value)}
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRequestOpen(false)} disabled={saving}>
            Cancel
          </Button>
          <Button variant="contained" disabled={!canSend} onClick={sendRequest}>
            Send request
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog
        open={decision !== null}
        onClose={() => !saving && setDecision(null)}
        fullWidth
        maxWidth="sm"
      >
        <DialogTitle>
          {decision?.accept
            ? "Accept this repeat order?"
            : "Decline this repeat order?"}
        </DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Check that both letters are from {registration.end_user_name} and
            say it is a repeat order. If not, decline it. The partner can read
            your reason, and can register a new deal instead.
          </Typography>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          <TextField
            required
            fullWidth
            multiline
            minRows={3}
            label="Reason"
            helperText="At least 5 characters."
            value={reason}
            onChange={(event) => setReason(event.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDecision(null)} disabled={saving}>
            Cancel
          </Button>
          <Button
            variant="contained"
            color={decision?.accept ? "primary" : "error"}
            disabled={saving || reason.trim().length < 5}
            onClick={saveDecision}
          >
            {decision?.accept ? "Accept repeat order" : "Decline repeat order"}
          </Button>
        </DialogActions>
      </Dialog>
    </Paper>
  );
}
