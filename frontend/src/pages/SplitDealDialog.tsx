import {
  Alert,
  Button,
  Checkbox,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  FormControlLabel,
  FormGroup,
  FormLabel,
  MenuItem,
  Radio,
  RadioGroup,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  getOpportunityScopes,
  splitRegistration,
  type OpportunityScope,
  type RegistrationDetail,
} from "../api";

type Props = {
  open: boolean;
  registration: RegistrationDetail;
  csrfToken: string;
  onClose: () => void;
};

export default function SplitDealDialog({
  open,
  registration,
  csrfToken,
  onClose,
}: Props) {
  const navigate = useNavigate();
  const [itemIds, setItemIds] = useState<number[]>([]);
  const [scopes, setScopes] = useState<OpportunityScope[]>([]);
  const [targetId, setTargetId] = useState("");
  const [lotName, setLotName] = useState("");
  const [priceAction, setPriceAction] = useState<"keep" | "review">("keep");
  const [reason, setReason] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!open) return;
    const controller = new AbortController();
    getOpportunityScopes(controller.signal)
      .then(setScopes)
      .catch(() => setScopes([]));
    return () => controller.abort();
  }, [open]);

  const savedItems = registration.items.flatMap((item) =>
    item.id === undefined ? [] : [{ ...item, id: item.id }],
  );
  const currentScope = scopes.find(
    (scope) => scope.id === registration.opportunity_scope_id,
  );
  const otherLots = scopes.filter(
    (scope) =>
      scope.opportunity_id === currentScope?.opportunity_id &&
      scope.id !== registration.opportunity_scope_id,
  );
  const hasTarget = Boolean(targetId) !== Boolean(lotName.trim());
  const canSave =
    itemIds.length > 0 &&
    itemIds.length < registration.items.length &&
    hasTarget &&
    reason.trim().length >= 5 &&
    !saving;

  const save = async () => {
    setSaving(true);
    setError("");
    try {
      const created = await splitRegistration(
        registration.id,
        {
          item_ids: itemIds,
          target_scope_id: targetId ? Number(targetId) : null,
          new_lot_name: lotName.trim(),
          reason: reason.trim(),
          price_action: priceAction,
        },
        csrfToken,
      );
      navigate(`/registrations/${created.id}/`);
      onClose();
    } catch (failure) {
      setError(
        failure instanceof Error
          ? failure.message
          : "The deal could not be split.",
      );
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog
      open={open}
      onClose={() => !saving && onClose()}
      fullWidth
      maxWidth="sm"
    >
      <DialogTitle>Split this deal</DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Use this when one deal covers separate lots. The products you choose
          move to a new deal for the same company. The new deal keeps the
          original submission time.
        </Typography>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        <Stack spacing={2}>
          <FormControl component="fieldset">
            <FormLabel component="legend">Products to move</FormLabel>
            <FormGroup>
              {savedItems.map((item) => (
                <FormControlLabel
                  key={item.id}
                  label={`${item.product_name ?? item.non_catalog_name} (${item.quantity})`}
                  control={
                    <Checkbox
                      checked={itemIds.includes(item.id)}
                      onChange={(event) =>
                        setItemIds((current) =>
                          event.target.checked
                            ? [...current, item.id]
                            : current.filter((id) => id !== item.id),
                        )
                      }
                    />
                  }
                />
              ))}
            </FormGroup>
          </FormControl>
          <TextField
            label="New lot name"
            helperText="For example: Lot 2. Or choose an existing lot below."
            value={lotName}
            disabled={Boolean(targetId)}
            onChange={(event) => setLotName(event.target.value)}
          />
          {otherLots.length > 0 && (
            <TextField
              select
              label="Existing lot"
              value={targetId}
              disabled={Boolean(lotName.trim())}
              onChange={(event) => setTargetId(event.target.value)}
            >
              <MenuItem value="">None</MenuItem>
              {otherLots.map((scope) => (
                <MenuItem key={scope.id} value={String(scope.id)}>
                  {scope.name}
                </MenuItem>
              ))}
            </TextField>
          )}
          <FormControl>
            <FormLabel>Decided prices</FormLabel>
            <RadioGroup
              value={priceAction}
              onChange={(event) =>
                setPriceAction(event.target.value as "keep" | "review")
              }
            >
              <FormControlLabel
                value="keep"
                control={<Radio />}
                label="Keep them"
              />
              <FormControlLabel
                value="review"
                control={<Radio />}
                label="Send them back for review, on both deals"
              />
            </RadioGroup>
          </FormControl>
          <TextField
            required
            fullWidth
            multiline
            minRows={3}
            label="Reason"
            helperText="At least 5 characters. Only DBGI sees this."
            value={reason}
            onChange={(event) => setReason(event.target.value)}
          />
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={saving}>
          Cancel
        </Button>
        <Button variant="contained" disabled={!canSave} onClick={save}>
          Split deal
        </Button>
      </DialogActions>
    </Dialog>
  );
}
