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
import { useState } from "react";

import {
  closeRegistration,
  type CloseReason,
  type RegistrationDetail,
} from "../api";
import { useSession } from "../session";
import { example } from "./exampleText";

const REASONS: { value: CloseReason; label: string }[] = [
  { value: "another_company_won", label: "Another company won" },
  { value: "project_cancelled", label: "The project was cancelled" },
  { value: "stopped_pursuing", label: "The company stopped pursuing it" },
  { value: "other", label: "Other" },
];

export type CloseTarget = {
  id: number;
  version: number;
  reference: string;
  companyName?: string;
};

type Props = {
  // The deal to close; null keeps the box shut. The parent gives each target a new key.
  target: CloseTarget | null;
  isDbgi: boolean;
  csrfToken: string;
  onClose: () => void;
  onClosed: (updated: RegistrationDetail) => void;
};

export default function CloseDealDialog({
  target,
  isDbgi,
  csrfToken,
  onClose,
  onClosed,
}: Props) {
  const { is_debug: isDebug } = useSession();
  const [reason, setReason] = useState<CloseReason>(
    isDbgi ? "another_company_won" : "stopped_pursuing",
  );
  const [note, setNote] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const save = async () => {
    if (!target) return;
    setSaving(true);
    setError("");
    try {
      onClosed(
        await closeRegistration(
          target.id,
          { version: target.version, reason, note: note.trim() },
          csrfToken,
        ),
      );
    } catch (failure) {
      setError(
        failure instanceof Error
          ? failure.message
          : "The deal could not be cancelled.",
      );
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog
      open={target !== null}
      onClose={() => !saving && onClose()}
      fullWidth
      maxWidth="sm"
    >
      <DialogTitle>
        Cancel {target?.companyName ? `${target.companyName}'s` : "this"} deal?
      </DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {target?.reference} leaves the ranking and can no longer change.
          {isDbgi
            ? " The company is told, and can read your note. DBGI can reopen it later if needed."
            : " DBGI is told. Only DBGI can reopen it."}
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
            label="Why is it cancelled?"
            value={reason}
            onChange={(event) => setReason(event.target.value as CloseReason)}
          >
            {REASONS.map((option) => (
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
            autoFocus
            label={isDbgi ? "Note from the call" : "Reason"}
            helperText="At least 5 characters. The company and DBGI can read it."
            {...example(
              isDbgi
                ? "Called the company today. They will not continue."
                : "The office gave the project to another bidder.",
              {
                debug: isDebug,
                onFill: setNote,
                more: isDbgi
                  ? [
                      "Called the company today. They will not continue.",
                      "The company confirmed by email that another bidder won.",
                      "The office cancelled the project. The company agreed to close it.",
                    ]
                  : [
                      "The office gave the project to another bidder.",
                      "We decided not to bid on this project.",
                      "The office cancelled the bidding.",
                    ],
              },
            )}
            value={note}
            onChange={(event) => setNote(event.target.value)}
          />
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={saving}>
          Keep the deal
        </Button>
        <Button
          variant="contained"
          color="error"
          disabled={saving || note.trim().length < 5}
          onClick={save}
        >
          Cancel deal
        </Button>
      </DialogActions>
    </Dialog>
  );
}
