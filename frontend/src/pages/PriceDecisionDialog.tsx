import {
  Alert,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  MenuItem,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";
import { useState } from "react";

import {
  decideCategoryPrice,
  getRegistration,
  type CategoryApproval,
  type RegistrationDetail,
} from "../api";
import IsoDateField from "./IsoDateField";

const moneyCell = {
  textAlign: "right" as const,
  fontVariantNumeric: "tabular-nums",
};

const STATUSES = [
  { value: "approved", label: "Approved: every product gets its price" },
  {
    value: "partially_approved",
    label: "Partly approved: only some products",
  },
  {
    value: "changes_requested",
    label: "Changes requested: the partner must fix something",
  },
  { value: "rejected", label: "Rejected" },
];

function money(value: string | number | null | undefined) {
  if (value === null || value === undefined || value === "") return "-";
  return Number(value).toLocaleString("en-PH", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

type Props = {
  approval: CategoryApproval | null;
  registration: RegistrationDetail;
  csrfToken: string;
  onClose: () => void;
  onSaved: (updated: RegistrationDetail) => void;
};

export default function PriceDecisionDialog({
  approval,
  registration,
  csrfToken,
  onClose,
  onSaved,
}: Props) {
  // The parent gives this box a new key for each approval, so these start fresh
  // each time it opens and survive the deal page reloading after a save.
  const [status, setStatus] = useState(
    !approval || approval.status === "pending" ? "approved" : approval.status,
  );
  const [reason, setReason] = useState(approval?.rationale ?? "");
  const [validUntil, setValidUntil] = useState(approval?.valid_until ?? "");
  const [prices, setPrices] = useState<Record<number, string>>(() =>
    Object.fromEntries(
      registration.items
        .filter((item) => item.id !== undefined && item.approved_unit_price)
        .map((item) => [item.id as number, String(item.approved_unit_price)]),
    ),
  );
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [warnings, setWarnings] = useState<string[]>([]);

  const items = registration.items.filter(
    (item) => item.id !== undefined && approval?.item_ids?.includes(item.id),
  );

  const priced = status === "approved" || status === "partially_approved";
  const filled = items.filter((item) => prices[item.id as number]?.trim());
  const pricesReady =
    !priced ||
    (status === "approved"
      ? filled.length === items.length
      : filled.length > 0);
  const canSave = reason.trim().length >= 5 && pricesReady && !saving;

  const save = async () => {
    if (!approval) return;
    setSaving(true);
    setError("");
    try {
      const result = await decideCategoryPrice(
        approval.id,
        {
          version: approval.version,
          status,
          rationale: reason.trim(),
          valid_until: priced && validUntil ? validUntil : null,
          approved_prices: priced
            ? Object.fromEntries(
                filled.map((item) => [
                  String(item.id),
                  prices[item.id as number].trim(),
                ]),
              )
            : {},
        },
        csrfToken,
      );
      onSaved(await getRegistration(registration.id));
      if (result.price_warnings?.length) setWarnings(result.price_warnings);
      else onClose();
    } catch (failure) {
      setError(
        failure instanceof Error
          ? failure.message
          : "The price decision could not be saved.",
      );
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog
      open={approval !== null}
      onClose={() => !saving && onClose()}
      fullWidth
      maxWidth="md"
    >
      <DialogTitle>Decide the {approval?.category} price</DialogTitle>
      <DialogContent>
        {warnings.length > 0 ? (
          <Stack spacing={1} sx={{ mt: 1 }}>
            <Alert severity="success">The price decision is saved.</Alert>
            {warnings.map((warning) => (
              <Alert severity="warning" key={warning}>
                {warning}
              </Alert>
            ))}
            <Typography variant="body2" color="text.secondary">
              Rank 1 gets the best price, and everyone after rank 1 gets the
              same price. If this is an exception, you can leave it. Otherwise,
              open the decision again and change the price.
            </Typography>
          </Stack>
        ) : (
          <Stack spacing={2} sx={{ mt: 1 }}>
            <Box
              sx={{ p: 1.5, bgcolor: "action.hover", borderRadius: 1 }}
              aria-label="Rank and prices on this project"
            >
              <Typography variant="body2">
                <strong>Rank on this project:</strong>{" "}
                {approval?.rank_text ?? "Not ranked"}
              </Typography>
              <Typography variant="body2" sx={{ mt: 0.5 }}>
                <strong>Approved prices on this project:</strong>{" "}
                {approval?.project_prices?.length ? "" : "None yet"}
              </Typography>
              {(approval?.project_prices ?? []).map((row) => (
                <Typography
                  variant="body2"
                  key={`${row.reference}-${row.product}`}
                >
                  Rank {row.rank}: {row.company} ({row.reference}),{" "}
                  {row.product}: {row.price}
                </Typography>
              ))}
              <Typography
                variant="caption"
                color="text.secondary"
                component="div"
                sx={{ mt: 0.5 }}
              >
                Rank 1 gets the best price. Everyone after rank 1 gets the same
                price.
              </Typography>
            </Box>
            {error && <Alert severity="error">{error}</Alert>}
            <TextField
              select
              required
              label="Decision"
              value={status}
              onChange={(event) => setStatus(event.target.value)}
            >
              {STATUSES.map((option) => (
                <MenuItem key={option.value} value={option.value}>
                  {option.label}
                </MenuItem>
              ))}
            </TextField>
            {priced && (
              <>
                <Table size="small" aria-label="Approved prices">
                  <TableHead>
                    <TableRow>
                      <TableCell>Product</TableCell>
                      <TableCell sx={moneyCell}>Quantity</TableCell>
                      <TableCell sx={moneyCell}>List price</TableCell>
                      <TableCell sx={moneyCell}>Requested price</TableCell>
                      <TableCell sx={moneyCell}>Approved price</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {items.map((item) => (
                      <TableRow key={item.id}>
                        <TableCell>{item.display_name}</TableCell>
                        <TableCell sx={moneyCell}>{item.quantity}</TableCell>
                        <TableCell sx={moneyCell}>
                          {money(item.list_unit_price)}
                        </TableCell>
                        <TableCell sx={moneyCell}>
                          {money(item.requested_unit_price)}
                        </TableCell>
                        <TableCell sx={moneyCell}>
                          <TextField
                            size="small"
                            type="number"
                            value={prices[item.id as number] ?? ""}
                            onChange={(event) =>
                              setPrices((current) => ({
                                ...current,
                                [item.id as number]: event.target.value,
                              }))
                            }
                            slotProps={{
                              htmlInput: {
                                min: 0,
                                step: "0.01",
                                style: { textAlign: "right" },
                                "aria-label": `Approved price for ${item.display_name}`,
                              },
                            }}
                          />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
                <IsoDateField
                  label="Valid until"
                  value={validUntil}
                  onChange={setValidUntil}
                  required={false}
                  helperText="Leave it empty for 90 days from today."
                />
              </>
            )}
            <TextField
              required
              fullWidth
              multiline
              minRows={3}
              label="Reason"
              helperText="At least 5 characters. The partner can read it."
              value={reason}
              onChange={(event) => setReason(event.target.value)}
            />
          </Stack>
        )}
      </DialogContent>
      <DialogActions>
        {warnings.length > 0 ? (
          <Button variant="contained" onClick={onClose}>
            Close
          </Button>
        ) : (
          <>
            <Button onClick={onClose} disabled={saving}>
              Cancel
            </Button>
            <Button variant="contained" disabled={!canSave} onClick={save}>
              Save decision
            </Button>
          </>
        )}
      </DialogActions>
    </Dialog>
  );
}
