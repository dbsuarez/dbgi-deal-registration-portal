import {
  Alert,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  TextField,
  Typography,
} from "@mui/material";
import { useState } from "react";

import { reopenRegistration, type RegistrationDetail } from "../api";
import { useSession } from "../session";
import { example } from "./exampleText";

type Props = {
  open: boolean;
  registration: RegistrationDetail;
  csrfToken: string;
  onClose: () => void;
  onSaved: (updated: RegistrationDetail) => void;
};

// DBGI reopens a cancelled deal, for example when the winner was disqualified.
export default function ReopenDealDialog({
  open,
  registration,
  csrfToken,
  onClose,
  onSaved,
}: Props) {
  const { is_debug: isDebug } = useSession();
  const [reason, setReason] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const save = async () => {
    setSaving(true);
    setError("");
    try {
      onSaved(
        await reopenRegistration(
          registration.id,
          { version: registration.version, reason: reason.trim() },
          csrfToken,
        ),
      );
    } catch (failure) {
      setError(
        failure instanceof Error
          ? failure.message
          : "The deal could not be reopened.",
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
      <DialogTitle>Reopen this deal?</DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          It goes back to the status it had before it was cancelled. It keeps
          its original submission time, so it takes back its place in the
          ranking. The company is told.
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
          autoFocus
          label="Reason"
          helperText="At least 5 characters. The company can read it."
          {...example("The winner was disqualified.", {
            debug: isDebug,
            onFill: setReason,
            more: [
              "The winner was disqualified.",
              "The winner backed out of the contract.",
              "The office posted the project again.",
            ],
          })}
          value={reason}
          onChange={(event) => setReason(event.target.value)}
        />
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
          Reopen deal
        </Button>
      </DialogActions>
    </Dialog>
  );
}
