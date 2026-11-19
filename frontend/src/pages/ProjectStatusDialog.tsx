import {
  Alert,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  MenuItem,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useEffect, useState } from "react";

import {
  changeProjectStatus,
  getRegistration,
  type RegistrationDetail,
} from "../api";
import { example } from "./exampleText";

const STATUSES = [
  { value: "upcoming", label: "Upcoming" },
  { value: "active", label: "Active" },
  { value: "on_hold", label: "On hold" },
  { value: "won", label: "Won" },
  { value: "lost", label: "Lost" },
  { value: "cancelled", label: "Cancelled" },
];

type Props = {
  open: boolean;
  registration: RegistrationDetail;
  csrfToken: string;
  onClose: () => void;
  onSaved: (updated: RegistrationDetail) => void;
};

export default function ProjectStatusDialog({
  open,
  registration,
  csrfToken,
  onClose,
  onSaved,
}: Props) {
  const [status, setStatus] = useState("active");
  const [reason, setReason] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!open) return;
    // oxlint-disable-next-line react/set-state-in-effect
    setStatus(registration.project_status ?? "active");
    setReason("");
    setError("");
  }, [open, registration.project_status]);

  const save = async () => {
    if (!registration.opportunity_id) return;
    setSaving(true);
    setError("");
    try {
      await changeProjectStatus(
        registration.opportunity_id,
        { status, reason: reason.trim() },
        csrfToken,
      );
      onSaved(await getRegistration(registration.id));
      onClose();
    } catch (failure) {
      setError(
        failure instanceof Error
          ? failure.message
          : "The project status could not be changed.",
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
      <DialogTitle>Change the project status</DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          This changes the project, so every deal linked to it shows the new
          status. Use <strong>On hold</strong> when a tender is postponed or
          will be posted again: partners keep their place for{" "}
          {registration.hold_limit_days ?? 60} days, then DBGI reviews the
          deals. A DBGI superuser can change that length in Portal settings.
        </Typography>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        <Stack spacing={2}>
          <TextField
            select
            required
            label="Project status"
            value={status}
            onChange={(event) => setStatus(event.target.value)}
          >
            {STATUSES.map((option) => (
              <MenuItem key={option.value} value={option.value}>
                {option.label}
              </MenuItem>
            ))}
          </TextField>
          <TextField
            required
            fullWidth
            multiline
            minRows={3}
            label="Reason"
            helperText="At least 5 characters. It is saved in each deal's Activity."
            {...example("The bidding was postponed.")}
            value={reason}
            onChange={(event) => setReason(event.target.value)}
          />
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={saving}>
          Cancel
        </Button>
        <Button
          variant="contained"
          disabled={saving || reason.trim().length < 5}
          onClick={save}
        >
          Change status
        </Button>
      </DialogActions>
    </Dialog>
  );
}
