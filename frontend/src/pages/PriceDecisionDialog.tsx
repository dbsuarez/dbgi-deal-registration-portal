import {
  Alert,
  Box,
  Button,
  Checkbox,
  FormControlLabel,
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
  RequestError,
  decideCategoryPrice,
  getRegistration,
  type CategoryApproval,
  type RegistrationDetail,
} from "../api";
import { useSession } from "../session";
import { example } from "./exampleText";
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
    label: "Ask for a new price: the partner must change it",
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
  const { is_debug: isDebug } = useSession();
  // The parent gives this box a new key for each approval, so these start fresh
  // each time it opens and survive the deal page reloading after a save.
  const [status, setStatus] = useState(
    !approval || ["pending", "owner_review"].includes(approval.status)
      ? "approved"
      : approval.status,
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
  const [savedNote, setSavedNote] = useState("");
  // Shown by the server before saving: confirm them, or change the price.
  const [rankWarnings, setRankWarnings] = useState<string[]>([]);
  const [rankConfirmed, setRankConfirmed] = useState(false);
  const [costWarnings, setCostWarnings] = useState<string[]>([]);
  const [costConfirmed, setCostConfirmed] = useState(false);
  const isOwner = Boolean(approval?.is_owner);
  const limit = Number(approval?.discount_limit_percent ?? 0);
  const costs = Object.fromEntries(
    (approval?.item_costs ?? []).map((row) => [row.item_id, row]),
  );
  const changePrice = (itemId: number, value: string) => {
    setPrices((current) => ({ ...current, [itemId]: value }));
    // A new price needs a new check.
    setRankWarnings([]);
    setRankConfirmed(false);
    setCostWarnings([]);
    setCostConfirmed(false);
  };
  const discount = (itemId: number, list: unknown) => {
    const price = Number(prices[itemId]);
    const listPrice = Number(list);
    if (!prices[itemId]?.trim() || !listPrice) return null;
    return ((listPrice - price) * 100) / listPrice;
  };

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
  const overLimit =
    priced &&
    !isOwner &&
    items.some(
      (item) =>
        (discount(item.id as number, item.list_unit_price) ?? 0) > limit,
    );
  const canSave =
    reason.trim().length >= 5 &&
    pricesReady &&
    !saving &&
    (rankWarnings.length === 0 || rankConfirmed) &&
    (costWarnings.length === 0 || costConfirmed);

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
          rank_exception_confirmed: rankConfirmed,
          below_cost_confirmed: costConfirmed,
        },
        csrfToken,
      );
      onSaved(await getRegistration(registration.id));
      if (result.status === "owner_review") {
        setSavedNote(
          "Sent to the owner for approval, because the discount is above the admin limit. The partner still sees the price as pending.",
        );
      } else if (result.price_warnings?.length) {
        setWarnings(result.price_warnings);
        setSavedNote(
          "The price decision is saved, as an exception you confirmed.",
        );
      } else onClose();
    } catch (failure) {
      const messages =
        failure instanceof RequestError
          ? (failure.details ?? []).map((detail) => detail.message)
          : [];
      if (
        failure instanceof RequestError &&
        failure.code === "rank_rule_needs_confirmation"
      ) {
        setRankWarnings(messages);
        setError("");
      } else if (
        failure instanceof RequestError &&
        failure.code === "below_cost_needs_confirmation"
      ) {
        setCostWarnings(messages);
        setError("");
      } else {
        setError(
          failure instanceof Error
            ? failure.message
            : "The price decision could not be saved.",
        );
      }
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
        {savedNote ? (
          <Stack spacing={1} sx={{ mt: 1 }}>
            <Alert severity="success">{savedNote}</Alert>
            {warnings.map((warning) => (
              <Alert severity="warning" key={warning}>
                {warning}
              </Alert>
            ))}
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
            {approval?.status === "owner_review" && (
              <Alert severity="info">
                Waiting for the owner. {approval.proposed_by_name ?? "An admin"}{" "}
                proposed: {approval.proposed_status_label}, with a discount
                above the admin limit of {limit}%.
                {isOwner
                  ? " You can approve it, change the price, or choose another decision."
                  : ""}
              </Alert>
            )}
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
                      <TableCell sx={moneyCell}>Landed cost</TableCell>
                      <TableCell sx={moneyCell}>Approved price</TableCell>
                      <TableCell sx={moneyCell}>Discount</TableCell>
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
                          {costs[item.id as number]?.landed_cost
                            ? money(costs[item.id as number]?.landed_cost)
                            : "Not entered"}
                        </TableCell>
                        <TableCell sx={moneyCell}>
                          <TextField
                            size="small"
                            type="number"
                            value={prices[item.id as number] ?? ""}
                            error={
                              Boolean(costs[item.id as number]?.landed_cost) &&
                              Boolean(prices[item.id as number]?.trim()) &&
                              Number(prices[item.id as number]) <
                                Number(costs[item.id as number]?.landed_cost)
                            }
                            onChange={(event) =>
                              changePrice(item.id as number, event.target.value)
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
                        <TableCell sx={moneyCell}>
                          {discount(item.id as number, item.list_unit_price) ===
                          null
                            ? "-"
                            : `${(discount(item.id as number, item.list_unit_price) ?? 0).toFixed(2)}%`}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
                <Typography variant="caption" color="text.secondary">
                  Discount is from the list price. Admins can approve up to{" "}
                  {limit}%; a bigger discount goes to the owner. No price can go
                  below the landed cost.
                </Typography>
                {overLimit && (
                  <Alert severity="info">
                    The discount is above {limit}%, so saving sends it to the
                    owner for approval.
                  </Alert>
                )}
                {costWarnings.length > 0 && (
                  <Alert severity="error">
                    {costWarnings.map((warning) => (
                      <div key={warning}>{warning}</div>
                    ))}
                    <FormControlLabel
                      control={
                        <Checkbox
                          checked={costConfirmed}
                          onChange={(event) =>
                            setCostConfirmed(event.target.checked)
                          }
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
                          onChange={(event) =>
                            setRankConfirmed(event.target.checked)
                          }
                        />
                      }
                      label="I confirm this exception to the rank rule."
                    />
                  </Alert>
                )}
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
              {...example(
                status === "approved"
                  ? "Within the allowed discount."
                  : status === "partially_approved"
                    ? "Approved the printers only. The scanner needs a new quotation."
                    : status === "changes_requested"
                      ? "Your price is below what we can give. Please send a price of at least 9,200."
                      : "The requested price is below the allowed discount.",
                {
                  debug: isDebug,
                  onFill: setReason,
                  more:
                    status === "approved"
                      ? [
                          "Within the allowed discount.",
                          "Matches rank 1's price on this project.",
                          "Approved for this bid only.",
                        ]
                      : status === "partially_approved"
                        ? [
                            "Approved the printers only. The scanner needs a new quotation.",
                            "Approved the main items. The accessories stay at list price.",
                            "Only the printers are within the allowed discount.",
                          ]
                        : status === "changes_requested"
                          ? [
                              "Your price is below what we can give. Please send a price of at least 9,200.",
                              "Please lower the quantity to 15 units.",
                              "Please send a new price for the scanner.",
                            ]
                          : [
                              "The requested price is below the allowed discount.",
                              "This product is not part of the program.",
                              "The office's budget does not match the requested items.",
                            ],
                },
              )}
              value={reason}
              onChange={(event) => setReason(event.target.value)}
            />
          </Stack>
        )}
      </DialogContent>
      <DialogActions>
        {savedNote ? (
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
