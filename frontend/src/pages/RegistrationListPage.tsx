import AddIcon from "@mui/icons-material/Add";
import FileUploadOutlinedIcon from "@mui/icons-material/FileUploadOutlined";
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
  type GridColumnVisibilityModel,
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

function ExportUpIcon() {
  return <FileUploadOutlinedIcon fontSize="small" />;
}

function loadGridPreference(key: string) {
  if (typeof localStorage?.getItem !== "function") return {};
  try {
    return JSON.parse(localStorage.getItem(key) ?? "{}");
  } catch {
    return {};
  }
}

export default function RegistrationListPage() {
  const session = useSession();
  const navigate = useNavigate();
  const [rows, setRows] = useState<RegistrationListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [grandTotal, setGrandTotal] = useState("0.00");
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
  const preferenceKey = `dbgi-registration-grid:${session.username}`;
  const [columnVisibilityModel, setColumnVisibilityModel] =
    useState<GridColumnVisibilityModel>(
      () => loadGridPreference(preferenceKey).visibility ?? {},
    );
  const [columnWidths, setColumnWidths] = useState<Record<string, number>>(
    () => loadGridPreference(preferenceKey).widths ?? {},
  );
  const [columnOrder, setColumnOrder] = useState<string[]>(
    () => loadGridPreference(preferenceKey).order ?? [],
  );

  useEffect(() => {
    if (typeof localStorage?.setItem !== "function") return;
    localStorage.setItem(
      preferenceKey,
      JSON.stringify({
        visibility: columnVisibilityModel,
        widths: columnWidths,
        order: columnOrder,
      }),
    );
  }, [columnOrder, columnVisibilityModel, columnWidths, preferenceKey]);

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
        setGrandTotal(result.grand_total ?? "0.00");
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

  const baseColumns = useMemo<GridColDef<RegistrationListItem>[]>(
    () => [
      {
        field: "reference",
        headerName: "Reference",
        minWidth: 140,
        renderCell: ({ row }) =>
          row.id === -1 ? (
            <Typography fontWeight={700}>Grand total</Typography>
          ) : (
            <Link href={`/registrations/${row.id}/`}>{row.reference}</Link>
          ),
      },
      { field: "project_title", headerName: "Project", minWidth: 220, flex: 1 },
      ...(session.is_dbgi_admin
        ? [{ field: "company_name", headerName: "Company", minWidth: 180 }]
        : []),
      {
        field: "end_user_name",
        headerName: "End-user",
        minWidth: 200,
        flex: 1,
      },
      {
        field: "status_label",
        headerName: "Registration status",
        minWidth: 140,
        sortable: false,
        renderCell: ({ row, value }) =>
          row.id === -1 ? null : (
            <Chip label={value} size="small" variant="outlined" />
          ),
      },
      {
        field: "project_status_label",
        headerName: "Project status",
        minWidth: 135,
        sortable: false,
        renderCell: ({ row, value }) =>
          row.id === -1 ? null : (
            <Chip label={value} size="small" variant="outlined" />
          ),
      },
      {
        field: "price_status_label",
        headerName: "Price status",
        minWidth: 150,
        sortable: false,
        renderCell: ({ row, value }) =>
          row.id === -1 ? null : (
            <Chip label={value} size="small" variant="outlined" />
          ),
      },
      {
        field: "total_requested_value",
        headerName: "Bid Total",
        minWidth: 150,
        sortable: false,
        align: "right",
        headerAlign: "right",
        renderCell: ({ row, value }) => (
          <Typography fontWeight={row.id === -1 ? 700 : 400}>
            {Number(value).toLocaleString("en-PH", {
              minimumFractionDigits: 2,
            })}
          </Typography>
        ),
      },
      {
        field: "bid_date",
        headerName: "Bid date",
        minWidth: 120,
        sortable: false,
      },
      {
        field: "age_days",
        headerName: "Age",
        minWidth: 90,
        sortable: false,
        align: "right",
        headerAlign: "right",
        valueFormatter: (value: number, row) =>
          row.id === -1 ? "" : `${value}d`,
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
        valueFormatter: (value: string, row) =>
          row.id === -1 ? "" : formatDateTime(value),
      },
      {
        field: "actions",
        type: "actions",
        headerName: "Actions",
        getActions: ({ row }) =>
          row.id === -1
            ? []
            : [
                <Button
                  key="view"
                  href={`/registrations/${row.id}/`}
                  size="small"
                >
                  View
                </Button>,
              ],
      },
    ],
    [session.is_dbgi_admin],
  );
  const columns = useMemo(() => {
    const positions = new Map(
      columnOrder.map((field, index) => [field, index]),
    );
    return baseColumns
      .map((column) => {
        const savedWidth = columnWidths[column.field];
        return {
          ...column,
          width: savedWidth ?? column.width,
          flex: savedWidth == null ? column.flex : undefined,
        };
      })
      .sort((left, right) => {
        const leftPosition = positions.get(left.field);
        const rightPosition = positions.get(right.field);
        if (leftPosition == null && rightPosition == null) return 0;
        if (leftPosition == null) return 1;
        if (rightPosition == null) return -1;
        return leftPosition - rightPosition;
      });
  }, [baseColumns, columnOrder, columnWidths]);

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
          rows={[
            ...rows,
            {
              id: -1,
              reference: "Grand total",
              project_title: "",
              company_name: "",
              end_user_name: "",
              end_user_id: null,
              end_user_status: null,
              end_user_status_label: null,
              status: "",
              status_label: "",
              project_status: null,
              project_status_label: "",
              price_status: "",
              price_status_label: "",
              total_requested_value: grandTotal,
              bid_date: "",
              age_days: 0,
              needs_review: false,
              created_at: "",
              version: 0,
            },
          ]}
          columns={columns}
          columnVisibilityModel={columnVisibilityModel}
          onColumnVisibilityModelChange={setColumnVisibilityModel}
          onColumnWidthChange={({ colDef, width }) =>
            setColumnWidths((current) => ({
              ...current,
              [colDef.field]: width,
            }))
          }
          onColumnOrderChange={({ oldIndex, targetIndex }) =>
            setColumnOrder((current) => {
              const fields = current.length
                ? [...current]
                : columns.map((column) => column.field);
              const [moved] = fields.splice(oldIndex, 1);
              fields.splice(targetIndex, 0, moved);
              return fields;
            })
          }
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
          slots={{ exportIcon: ExportUpIcon }}
          localeText={{
            paginationDisplayedRows: ({ from, to, count }) =>
              `${from}-${to} of ${count === -1 ? `more than ${to}` : count}`,
          }}
          getRowClassName={({ row }) =>
            row.id === -1 ? "grand-total-row" : ""
          }
          sx={{
            border: 0,
            "& .grand-total-row": {
              bgcolor: "action.hover",
              borderTop: 1,
              borderColor: "divider",
            },
          }}
        />
      </Box>
    </Container>
  );
}
