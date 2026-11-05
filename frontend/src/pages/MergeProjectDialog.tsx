import ArrowDownwardIcon from "@mui/icons-material/ArrowDownward";
import ArrowUpwardIcon from "@mui/icons-material/ArrowUpward";
import {
  Alert,
  Button,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  FormControlLabel,
  FormLabel,
  IconButton,
  List,
  ListItem,
  ListItemText,
  MenuItem,
  Radio,
  RadioGroup,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useEffect, useState } from "react";

import {
  getMergePreview,
  getOpportunityScopes,
  mergeProject,
  type MergePreview,
  type MergePreviewRow,
  type OpportunityScope,
} from "../api";

type Props = {
  source: { scope_id: number; label: string } | null;
  csrfToken: string;
  onClose: () => void;
  onMerged: () => void;
};

export default function MergeProjectDialog({
  source,
  csrfToken,
  onClose,
  onMerged,
}: Props) {
  const [scopes, setScopes] = useState<OpportunityScope[]>([]);
  const [targetId, setTargetId] = useState("");
  const [preview, setPreview] = useState<MergePreview | null>(null);
  const [rows, setRows] = useState<MergePreviewRow[]>([]);
  const [priceAction, setPriceAction] = useState<"keep" | "review">("keep");
  const [reason, setReason] = useState("");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const sourceScopeId = source?.scope_id;

  useEffect(() => {
    if (sourceScopeId === undefined) return;
    const controller = new AbortController();
    // oxlint-disable-next-line react/set-state-in-effect
    setTargetId("");
    setPreview(null);
    setRows([]);
    setPriceAction("keep");
    setReason("");
    setError("");
    getOpportunityScopes(controller.signal)
      .then((items) =>
        setScopes(items.filter((scope) => scope.id !== sourceScopeId)),
      )
      .catch(() => setScopes([]));
    return () => controller.abort();
  }, [sourceScopeId]);

  useEffect(() => {
    if (sourceScopeId === undefined || !targetId) return;
    const controller = new AbortController();
    // oxlint-disable-next-line react/set-state-in-effect
    setLoading(true);
    setError("");
    getMergePreview(sourceScopeId, Number(targetId), controller.signal)
      .then((result) => {
        setPreview(result);
        setRows(result.rows);
      })
      .catch((failure) => {
        if (controller.signal.aborted) return;
        setPreview(null);
        setError(
          failure instanceof Error
            ? failure.message
            : "The preview could not load.",
        );
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [sourceScopeId, targetId]);

  const move = (index: number, change: number) => {
    setRows((current) => {
      const next = [...current];
      const [row] = next.splice(index, 1);
      next.splice(index + change, 0, row);
      return next;
    });
  };

  const save = async () => {
    if (sourceScopeId === undefined) return;
    setSaving(true);
    setError("");
    try {
      await mergeProject(
        sourceScopeId,
        {
          target_scope_id: Number(targetId),
          reason: reason.trim(),
          price_action: priceAction,
          order: rows.map((row) => row.registration_id),
        },
        csrfToken,
      );
      onMerged();
    } catch (failure) {
      setError(
        failure instanceof Error
          ? failure.message
          : "The projects could not be merged.",
      );
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog
      open={source !== null}
      onClose={() => !saving && onClose()}
      fullWidth
      maxWidth="sm"
    >
      <DialogTitle>Merge this project into another</DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Use this when you learn that two projects are the same tender. Deals
          from {source?.label} move to the project you choose. This cannot be
          undone.
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
            label="Merge into"
            value={targetId}
            onChange={(event) => setTargetId(event.target.value)}
          >
            {scopes.map((scope) => (
              <MenuItem key={scope.id} value={String(scope.id)}>
                {scope.label}
              </MenuItem>
            ))}
          </TextField>
          {loading && <CircularProgress size={24} />}
          {preview && (
            <>
              {!preview.same_end_user && (
                <Alert severity="warning">
                  These two projects have different end-users. Please check that
                  they really are the same tender.
                </Alert>
              )}
              <Typography variant="body2">
                {preview.deals_moving} deal(s) will move.{" "}
                {preview.decided_prices} price decision(s) already made. The
                project status will be {preview.target_project_status}.
              </Typography>
              <div>
                <FormLabel>New ranking, first place at the top</FormLabel>
                <Typography variant="body2" color="text.secondary">
                  This starts in order of original submission time. Change it
                  only if DBGI decides this case differently.
                </Typography>
                <List dense>
                  {rows.map((row, index) => (
                    <ListItem
                      key={row.registration_id}
                      divider
                      secondaryAction={
                        <>
                          <IconButton
                            aria-label={`Move ${row.company_name} up`}
                            disabled={index === 0}
                            onClick={() => move(index, -1)}
                          >
                            <ArrowUpwardIcon />
                          </IconButton>
                          <IconButton
                            aria-label={`Move ${row.company_name} down`}
                            disabled={index === rows.length - 1}
                            onClick={() => move(index, 1)}
                          >
                            <ArrowDownwardIcon />
                          </IconButton>
                        </>
                      }
                    >
                      <ListItemText
                        sx={{ pr: 10 }}
                        primary={`${index + 1}. ${row.company_name}`}
                        secondary={`${row.reference}, was rank ${row.current_rank} on ${row.current_project}`}
                      />
                    </ListItem>
                  ))}
                </List>
              </div>
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
                    label="Send the moved deals' prices back for review"
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
            </>
          )}
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={saving}>
          Cancel
        </Button>
        <Button
          variant="contained"
          disabled={!preview || saving || reason.trim().length < 5}
          onClick={save}
        >
          Merge projects
        </Button>
      </DialogActions>
    </Dialog>
  );
}
