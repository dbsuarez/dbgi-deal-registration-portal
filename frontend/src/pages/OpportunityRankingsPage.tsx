import ArrowDownwardIcon from "@mui/icons-material/ArrowDownward";
import ArrowUpwardIcon from "@mui/icons-material/ArrowUpward";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import RefreshIcon from "@mui/icons-material/Refresh";
import SearchIcon from "@mui/icons-material/Search";
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Container,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  InputAdornment,
  Link,
  List,
  ListItem,
  ListItemText,
  Stack,
  TablePagination,
  TextField,
  Typography,
} from "@mui/material";
import { DataGrid, type GridColDef } from "@mui/x-data-grid";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
  decideRankingTie,
  getOpportunityRankings,
  type OpportunityRanking,
  type RankingEntry,
} from "../api";
import { useSession } from "../session";
import MergeProjectDialog from "./MergeProjectDialog";

type RankingRow = RankingEntry & {
  id: string;
  scope_id: number;
  opportunity_title: string;
  scope_name: string;
  participant_count: number;
};

function formatDateTime(value: string) {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Manila",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).formatToParts(new Date(value));
  const part = (type: Intl.DateTimeFormatPartTypes) =>
    parts.find((item) => item.type === type)?.value ?? "";
  return `${part("year")}-${part("month")}-${part("day")} ${part("hour")}:${part("minute")}`;
}

function flattenRankings(rankings: OpportunityRanking[]): RankingRow[] {
  return rankings.flatMap((ranking) =>
    ranking.entries.map((entry) => ({
      ...entry,
      id: `${ranking.scope_id}-${entry.registration_id}`,
      scope_id: ranking.scope_id,
      opportunity_title: ranking.opportunity_title,
      scope_name: ranking.scope_name,
      participant_count: ranking.participant_count,
    })),
  );
}

