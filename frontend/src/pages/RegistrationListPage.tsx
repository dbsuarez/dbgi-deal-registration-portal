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
  MenuItem,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import {
  DataGrid,
  GridToolbarColumnsButton,
  GridToolbarContainer,
  GridToolbarDensitySelector,
  GridToolbarExport,
  GridToolbarFilterButton,
  gridFilterActiveItemsSelector,
  type GridColDef,
  type GridColumnVisibilityModel,
  type GridFilterModel,
  type GridSortModel,
  useGridApiContext,
  useGridSelector,
} from "@mui/x-data-grid";
import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { getRegistrations, type RegistrationListItem } from "../api";
import { useSession } from "../session";
import { getStatusColor } from "../status";

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

function RegistrationGridToolbar() {
  const apiRef = useGridApiContext();
  const activeFilterItems = useGridSelector(
    apiRef,
    gridFilterActiveItemsSelector,
  );

  return (
    <GridToolbarContainer>
      <GridToolbarColumnsButton />
      <GridToolbarFilterButton />
      <Button
        size="small"
        variant="text"
        disabled={activeFilterItems.length === 0}
        onClick={() => apiRef.current.setFilterModel({ items: [] })}
      >
        Clear filters
      </Button>
      <GridToolbarDensitySelector />
      <GridToolbarExport />
    </GridToolbarContainer>
  );
}

function loadGridPreference(key: string) {
  if (typeof localStorage?.getItem !== "function") return {};
  try {
    return JSON.parse(localStorage.getItem(key) ?? "{}");
  } catch {
    return {};
  }
}

