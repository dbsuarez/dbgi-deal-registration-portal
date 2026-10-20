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
  Stack,
  TablePagination,
  TextField,
  Typography,
} from "@mui/material";
import { DataGrid, type GridColDef } from "@mui/x-data-grid";
import { useEffect, useMemo, useRef, useState } from "react";

import {
  getOpportunityRankings,
  type OpportunityRanking,
  type RankingEntry,
} from "../api";
import { useSession } from "../session";

type RankingRow = RankingEntry & {
  id: string;
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
        width: 100,
        align: "right",
        headerAlign: "right",
        renderCell: ({ row }) => (row.is_tied ? `Tied ${row.rank}` : row.rank),
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
    ],
    [session.is_dbgi_admin],
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
            marked as tied.
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