export default function OpportunityRankingsPage() {
  const session = useSession();
  const [rows, setRows] = useState<RankingRow[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [refreshKey, setRefreshKey] = useState(0);
  const [explanationOpen, setExplanationOpen] = useState(false);
  const [mergeSource, setMergeSource] = useState<{
    scope_id: number;
    label: string;
  } | null>(null);
  const explanationCloseRef = useRef<HTMLButtonElement>(null);
  const [paginationModel, setPaginationModel] = useState({
    page: 0,
    pageSize: 25,
  });

  useEffect(() => {
    const timeout = window.setTimeout(() => {
      setDebouncedSearch(search);
      setPaginationModel((current) => ({ ...current, page: 0 }));
    }, 300);
    return () => window.clearTimeout(timeout);
  }, [search]);

  useEffect(() => {
    const controller = new AbortController();
    // oxlint-disable-next-line react/set-state-in-effect
    setLoading(true);
    setError("");
    getOpportunityRankings(
      paginationModel.page,
      paginationModel.pageSize,
      debouncedSearch,
      controller.signal,
    )
      .then((result) => {
        setRows(flattenRankings(result.items));
        setTotal(result.total);
      })
      .catch((reason: unknown) => {
        if (reason instanceof DOMException && reason.name === "AbortError")
          return;
        setError(
          reason instanceof Error
            ? reason.message
            : "Rankings could not be loaded.",
        );
      })
      .finally(() => setLoading(false));
    return () => controller.abort();
  }, [debouncedSearch, paginationModel, refreshKey]);

  const [tieRows, setTieRows] = useState<RankingRow[] | null>(null);
  const [tieReason, setTieReason] = useState("");
  const [decidingTie, setDecidingTie] = useState(false);
  const [tieError, setTieError] = useState("");

  const openTie = useCallback(
    (row: RankingRow) => {
      setTieRows(
        rows
          .filter(
            (other) =>
              other.scope_id === row.scope_id &&
              other.original_submitted_at === row.original_submitted_at,
          )
          .sort((a, b) => a.rank - b.rank),
      );
      setTieReason(row.tie_reason ?? "");
      setTieError("");
    },
    [rows],
  );

  const moveTieRow = (index: number, change: number) => {
    setTieRows((current) => {
      if (!current) return current;
      const next = [...current];
      [next[index], next[index + change]] = [next[index + change], next[index]];
      return next;
    });
  };

  const saveTie = async () => {
    if (!tieRows) return;
    setDecidingTie(true);
    setTieError("");
    try {
      await decideRankingTie(
        tieRows[0].scope_id,
        {
          order: tieRows.map((row) => row.registration_id),
          reason: tieReason.trim(),
        },
        session.csrf_token,
      );
      setTieRows(null);
      setRefreshKey((value) => value + 1);
    } catch (reason) {
      setTieError(
        reason instanceof Error ? reason.message : "The decision failed.",
      );
    } finally {
      setDecidingTie(false);
    }
  };

  const columns = useMemo<GridColDef<RankingRow>[]>(
    () => [
      {
        field: "opportunity_title",
        headerName: "Opportunity",
        minWidth: 260,
        flex: 1,
      },
      {
        field: "scope_name",
        headerName: "Ranking scope",
        minWidth: 220,
        flex: 1,
      },
      {
        field: "rank",
        headerName: "Rank",
        width: 150,
        align: "right",
        headerAlign: "right",
        renderCell: ({ row }) =>
          row.is_tied
            ? `Tied ${row.rank}`
            : row.tie_decided
              ? `${row.rank} (tie decided)`
              : row.rank,
      },
      ...(session.is_dbgi_admin
        ? [{ field: "company_name", headerName: "Company", minWidth: 180 }]
        : []),
      {
        field: "reference",
        headerName: "Registration",
        minWidth: 150,
        renderCell: ({ row }) => (
          <Link href={`/registrations/${row.registration_id}/`}>
            {row.reference}
          </Link>
        ),
      },
      {
        field: "original_submitted_at",
        headerName: "Eligible since",
        minWidth: 180,
        valueFormatter: (value: string) => formatDateTime(value),
      },
      {
        field: "participant_count",
        headerName: "Companies",
        width: 120,
        align: "right",
        headerAlign: "right",
      },
      ...(session.is_dbgi_admin
        ? [
            {
              field: "merge_action",
              headerName: "Project",
              minWidth: 110,
              sortable: false,
              renderCell: ({ row }: { row: RankingRow }) => (
                <Button
                  size="small"
                  onClick={() =>
                    setMergeSource({
                      scope_id: row.scope_id,
                      label: `${row.opportunity_title} | ${row.scope_name}`,
                    })
                  }
                >
                  Merge
                </Button>
              ),
            },
            {
              field: "tie_action",
              headerName: "Tie",
              minWidth: 130,
              sortable: false,
              renderCell: ({ row }: { row: RankingRow }) =>
                row.is_tied || row.tie_decided ? (
                  <Button size="small" onClick={() => openTie(row)}>
                    {row.is_tied ? "Decide tie" : "Change"}
                  </Button>
                ) : null,
            },
          ]
        : []),
    ],
    [session.is_dbgi_admin, openTie],
  );

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Stack direction="row" spacing={1} alignItems="center">
        <Box sx={{ flexGrow: 1 }}>
          <Typography variant="overline" color="text.secondary">
            Confirmed opportunity scopes
          </Typography>
          <Typography variant="h1">Opportunity rankings</Typography>
          <Typography color="text.secondary">
            {session.is_dbgi_admin
              ? "Compare company priority within each confirmed opportunity or lot."
              : "View your company’s confirmed position without exposing other companies."}
          </Typography>
        </Box>
        <IconButton
          aria-label="Explain opportunity rankings"
          onClick={() => setExplanationOpen(true)}
        >
          <InfoOutlinedIcon />
        </IconButton>
      </Stack>

      {!session.is_dbgi_admin && (
        <Alert severity="info" sx={{ mt: 3 }}>
          Only your company’s confirmed rank is shown. Other participating
          companies and their registrations remain private.
        </Alert>
      )}

      <Stack direction={{ xs: "column", sm: "row" }} spacing={2} sx={{ my: 3 }}>
        <TextField
          label="Search opportunities"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          sx={{ width: { xs: "100%", sm: 360 } }}
          slotProps={{
            input: {
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            },
          }}
        />
        <Button
          variant="outlined"
          startIcon={loading ? <CircularProgress size={16} /> : <RefreshIcon />}
          disabled={loading}
          onClick={() => setRefreshKey((value) => value + 1)}
        >
          Refresh
        </Button>
      </Stack>

      {error && <Alert severity="error">{error}</Alert>}
      <Box sx={{ width: "100%" }}>
        <DataGrid
          rows={rows}
          columns={columns}
          loading={loading}
          hideFooter
          disableRowSelectionOnClick
          autoHeight
          localeText={{ noRowsLabel: "No confirmed rankings are available." }}
          sx={{ minHeight: 320 }}
        />
        <TablePagination
          component="div"
          count={total}
          page={paginationModel.page}
          rowsPerPage={paginationModel.pageSize}
          rowsPerPageOptions={[10, 25, 50, 100]}
          labelRowsPerPage="Opportunities per page"
          onPageChange={(_, page) =>
            setPaginationModel((current) => ({ ...current, page }))
          }
          onRowsPerPageChange={(event) =>
            setPaginationModel({
              page: 0,
              pageSize: Number(event.target.value),
            })
          }
        />
      </Box>

      <Dialog
        open={tieRows !== null}
        onClose={() => !decidingTie && setTieRows(null)}
        fullWidth
        maxWidth="sm"
      >
        <DialogTitle>Decide the tied ranking</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            These registrations have the same submission time. Put them in rank
            order, first place at the top. Companies see only their own rank,
            not your reason.
          </Typography>
          {tieError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {tieError}
            </Alert>
          )}
          <List dense sx={{ mb: 1 }}>
            {(tieRows ?? []).map((row, index) => (
              <ListItem
                key={row.id}
                divider
                secondaryAction={
                  <>
                    <IconButton
                      aria-label={`Move ${row.company_name} up`}
                      disabled={index === 0}
                      onClick={() => moveTieRow(index, -1)}
                    >
                      <ArrowUpwardIcon />
                    </IconButton>
                    <IconButton
                      aria-label={`Move ${row.company_name} down`}
                      disabled={index === (tieRows ?? []).length - 1}
                      onClick={() => moveTieRow(index, 1)}
                    >
                      <ArrowDownwardIcon />
                    </IconButton>
                  </>
                }
              >
                <ListItemText
                  primary={`${index + 1}. ${row.company_name}`}
                  secondary={row.reference}
                />
              </ListItem>
            ))}
          </List>
          <TextField
            required
            fullWidth
            multiline
            minRows={3}
            label="Reason for this order"
            helperText="At least 5 characters. Only DBGI sees this."
            value={tieReason}
            onChange={(event) => setTieReason(event.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTieRows(null)} disabled={decidingTie}>
            Cancel
          </Button>
          <Button
            variant="contained"
            disabled={decidingTie || tieReason.trim().length < 5}
            onClick={saveTie}
          >
            Save order
          </Button>
        </DialogActions>
      </Dialog>

      <MergeProjectDialog
        source={mergeSource}
        csrfToken={session.csrf_token}
        onClose={() => setMergeSource(null)}
        onMerged={() => {
          setMergeSource(null);
          setRefreshKey((value) => value + 1);
        }}
      />

      <Dialog
        open={explanationOpen}
        onClose={() => setExplanationOpen(false)}
        slotProps={{
          transition: {
            onEntered: () => explanationCloseRef.current?.focus(),
          },
        }}
      >
        <DialogTitle>How ranking works</DialogTitle>
        <DialogContent>
          <Typography paragraph>
            Rankings are calculated separately for each confirmed opportunity or
            lot. Each company appears once using its earliest eligible
            registration time.
          </Typography>
          <Typography paragraph>
            Earlier original eligible timestamps receive the higher position.
            Review time, later edits, and user-entered project dates do not
            replace that timestamp.
          </Typography>
          <Typography>
            Registrations with the exact same timestamp share a rank and are
            marked as tied until DBGI decides their order. If DBGI merges two
            projects, it can also set the order for that case.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button
            ref={explanationCloseRef}
            onClick={() => setExplanationOpen(false)}
          >
            Close
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}