function OverflowText({ children }: { children: string }) {
  const textRef = useRef<HTMLDivElement>(null);
  const [isOverflowing, setIsOverflowing] = useState(false);

  return (
    <Tooltip title={isOverflowing ? children : ""} enterDelay={300}>
      <Box
        ref={textRef}
        onMouseEnter={() => {
          const element = textRef.current;
          setIsOverflowing(
            Boolean(element && element.scrollWidth > element.clientWidth),
          );
        }}
        sx={{
          overflow: "hidden",
          textOverflow: "ellipsis",
          whiteSpace: "nowrap",
        }}
      >
        {children}
      </Box>
    </Tooltip>
  );
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
  const [projectStatus, setProjectStatus] = useState("");
  const [registrationStatus, setRegistrationStatus] = useState("");
  const [filterModel, setFilterModel] = useState<GridFilterModel>({
    items: [],
  });
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
      projectStatus,
      registrationStatus,
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
  }, [
    debouncedSearch,
    paginationModel,
    projectStatus,
    refreshKey,
    registrationStatus,
    sortModel,
  ]);

  const baseColumns = useMemo<GridColDef<RegistrationListItem>[]>(
    () => [
      {
        field: "reference",
        headerName: "Reference",
        minWidth: 140,
        renderCell: ({ row }) =>
          row.id === -1 ? (
            <Box component="span" sx={{ font: "inherit", fontWeight: 700 }}>
              Grand total
            </Box>
          ) : (
            <Link href={`/registrations/${row.id}/`}>{row.reference}</Link>
          ),
      },
      {
        field: "project_title",
        headerName: "Project",
        minWidth: 220,
        flex: 1,
        renderCell: ({ row, value }) =>
          row.id === -1 ? null : <OverflowText>{String(value)}</OverflowText>,
      },
      ...(session.is_dbgi_admin
        ? [
            {
              field: "company_name",
              headerName: "Company",
              minWidth: 180,
              renderCell: ({ row, value }) =>
                row.id === -1 ? null : (
                  <OverflowText>{String(value)}</OverflowText>
                ),
            } as GridColDef<RegistrationListItem>,
          ]
        : []),
      {
        field: "end_user_name",
        headerName: "End-user",
        minWidth: 200,
        flex: 1,
        renderCell: ({ row, value }) =>
          row.id === -1 ? null : <OverflowText>{String(value)}</OverflowText>,
      },
      {
        field: "status_label",
        headerName: "Registration status",
        minWidth: 140,
        sortable: false,
        renderCell: ({ row, value }) =>
          row.id === -1 ? null : (
            <Tooltip title={String(value)} enterDelay={300}>
              <Chip
                label={value}
                size="small"
                variant="filled"
                color={getStatusColor("registration", row.status)}
              />
            </Tooltip>
          ),
      },
      {
        field: "project_status_label",
        headerName: "Project status",
        minWidth: 135,
        sortable: false,
        renderCell: ({ row, value }) =>
          row.id === -1 ? null : (
            <Tooltip title={String(value)} enterDelay={300}>
              <Chip
                label={value}
                size="small"
                variant="filled"
                color={getStatusColor("project", row.project_status)}
              />
            </Tooltip>
          ),
      },
      {
        field: "price_status_label",
        headerName: "Price status",
        minWidth: 150,
        sortable: false,
        renderCell: ({ row, value }) =>
          row.id === -1 ? null : (
            <Tooltip title={String(value)} enterDelay={300}>
              <Chip
                label={value}
                size="small"
                variant="filled"
                color={getStatusColor("price", row.price_status)}
              />
            </Tooltip>
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
          <Box
            component="span"
            sx={{ font: "inherit", fontWeight: row.id === -1 ? 700 : 400 }}
          >
            {Number(value).toLocaleString("en-PH", {
              minimumFractionDigits: 2,
            })}
          </Box>
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
            <Tooltip title="Review required" enterDelay={300}>
              <Chip label="Review required" size="small" color="warning" />
            </Tooltip>
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
      <Stack
        direction={{ xs: "column", sm: "row" }}
        spacing={2}
        useFlexGap
        flexWrap="wrap"
        sx={{ my: 3 }}
      >
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
        <TextField
          select
          label="Project status"
          value={projectStatus}
          onChange={(event) => {
            setProjectStatus(event.target.value);
            setPaginationModel((current) => ({ ...current, page: 0 }));
          }}
          slotProps={{
            inputLabel: { shrink: true },
            select: { displayEmpty: true },
          }}
          sx={{ minWidth: { xs: "100%", sm: 210 } }}
        >
          <MenuItem value="">All Project Statuses</MenuItem>
          <MenuItem value="not_linked">Not linked</MenuItem>
          <MenuItem value="upcoming">Upcoming</MenuItem>
          <MenuItem value="active">Active</MenuItem>
          <MenuItem value="won">Won</MenuItem>
          <MenuItem value="lost">Lost</MenuItem>
          <MenuItem value="cancelled">Cancelled</MenuItem>
          <MenuItem value="on_hold">On hold</MenuItem>
        </TextField>
        <TextField
          select
          label="Registration status"
          value={registrationStatus}
          onChange={(event) => {
            setRegistrationStatus(event.target.value);
            setPaginationModel((current) => ({ ...current, page: 0 }));
          }}
          slotProps={{
            inputLabel: { shrink: true },
            select: { displayEmpty: true },
          }}
          sx={{ minWidth: { xs: "100%", sm: 230 } }}
        >
          <MenuItem value="">All Registration Statuses</MenuItem>
          <MenuItem value="submitted">Submitted</MenuItem>
          <MenuItem value="under_review">Under review</MenuItem>
          <MenuItem value="changes_requested">Returned for changes</MenuItem>
          <MenuItem value="resubmitted">Resubmitted</MenuItem>
          <MenuItem value="eligible_matched">Registered</MenuItem>
          <MenuItem value="review_required">
            Review required after edit
          </MenuItem>
          <MenuItem value="approved">Approved</MenuItem>
          <MenuItem value="rejected">Rejected</MenuItem>
          <MenuItem value="withdrawn">Withdrawn</MenuItem>
        </TextField>
        <Button
          variant="text"
          disabled={
            !search &&
            !projectStatus &&
            !registrationStatus &&
            filterModel.items.length === 0
          }
          onClick={() => {
            setSearch("");
            setDebouncedSearch("");
            setProjectStatus("");
            setRegistrationStatus("");
            setFilterModel({ items: [] });
            setPaginationModel((current) => ({ ...current, page: 0 }));
          }}
        >
          Clear all filters
        </Button>
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
          filterModel={filterModel}
          onFilterModelChange={setFilterModel}
          pageSizeOptions={[10, 25, 50, 100]}
          disableRowSelectionOnClick
          onRowDoubleClick={({ row }) => navigate(`/registrations/${row.id}/`)}
          showToolbar
          slots={{ toolbar: RegistrationGridToolbar, exportIcon: ExportUpIcon }}
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
