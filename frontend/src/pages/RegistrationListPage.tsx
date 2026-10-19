import AddIcon from "@mui/icons-material/Add";
import RefreshIcon from "@mui/icons-material/Refresh";
import SearchIcon from "@mui/icons-material/Search";
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Container,
  InputAdornment,
  Link,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import {
  DataGrid,
  type GridColDef,
  type GridSortModel,
} from "@mui/x-data-grid";
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import { getRegistrations, type RegistrationListItem } from "../api";
import { useSession } from "../session";

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

export default function RegistrationListPage() {
  const session = useSession();
  const navigate = useNavigate();
  const [rows, setRows] = useState<RegistrationListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [paginationModel, setPaginationModel] = useState({
    page: 0,
    pageSize: 25,
  });
  const [sortModel, setSortModel] = useState<GridSortModel>([
    { field: "created_at", sort: "desc" },
  ]);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    const timeout = window.setTimeout(() => {
      setDebouncedSearch(search);
      setPaginationModel((current) => ({ ...current, page: 0 }));
    }, 300);
    return () => window.clearTimeout(timeout);
  }, [search]);

  useEffect(() => {
    const controller = new AbortController();
    const activeSort = sortModel[0];
    const sortField =
      activeSort?.field === "company_name"
        ? "company__name"
        : activeSort?.field;
    const sort = activeSort
      ? `${activeSort.sort === "desc" ? "-" : ""}${sortField}`
      : "-created_at";
    // This effect starts a new server request whenever its query state changes.
    // oxlint-disable-next-line react/set-state-in-effect
    setLoading(true);
    setError("");
    getRegistrations(
      paginationModel.page,
      paginationModel.pageSize,
      debouncedSearch,
      sort,
      controller.signal,
    )
      .then((result) => {
        setRows(result.items);
        setTotal(result.total);
      })
      .catch((reason: unknown) => {
        if (reason instanceof DOMException && reason.name === "AbortError")
          return;
        setError(
          reason instanceof Error
            ? reason.message
            : "Registrations could not be loaded.",
        );
      })
      .finally(() => setLoading(false));
    return () => controller.abort();
  }, [debouncedSearch, paginationModel, refreshKey, sortModel]);

  const columns = useMemo<GridColDef<RegistrationListItem>[]>(
    () => [
      {
        field: "reference",
        headerName: "Reference",
        minWidth: 140,
        renderCell: ({ row }) => (
          <Link href={`/registrations/${row.id}/`}>{row.reference}</Link>
        ),
      },
      { field: "project_title", headerName: "Project", minWidth: 220, flex: 1 },
      ...(session.is_dbgi_admin
        ? [{ field: "company_name", headerName: "Company", minWidth: 180 }]
        : []),
      {
        field: "end_user_name",
        headerName: "End user",
        minWidth: 200,
        flex: 1,
      },
      {
        field: "status_label",
        headerName: "Status",
        minWidth: 140,
        sortable: false,
        renderCell: ({ value }) => (
          <Chip label={value} size="small" variant="outlined" />
        ),
      },
      {
        field: "needs_review",
        headerName: "Review",
        minWidth: 150,
        sortable: false,
        renderCell: ({ value }) =>
          value ? (
            <Chip label="Review required" size="small" color="warning" />
          ) : null,
      },
      {
        field: "created_at",
        headerName: "Submitted",
        minWidth: 170,
        valueFormatter: (value: string) => formatDateTime(value),
      },
      {
        field: "actions",
        type: "actions",
        headerName: "Actions",
        getActions: ({ row }) => [
          <Button key="view" href={`/registrations/${row.id}/`} size="small">
            View
          </Button>,
        ],
      },
    ],
    [session.is_dbgi_admin],
  );

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Stack
        direction={{ xs: "column", sm: "row" }}
        spacing={2}
        alignItems="flex-start"
      >
        <Box sx={{ flexGrow: 1 }}>
          <Typography variant="overline" color="text.secondary">
            Project pipeline
          </Typography>
          <Typography variant="h1">Deal registrations</Typography>
          <Typography color="text.secondary">
            Review registrations and their current status.
          </Typography>
        </Box>
        {!session.is_dbgi_admin && (
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => navigate("/registrations/new/")}
          >
            New registration
          </Button>
        )}
      </Stack>
      <Stack direction={{ xs: "column", sm: "row" }} spacing={2} sx={{ my: 3 }}>
        <TextField
          label="Search registrations"
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
          onClick={() => setRefreshKey((value) => value + 1)}
          disabled={loading}
        >
          Refresh
        </Button>
      </Stack>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      <Box sx={{ height: 620, bgcolor: "background.paper" }}>
        <DataGrid
          rows={rows}
          columns={columns}
          rowCount={total}
          loading={loading}
          paginationMode="server"
          sortingMode="server"
          paginationModel={paginationModel}
          onPaginationModelChange={setPaginationModel}
          sortModel={sortModel}
          onSortModelChange={setSortModel}
          pageSizeOptions={[10, 25, 50, 100]}
          disableRowSelectionOnClick
          onRowDoubleClick={({ row }) => navigate(`/registrations/${row.id}/`)}
          showToolbar
          sx={{ border: 0 }}
        />
      </Box>
    </Container>
  );
}
