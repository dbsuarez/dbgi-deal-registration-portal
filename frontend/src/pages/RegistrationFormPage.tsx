import AddIcon from "@mui/icons-material/Add";
import BugReportIcon from "@mui/icons-material/BugReport";
import DeleteIcon from "@mui/icons-material/Delete";
import EditIcon from "@mui/icons-material/Edit";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import {
  Alert,
  Autocomplete,
  Box,
  Breadcrumbs,
  Button,
  Checkbox,
  Container,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Drawer,
  FormControlLabel,
  Grid,
  IconButton,
  InputAdornment,
  Link,
  MenuItem,
  Paper,
  Popover,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Tooltip,
  Typography,
  type AutocompleteRenderInputParams,
} from "@mui/material";
import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type ChangeEvent,
  type FormEvent,
} from "react";
import { useNavigate, useParams } from "react-router-dom";

import {
  createRegistration,
  createRegistrationTestPreset,
  createEndUser,
  deleteAttachment,
  deleteRegistrationTestPreset,
  finalizeRegistration,
  getCompetitorBrands,
  getCompetitorModels,
  getEndUserClassifications,
  getEndUsers,
  getGeographicAreas,
  getGeographicDataset,
  getProducts,
  getRegistration,
  getRegistrationTestPresets,
  type Attachment,
  type CompetitorItem,
  type CompetitorModelOption,
  type EndUser,
  type EndUserClassificationOption,
  type EndUserCreatePayload,
  type GeographicArea,
  type GeographicDataset,
  type ProductOption,
  type RegistrationPayload,
  type RegistrationTestPreset,
  type RequestedItem,
  updateRegistration,
  updateRegistrationTestPreset,
  uploadAttachment,
} from "../api";
import { useSession } from "../session";

type MainFields = Omit<
  RegistrationPayload,
  "version" | "competitor_items" | "items"
>;
type PendingAttachment = { file: File; description: string };
type TestRegistrationPreset = {
  title: string;
  purpose: string;
  projectTitle: string;
  preferredEndUser: string;
  bidDate: string;
  deliveryDate: string;
  competitor: CompetitorItem;
  productCode: string;
  quantity: number;
  requestedUnitPrice: string;
  justification: string;
  evidenceDescription: string;
};

const testRegistrationPresets: TestRegistrationPreset[] = [
  {
    title: "Pasig competing bid A",
    purpose: "First registration for the shared Pasig printer competition.",
    projectTitle: "Pasig Schools Printer Procurement A",
    preferredEndUser: "Pasig",
    bidDate: "2027-01-15",
    deliveryDate: "2027-02-15",
    competitor: {
      brand: "HP",
      item_name: "LaserJet Pro 4003dn",
      bid_price: "8500.00",
      remarks: "Development test for the shared Pasig competition.",
    },
    productCode: "P1820W",
    quantity: 25,
    requestedUnitPrice: "7950.00",
    justification: "Requested test price for the Pasig printer procurement.",
    evidenceDescription: "Development evidence for Pasig competing bid A.",
  },
  {
    title: "Pasig competing bid B",
    purpose: "Different title, but the same End-user and product competition.",
    projectTitle: "Pasig Schools Printer Procurement B",
    preferredEndUser: "Pasig",
    bidDate: "2027-01-15",
    deliveryDate: "2027-02-15",
    competitor: {
      brand: "Lexmark",
      item_name: "MX431adn",
      bid_price: "8650.00",
      remarks: "Development test for the shared Pasig competition.",
    },
    productCode: "P1820W",
    quantity: 25,
    requestedUnitPrice: "8050.00",
    justification: "Competing test price for the Pasig printer procurement.",
    evidenceDescription: "Development evidence for Pasig competing bid B.",
  },
  {
    title: "Quezon City exact match",
    purpose: "Exercises an exact End-user, address, and product match.",
    projectTitle: "Quezon City Schools Printer Acquisition 2027",
    preferredEndUser: "Quezon City",
    bidDate: "2027-02-05",
    deliveryDate: "2027-03-20",
    competitor: {
      brand: "Canon",
      item_name: "imageCLASS LBP246dw",
      bid_price: "8200.00",
      remarks: "Development exact-match scenario.",
    },
    productCode: "M1820W",
    quantity: 40,
    requestedUnitPrice: "7750.00",
    justification: "Volume pricing request for a public school deployment.",
    evidenceDescription:
      "Development procurement notice for Quezon City schools.",
  },
  {
    title: "Makati office replacement",
    purpose: "Exercises a separate End-user and delivery schedule.",
    projectTitle: "Makati City Hall Printer Replacement 2027",
    preferredEndUser: "Makati",
    bidDate: "2027-02-20",
    deliveryDate: "2027-04-10",
    competitor: {
      brand: "Epson",
      item_name: "WorkForce Pro WF-C5890",
      bid_price: "19500.00",
      remarks: "Development material-edit scenario.",
    },
    productCode: "M1820W",
    quantity: 18,
    requestedUnitPrice: "7900.00",
    justification: "Replacement units for administrative offices.",
    evidenceDescription:
      "Development request for the Makati replacement project.",
  },
  {
    title: "Regional library rollout",
    purpose: "Exercises a smaller quantity and an alternate competitor model.",
    projectTitle: "Regional Public Library Printer Rollout",
    preferredEndUser: "Library",
    bidDate: "2027-03-12",
    deliveryDate: "2027-05-01",
    competitor: {
      brand: "Canon",
      item_name: "imageCLASS MF275dw",
      bid_price: "11250.00",
      remarks: "Development catalog-growth scenario.",
    },
    productCode: "P1820W",
    quantity: 8,
    requestedUnitPrice: "8350.00",
    justification: "Pilot deployment before a regional rollout.",
    evidenceDescription: "Development request for a regional library rollout.",
  },
];

const emptyMain: MainFields = {
  end_user_id: 0,
  project_title: "",
  bid_date: "",
  delivery_date: "",
  contact_person: "",
  contact_designation: "",
  contact_email: "",
  contact_number: "",
  evidence_description: "",
  evidence_url: "",
  evidence_sharing_confirmed: false,
};

const emptyEndUser: EndUserCreatePayload = {
  official_name: "",
  acronym: "",
  government_branch: "",
  organization_type: "",
  sector: "",
  region: "",
  province: "",
  city_municipality: "",
  street_address: "",
  postal_code: "",
  philgeps_reference: "",
  source_url: "",
};

const emptyCompetitor: CompetitorItem = {
  brand: "",
  item_name: "",
  bid_price: "",
  remarks: "",
};

const emptyItem: RequestedItem = {
  product_id: null,
  non_catalog_name: "",
  quantity: 1,
  requested_unit_price: "",
  justification: "",
};

const numeric = { "& input": { textAlign: "right" } };
const numericCell = {
  textAlign: "right" as const,
  fontVariantNumeric: "tabular-nums",
};

export default function RegistrationFormPage() {
  const { id } = useParams();
  const registrationId = id ? Number(id) : null;
  const session = useSession();
  const navigate = useNavigate();
  const [savedRegistrationId, setSavedRegistrationId] = useState<number | null>(
    registrationId,
  );
  const [main, setMain] = useState<MainFields>(() => ({
    ...emptyMain,
    contact_person: session.display_name,
    contact_designation: session.designation,
    contact_email: session.email,
    contact_number: session.phone_number,
  }));
  const [version, setVersion] = useState<number | undefined>();
  const [evidencePendingFinalize, setEvidencePendingFinalize] = useState(false);
  const [competitors, setCompetitors] = useState<CompetitorItem[]>([]);
  const [items, setItems] = useState<RequestedItem[]>([]);
  const [products, setProducts] = useState<ProductOption[]>([]);
  const [endUsers, setEndUsers] = useState<EndUser[]>([]);
  const [competitorBrands, setCompetitorBrands] = useState<string[]>([]);
  const [competitorModels, setCompetitorModels] = useState<
    CompetitorModelOption[]
  >([]);
  const [endUserDialogOpen, setEndUserDialogOpen] = useState(false);
  const [endUserDraft, setEndUserDraft] =
    useState<EndUserCreatePayload>(emptyEndUser);
  const [savingEndUser, setSavingEndUser] = useState(false);
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [attachmentIdsToDelete, setAttachmentIdsToDelete] = useState<number[]>(
    [],
  );
  const [pendingAttachments, setPendingAttachments] = useState<
    PendingAttachment[]
  >([]);
  const [competitorEditor, setCompetitorEditor] = useState<
    number | "new" | null
  >(null);
  const [itemEditor, setItemEditor] = useState<number | "new" | null>(null);
  const [competitorDraft, setCompetitorDraft] =
    useState<CompetitorItem>(emptyCompetitor);
  const [itemDraft, setItemDraft] = useState<RequestedItem>(emptyItem);
  const [deleteTarget, setDeleteTarget] = useState<Attachment | null>(null);
  const [dirty, setDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [testPanelOpen, setTestPanelOpen] = useState(false);
  const [loadedPreset, setLoadedPreset] = useState("");
  const [savedPresets, setSavedPresets] = useState<RegistrationTestPreset[]>(
    [],
  );
  const [editingPresetId, setEditingPresetId] = useState<number | null>(null);
  const [presetDialogOpen, setPresetDialogOpen] = useState(false);
  const [presetName, setPresetName] = useState("");
  const [presetDescription, setPresetDescription] = useState("");
  const [presetSaving, setPresetSaving] = useState(false);
  const [presetDeleteTarget, setPresetDeleteTarget] =
    useState<RegistrationTestPreset | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    getProducts(controller.signal)
      .then(setProducts)
      .catch((reason: Error) => {
        if (reason.name !== "AbortError") setError(reason.message);
      });
    getEndUsers(controller.signal)
      .then(setEndUsers)
      .catch((reason: Error) => {
        if (reason.name !== "AbortError") setError(reason.message);
      });
    getCompetitorBrands(controller.signal)
      .then(setCompetitorBrands)
      .catch((reason: Error) => {
        if (reason.name !== "AbortError") setError(reason.message);
      });
    getCompetitorModels(controller.signal)
      .then(setCompetitorModels)
      .catch((reason: Error) => {
        if (reason.name !== "AbortError") setError(reason.message);
      });
    if (session.is_debug && !registrationId) {
      getRegistrationTestPresets(controller.signal)
        .then(setSavedPresets)
        .catch((reason: Error) => {
          if (reason.name !== "AbortError") setError(reason.message);
        });
    }
    if (registrationId) {
      getRegistration(registrationId, controller.signal)
        .then((registration) => {
          if (!registration.can_edit)
            throw new Error("This account cannot edit registrations.");
          setMain({
            end_user_id: registration.end_user_id ?? 0,
            project_title: registration.project_title,
            bid_date: registration.bid_date,
            delivery_date: registration.delivery_date,
            contact_person: registration.contact_person,
            contact_designation: registration.contact_designation,
            contact_email: registration.contact_email,
            contact_number: registration.contact_number,
            evidence_description: registration.evidence_description,
            evidence_url: registration.evidence_url,
            evidence_sharing_confirmed: registration.evidence_sharing_confirmed,
          });
          setVersion(registration.version);
          setCompetitors(registration.competitor_items);
          setItems(registration.items);
          setAttachments(registration.attachments);
        })
        .catch((reason: Error) => {
          if (reason.name !== "AbortError") setError(reason.message);
        });
    }
    return () => controller.abort();
  }, [registrationId, session.is_debug]);

  useEffect(() => {
    const warn = (event: BeforeUnloadEvent) => {
      if (!dirty) return;
      event.preventDefault();
    };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [dirty]);

  const title = savedRegistrationId ? "Edit registration" : "New registration";
  const productMap = useMemo(
    () => new Map(products.map((product) => [product.id, product])),
    [products],
  );
  const selectedEndUser =
    endUsers.find((endUser) => endUser.id === main.end_user_id) ?? null;

  const saveEndUser = async () => {
    setSavingEndUser(true);
    setError("");
    try {
      const created = await createEndUser(endUserDraft, session.csrf_token);
      setEndUsers((current) => [...current, created]);
      setMain((current) => ({ ...current, end_user_id: created.id }));
      setEndUserDraft(emptyEndUser);
      setEndUserDialogOpen(false);
      setDirty(true);
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "The End-user could not be added.",
      );
    } finally {
      setSavingEndUser(false);
    }
  };

  const updateMain = (field: keyof MainFields, value: string | boolean) => {
    setMain((current) => ({ ...current, [field]: value }));
    setDirty(true);
  };

  const openCompetitor = (index: number | "new") => {
    setCompetitorDraft(
      index === "new" ? emptyCompetitor : { ...competitors[index] },
    );
    setCompetitorEditor(index);
  };

  const saveCompetitor = () => {
    if (
      !competitorDraft.brand ||
      !competitorDraft.item_name ||
      competitorDraft.bid_price === ""
    )
      return;
    setCompetitors((current) =>
      competitorEditor === "new"
        ? [...current, competitorDraft]
        : current.map((item, index) =>
            index === competitorEditor ? competitorDraft : item,
          ),
    );
    setCompetitorEditor(null);
    setDirty(true);
  };

  const openItem = (index: number | "new") => {
    setItemDraft(index === "new" ? emptyItem : { ...items[index] });
    setItemEditor(index);
  };

  const saveItem = () => {
    if (
      (!itemDraft.product_id && !itemDraft.non_catalog_name) ||
      itemDraft.quantity < 1 ||
      itemDraft.requested_unit_price === ""
    )
      return;
    setItems((current) =>
      itemEditor === "new"
        ? [...current, itemDraft]
        : current.map((item, index) =>
            index === itemEditor ? itemDraft : item,
          ),
    );
    setItemEditor(null);
    setDirty(true);
  };

  const applyTestPreset = (preset: TestRegistrationPreset) => {
    const normalizedPreference = preset.preferredEndUser.toLocaleLowerCase();
    const endUser =
      endUsers.find((option) =>
        `${option.official_name} ${option.full_address}`
          .toLocaleLowerCase()
          .includes(normalizedPreference),
      ) ?? endUsers[0];
    const product =
      products.find((option) => option.code === preset.productCode) ??
      products[0];

    if (!endUser || !product) {
      setError(
        "Test data needs at least one active End-user and one active product.",
      );
      return;
    }

    setMain({
      end_user_id: endUser.id,
      project_title: preset.projectTitle,
      bid_date: preset.bidDate,
      delivery_date: preset.deliveryDate,
      contact_person: session.display_name,
      contact_designation: session.designation,
      contact_email: session.email,
      contact_number: session.phone_number,
      evidence_description: preset.evidenceDescription,
      evidence_url: "",
      evidence_sharing_confirmed: true,
    });
    setCompetitors([{ ...preset.competitor }]);
    setItems([
      {
        product_id: product.id,
        non_catalog_name: "",
        quantity: preset.quantity,
        requested_unit_price: preset.requestedUnitPrice,
        justification: preset.justification,
      },
    ]);
    setPendingAttachments([]);
    setEditingPresetId(null);
    setError("");
    setDirty(true);
    setLoadedPreset(preset.title);
    setTestPanelOpen(false);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const currentTestPayload = (): RegistrationPayload => ({
    ...main,
    competitor_items: competitors.map(
      ({ brand, item_name, bid_price, remarks }) => ({
        brand,
        item_name,
        bid_price,
        remarks,
      }),
    ),
    items: items.map(
      ({
        product_id,
        non_catalog_name,
        quantity,
        requested_unit_price,
        justification,
      }) => ({
        product_id,
        non_catalog_name,
        quantity,
        requested_unit_price,
        justification,
      }),
    ),
  });

  const loadSavedPreset = (preset: RegistrationTestPreset) => {
    const {
      competitor_items,
      items: presetItems,
      ...presetMain
    } = preset.payload;
    setMain(presetMain);
    setCompetitors(competitor_items);
    setItems(presetItems);
    setPendingAttachments([]);
    setEditingPresetId(preset.id);
    setPresetName(preset.name);
    setPresetDescription(preset.description);
    setLoadedPreset(preset.name);
    setDirty(true);
    setTestPanelOpen(false);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const openSavePresetDialog = () => {
    setPresetName(main.project_title || "New registration test data");
    setPresetDescription("");
    setPresetDialogOpen(true);
  };

  const saveNewPreset = async () => {
    if (!presetName.trim()) return;
    setPresetSaving(true);
    setError("");
    try {
      const created = await createRegistrationTestPreset(
        presetName,
        presetDescription,
        currentTestPayload(),
        session.csrf_token,
      );
      setSavedPresets((current) => [...current, created]);
      setEditingPresetId(created.id);
      setLoadedPreset(created.name);
      setPresetDialogOpen(false);
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Test data could not be saved.",
      );
    } finally {
      setPresetSaving(false);
    }
  };

  const updateSavedPreset = async () => {
    const preset = savedPresets.find((item) => item.id === editingPresetId);
    if (!preset) return;
    setPresetSaving(true);
    try {
      const updated = await updateRegistrationTestPreset(
        preset.id,
        preset.name,
        preset.description,
        currentTestPayload(),
        session.csrf_token,
      );
      setSavedPresets((current) =>
        current.map((item) => (item.id === updated.id ? updated : item)),
      );
      setLoadedPreset(updated.name);
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Test data could not be updated.",
      );
    } finally {
      setPresetSaving(false);
    }
  };

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!competitors.length || !items.length) {
      setError("Add at least one competitor item and one requested product.");
      return;
    }
    setSaving(true);
    setError("");
    const evidenceChanged =
      evidencePendingFinalize ||
      pendingAttachments.length > 0 ||
      attachmentIdsToDelete.length > 0;
    const payload: RegistrationPayload = {
      ...main,
      ...(savedRegistrationId ? { version } : {}),
      competitor_items: competitors.map(
        ({ brand, item_name, bid_price, remarks }) => ({
          brand,
          item_name,
          bid_price,
          remarks,
        }),
      ),
      items: items.map(
        ({
          product_id,
          non_catalog_name,
          quantity,
          requested_unit_price,
          justification,
        }) => ({
          product_id,
          non_catalog_name,
          quantity,
          requested_unit_price,
          justification,
        }),
      ),
    };
    try {
      const saved = savedRegistrationId
        ? await updateRegistration(
            savedRegistrationId,
            payload,
            session.csrf_token,
          )
        : await createRegistration(payload, session.csrf_token);
      setSavedRegistrationId(saved.id);
      setVersion(saved.version);
      if (evidenceChanged) setEvidencePendingFinalize(true);
      for (const attachment of [...pendingAttachments]) {
        await uploadAttachment(
          saved.id,
          attachment.file,
          attachment.description,
          saved.version,
          session.csrf_token,
        );
        setPendingAttachments((current) =>
          current.filter((item) => item !== attachment),
        );
      }
      for (const attachmentId of [...attachmentIdsToDelete]) {
        await deleteAttachment(attachmentId, saved.version, session.csrf_token);
        setAttachmentIdsToDelete((current) =>
          current.filter((id) => id !== attachmentId),
        );
      }
      if (evidenceChanged) {
        const finalized = await finalizeRegistration(
          saved.id,
          saved.version,
          evidenceChanged,
          session.csrf_token,
        );
        setVersion(finalized.version);
        setEvidencePendingFinalize(false);
      }
      setDirty(false);
      navigate(`/registrations/${saved.id}/`, { replace: true });
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "The registration could not be saved.",
      );
    } finally {
      setSaving(false);
    }
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Breadcrumbs aria-label="Breadcrumb" sx={{ mb: 2 }}>
        <Link href="/">Registrations</Link>
        {savedRegistrationId && (
          <Link href={`/registrations/${savedRegistrationId}/`}>
            Registration details
          </Link>
        )}
        <Typography color="text.primary">{title}</Typography>
      </Breadcrumbs>
      <Typography variant="h1" gutterBottom>
        {title}
      </Typography>
      <Typography color="text.secondary" sx={{ mb: 3 }}>
        Requested prices are proposals and require DBGI review.
      </Typography>
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}
      {loadedPreset && (
        <Alert severity="success" sx={{ mb: 3 }}>
          Loaded test data: {loadedPreset}. Review the fields, then create the
          registration when ready.
        </Alert>
      )}
      <Box component="form" onSubmit={submit}>
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h2" gutterBottom>
            Opportunity and contact
          </Typography>
          <Grid container spacing={2}>
            <Grid size={{ xs: 12, md: 8 }}>
              <Autocomplete
                fullWidth
                options={endUsers}
                value={selectedEndUser}
                getOptionLabel={(option) =>
                  `${option.official_name}${option.acronym ? ` (${option.acronym})` : ""}`
                }
                onChange={(_, value) => {
                  setMain((current) => ({
                    ...current,
                    end_user_id: value?.id ?? 0,
                  }));
                  setDirty(true);
                }}
                renderInput={(params) => (
                  <TextField {...params} required label="End-user" />
                )}
              />
            </Grid>
            <Grid size={{ xs: 12, md: 4 }}>
              <Button
                fullWidth
                variant="outlined"
                sx={{ height: "100%" }}
                onClick={() => setEndUserDialogOpen(true)}
              >
                Add missing End-user
              </Button>
            </Grid>
            {selectedEndUser && (
              <Grid size={12}>
                <Alert
                  severity={
                    selectedEndUser.status === "verified"
                      ? "success"
                      : "warning"
                  }
                >
                  {selectedEndUser.full_address}. {selectedEndUser.status_label}
                  .
                  {selectedEndUser.status !== "verified" &&
                    " This registration can be submitted, but matching and ranking wait for administrator verification."}
                </Alert>
              </Grid>
            )}
            <Grid size={{ xs: 12, md: 6 }}>
              <TextField
                fullWidth
                required
                label="Project opportunity title"
                value={main.project_title}
                onChange={(e) => updateMain("project_title", e.target.value)}
              />
            </Grid>
            <Grid size={{ xs: 12, md: 3 }}>
              <TextField
                fullWidth
                required
                type="date"
                label="Bid date"
                value={main.bid_date}
                onChange={(e) => updateMain("bid_date", e.target.value)}
                slotProps={{ inputLabel: { shrink: true } }}
              />
            </Grid>
            <Grid size={{ xs: 12, md: 3 }}>
              <TextField
                fullWidth
                required
                type="date"
                label="Delivery date"
                value={main.delivery_date}
                onChange={(e) => updateMain("delivery_date", e.target.value)}
                slotProps={{ inputLabel: { shrink: true } }}
              />
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <TextField
                fullWidth
                required
                label="Contact person"
                value={main.contact_person}
                onChange={(e) => updateMain("contact_person", e.target.value)}
              />
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <TextField
                fullWidth
                required
                label="Designation"
                value={main.contact_designation}
                onChange={(e) =>
                  updateMain("contact_designation", e.target.value)
                }
              />
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <TextField
                fullWidth
                required
                type="email"
                label="Contact email"
                value={main.contact_email}
                onChange={(e) => updateMain("contact_email", e.target.value)}
              />
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <TextField
                fullWidth
                required
                label="Contact number"
                value={main.contact_number}
                onChange={(e) => updateMain("contact_number", e.target.value)}
              />
            </Grid>
          </Grid>
        </Paper>

        <Paper sx={{ p: 3, mb: 3 }}>
          <Stack
            direction="row"
            justifyContent="space-between"
            alignItems="center"
          >
            <Typography variant="h2">Competitor items</Typography>
            <Button
              startIcon={<AddIcon />}
              onClick={() => openCompetitor("new")}
            >
              Add competitor
            </Button>
          </Stack>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Brand</TableCell>
                  <TableCell>Item / model</TableCell>
                  <TableCell sx={numericCell}>Bid price</TableCell>
                  <TableCell>Remarks</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {competitors.map((item, index) => (
                  <TableRow key={`${item.brand}-${index}`}>
                    <TableCell>{item.brand}</TableCell>
                    <TableCell>{item.item_name}</TableCell>
                    <TableCell sx={numericCell}>{item.bid_price}</TableCell>
                    <TableCell>{item.remarks || "Not provided"}</TableCell>
                    <TableCell align="right">
                      <IconButton
                        aria-label="Edit competitor"
                        onClick={() => openCompetitor(index)}
                      >
                        <EditIcon />
                      </IconButton>
                      <IconButton
                        aria-label="Remove competitor"
                        onClick={() => {
                          setCompetitors((current) =>
                            current.filter(
                              (_, itemIndex) => itemIndex !== index,
                            ),
                          );
                          setDirty(true);
                        }}
                      >
                        <DeleteIcon />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>

        <Paper sx={{ p: 3, mb: 3 }}>
          <Stack
            direction="row"
            justifyContent="space-between"
            alignItems="center"
          >
            <Typography variant="h2">Requested products</Typography>
            <Button startIcon={<AddIcon />} onClick={() => openItem("new")}>
              Add product
            </Button>
          </Stack>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Product</TableCell>
                  <TableCell sx={numericCell}>Quantity</TableCell>
                  <TableCell sx={numericCell}>Requested unit price</TableCell>
                  <TableCell>Justification</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {items.map((item, index) => (
                  <TableRow
                    key={`${item.product_id}-${item.non_catalog_name}-${index}`}
                  >
                    <TableCell>
                      {item.product_id
                        ? `${productMap.get(item.product_id)?.code ?? item.product_code} - ${productMap.get(item.product_id)?.name ?? item.product_name}`
                        : item.non_catalog_name}
                    </TableCell>
                    <TableCell sx={numericCell}>{item.quantity}</TableCell>
                    <TableCell sx={numericCell}>
                      {item.requested_unit_price}
                    </TableCell>
                    <TableCell>
                      {item.justification || "Not provided"}
                    </TableCell>
                    <TableCell align="right">
                      <IconButton
                        aria-label="Edit requested product"
                        onClick={() => openItem(index)}
                      >
                        <EditIcon />
                      </IconButton>
                      <IconButton
                        aria-label="Remove requested product"
                        onClick={() => {
                          setItems((current) =>
                            current.filter(
                              (_, itemIndex) => itemIndex !== index,
                            ),
                          );
                          setDirty(true);
                        }}
                      >
                        <DeleteIcon />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>

        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h2" gutterBottom>
            Evidence
          </Typography>
          <Alert severity="info" sx={{ mb: 2 }}>
            Do not upload confidential third-party bids, unnecessary personal
            information, IDs, signatures, or another company&apos;s pricing.
          </Alert>
          <Grid container spacing={2}>
            <Grid size={12}>
              <TextField
                fullWidth
                required
                multiline
                rows={4}
                label="Evidence description"
                value={main.evidence_description}
                onChange={(e) =>
                  updateMain("evidence_description", e.target.value)
                }
              />
            </Grid>
            <Grid size={12}>
              <TextField
                fullWidth
                type="url"
                label="Public evidence link (optional)"
                value={main.evidence_url}
                onChange={(e) => updateMain("evidence_url", e.target.value)}
              />
            </Grid>
            <Grid size={12}>
              <FormControlLabel
                control={
                  <Checkbox
                    required
                    checked={main.evidence_sharing_confirmed}
                    onChange={(e) =>
                      updateMain("evidence_sharing_confirmed", e.target.checked)
                    }
                  />
                }
                label="I confirm that I am authorized to share this evidence with DBGI for review."
              />
            </Grid>
            <Grid size={12}>
              <Button component="label" variant="outlined">
                Add files
                <input
                  hidden
                  multiple
                  type="file"
                  accept=".pdf,.png,.jpg,.jpeg,.docx,.xlsx"
                  onChange={(e) => {
                    const files = Array.from(e.target.files ?? []).map(
                      (file) => ({ file, description: "" }),
                    );
                    setPendingAttachments((current) => [...current, ...files]);
                    setDirty(true);
                  }}
                />
              </Button>
            </Grid>
          </Grid>
          <ListAttachments
            attachments={attachments}
            pending={pendingAttachments}
            onDeleteExisting={setDeleteTarget}
            onDeletePending={(index) =>
              setPendingAttachments((current) =>
                current.filter((_, itemIndex) => itemIndex !== index),
              )
            }
          />
        </Paper>

        <Stack direction="row" spacing={2} justifyContent="flex-end">
          <Button
            disabled={saving}
            onClick={() => {
              if (!dirty || window.confirm("Discard unsaved changes?"))
                navigate(
                  savedRegistrationId
                    ? `/registrations/${savedRegistrationId}/`
                    : "/",
                );
            }}
          >
            Cancel
          </Button>
          {session.is_debug && !savedRegistrationId && (
            <Button
              variant="outlined"
              color="warning"
              startIcon={<BugReportIcon />}
              disabled={presetSaving}
              onClick={
                editingPresetId ? updateSavedPreset : openSavePresetDialog
              }
            >
              {editingPresetId ? "Update test data" : "Save as test data"}
            </Button>
          )}
          <Button type="submit" variant="contained" disabled={saving}>
            {saving
              ? "Saving..."
              : savedRegistrationId
                ? "Save changes"
                : "Create registration"}
          </Button>
        </Stack>
      </Box>

      <CompetitorDialog
        open={competitorEditor !== null}
        value={competitorDraft}
        brands={competitorBrands}
        models={competitorModels}
        onChange={setCompetitorDraft}
        onClose={() => setCompetitorEditor(null)}
        onSave={saveCompetitor}
      />
      <ItemDialog
        open={itemEditor !== null}
        value={itemDraft}
        products={products}
        onChange={setItemDraft}
        onClose={() => setItemEditor(null)}
        onSave={saveItem}
      />
      <EndUserDialog
        open={endUserDialogOpen}
        value={endUserDraft}
        saving={savingEndUser}
        showFieldHelp={session.show_end_user_field_help}
        onChange={setEndUserDraft}
        onClose={() => setEndUserDialogOpen(false)}
        onSave={saveEndUser}
      />
      <Dialog
        open={Boolean(deleteTarget)}
        onClose={() => setDeleteTarget(null)}
      >
        <DialogTitle>Remove attachment?</DialogTitle>
        <DialogContent>
          <Typography>
            This will remove {deleteTarget?.original_name} permanently when you
            save the registration.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteTarget(null)}>Cancel</Button>
          <Button
            color="error"
            onClick={() => {
              if (!deleteTarget) return;
              setAttachmentIdsToDelete((current) => [
                ...current,
                deleteTarget.id,
              ]);
              setAttachments((current) =>
                current.filter((item) => item.id !== deleteTarget.id),
              );
              setDeleteTarget(null);
              setDirty(true);
            }}
          >
            Remove file
          </Button>
        </DialogActions>
      </Dialog>
      {session.is_debug && !savedRegistrationId && (
        <>
          <Button
            variant="contained"
            color="warning"
            startIcon={<BugReportIcon />}
            onClick={() => setTestPanelOpen(true)}
            sx={{
              position: "fixed",
              right: 0,
              top: "50%",
              zIndex: (theme) => theme.zIndex.speedDial,
              borderTopRightRadius: 0,
              borderBottomRightRadius: 0,
              transform: "translateY(-50%) rotate(-90deg) translateY(-100%)",
              transformOrigin: "right top",
            }}
          >
            Test data
          </Button>
          <Drawer
            anchor="right"
            open={testPanelOpen}
            onClose={() => setTestPanelOpen(false)}
            slotProps={{
              paper: { sx: { width: { xs: "100%", sm: 420 }, p: 3 } },
            }}
          >
            <Typography variant="h2" gutterBottom>
              Registration test data
            </Typography>
            <Alert severity="warning" sx={{ mb: 2 }}>
              Development only. Loading a sample replaces the current unsaved
              form values, but does not create a registration.
            </Alert>
            <Stack spacing={2}>
              {testRegistrationPresets.map((preset) => (
                <Paper key={preset.title} variant="outlined" sx={{ p: 2 }}>
                  <Typography fontWeight={700}>{preset.title}</Typography>
                  <Typography
                    color="text.secondary"
                    variant="body2"
                    sx={{ mb: 2 }}
                  >
                    {preset.purpose}
                  </Typography>
                  <Button
                    fullWidth
                    variant="outlined"
                    onClick={() => applyTestPreset(preset)}
                  >
                    Fill this registration
                  </Button>
                </Paper>
              ))}
            </Stack>
            <Typography variant="h3" sx={{ mt: 3, mb: 1 }}>
              My saved test data
            </Typography>
            {savedPresets.length === 0 ? (
              <Typography color="text.secondary" variant="body2">
                No saved test data yet. Fill the form and use Save as test data.
              </Typography>
            ) : (
              <Stack spacing={2}>
                {savedPresets.map((preset) => (
                  <Paper key={preset.id} variant="outlined" sx={{ p: 2 }}>
                    <Typography fontWeight={700}>{preset.name}</Typography>
                    {preset.description && (
                      <Typography color="text.secondary" variant="body2">
                        {preset.description}
                      </Typography>
                    )}
                    <Stack direction="row" spacing={1} sx={{ mt: 2 }}>
                      <Button onClick={() => loadSavedPreset(preset)}>
                        Edit
                      </Button>
                      <Button
                        color="error"
                        onClick={() => setPresetDeleteTarget(preset)}
                      >
                        Delete
                      </Button>
                    </Stack>
                  </Paper>
                ))}
              </Stack>
            )}
            <Button sx={{ mt: 2 }} onClick={() => setTestPanelOpen(false)}>
              Close
            </Button>
          </Drawer>
        </>
      )}
      <Dialog
        open={presetDialogOpen}
        onClose={() => !presetSaving && setPresetDialogOpen(false)}
        fullWidth
        maxWidth="sm"
      >
        <DialogTitle>Save registration as test data</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ pt: 1 }}>
            <TextField
              autoFocus
              required
              label="Test data name"
              value={presetName}
              onChange={(event) => setPresetName(event.target.value)}
            />
            <TextField
              label="Description"
              value={presetDescription}
              onChange={(event) => setPresetDescription(event.target.value)}
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPresetDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            disabled={presetSaving || !presetName.trim()}
            onClick={saveNewPreset}
          >
            Save test data
          </Button>
        </DialogActions>
      </Dialog>
      <Dialog
        open={Boolean(presetDeleteTarget)}
        onClose={() => setPresetDeleteTarget(null)}
      >
        <DialogTitle>Delete saved test data?</DialogTitle>
        <DialogContent>
          <Typography>
            {presetDeleteTarget?.name} will be permanently removed from your
            development presets.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPresetDeleteTarget(null)}>Cancel</Button>
          <Button
            color="error"
            onClick={async () => {
              if (!presetDeleteTarget) return;
              try {
                await deleteRegistrationTestPreset(
                  presetDeleteTarget.id,
                  session.csrf_token,
                );
                setSavedPresets((current) =>
                  current.filter((item) => item.id !== presetDeleteTarget.id),
                );
                if (editingPresetId === presetDeleteTarget.id) {
                  setEditingPresetId(null);
                }
                setPresetDeleteTarget(null);
              } catch (reason) {
                setError(
                  reason instanceof Error
                    ? reason.message
                    : "Test data could not be deleted.",
                );
              }
            }}
          >
            Delete test data
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}

function CompetitorDialog({
  open,
  value,
  brands,
  models,
  onChange,
  onClose,
  onSave,
}: {
  open: boolean;
  value: CompetitorItem;
  brands: string[];
  models: CompetitorModelOption[];
  onChange: (value: CompetitorItem) => void;
  onClose: () => void;
  onSave: () => void;
}) {
  const brandInputRef = useRef<HTMLInputElement>(null);
  const modelOptions = models
    .filter(
      (model) =>
        model.brand.localeCompare(value.brand, undefined, {
          sensitivity: "accent",
        }) === 0,
    )
    .map((model) => model.item_name);

  return (
    <Dialog
      open={open}
      onClose={onClose}
      fullWidth
      maxWidth="sm"
      slotProps={{
        transition: {
          onEntered: () => brandInputRef.current?.focus(),
        },
      }}
    >
      <DialogTitle>Competitor item</DialogTitle>
      <DialogContent>
        <Grid container spacing={2} sx={{ pt: 1 }}>
          <Grid size={6}>
            <Autocomplete
              freeSolo
              options={brands}
              inputValue={value.brand}
              onInputChange={(_, brand) => onChange({ ...value, brand })}
              renderInput={(params) => (
                <TextField
                  {...params}
                  inputRef={brandInputRef}
                  required
                  label="Brand"
                  helperText="Choose a previous brand or enter a new one."
                />
              )}
            />
          </Grid>
          <Grid size={6}>
            <Autocomplete
              freeSolo
              options={modelOptions}
              inputValue={value.item_name}
              onInputChange={(_, itemName) =>
                onChange({ ...value, item_name: itemName })
              }
              renderInput={(params) => (
                <TextField
                  {...params}
                  required
                  label="Item / model"
                  helperText="Choose a previous model or enter a new one."
                />
              )}
            />
          </Grid>
          <Grid size={12}>
            <TextField
              fullWidth
              required
              type="number"
              label="Bid price"
              value={value.bid_price}
              onChange={(e) =>
                onChange({ ...value, bid_price: e.target.value })
              }
              sx={numeric}
              slotProps={{ htmlInput: { min: 0, step: "0.01" } }}
            />
          </Grid>
          <Grid size={12}>
            <TextField
              fullWidth
              multiline
              rows={2}
              label="Remarks"
              value={value.remarks}
              onChange={(e) => onChange({ ...value, remarks: e.target.value })}
            />
          </Grid>
        </Grid>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          variant="contained"
          onClick={onSave}
          disabled={
            !value.brand.trim() ||
            !value.item_name.trim() ||
            value.bid_price === ""
          }
        >
          Save item
        </Button>
      </DialogActions>
    </Dialog>
  );
}

function ItemDialog({
  open,
  value,
  products,
  onChange,
  onClose,
  onSave,
}: {
  open: boolean;
  value: RequestedItem;
  products: ProductOption[];
  onChange: (value: RequestedItem) => void;
  onClose: () => void;
  onSave: () => void;
}) {
  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle>Requested product</DialogTitle>
      <DialogContent>
        <Grid container spacing={2} sx={{ pt: 1 }}>
          <Grid size={12}>
            <TextField
              select
              fullWidth
              label="Catalog product"
              value={value.product_id ?? ""}
              onChange={(e) => {
                const product = products.find(
                  (option) => option.id === Number(e.target.value),
                );
                onChange({
                  ...value,
                  product_id: e.target.value ? Number(e.target.value) : null,
                  non_catalog_name: e.target.value
                    ? ""
                    : value.non_catalog_name,
                  requested_unit_price: product
                    ? (product.list_price ?? "")
                    : value.requested_unit_price,
                });
              }}
            >
              <MenuItem value="">Not in catalog</MenuItem>
              {products.map((product) => (
                <MenuItem key={product.id} value={product.id}>
                  {product.code} - {product.name} ({product.category}) |{" "}
                  {product.currency}{" "}
                  {product.list_price
                    ? Number(product.list_price).toLocaleString("en-PH", {
                        minimumFractionDigits: 2,
                      })
                    : "Price not set"}
                </MenuItem>
              ))}
            </TextField>
          </Grid>
          {!value.product_id && (
            <Grid size={12}>
              <TextField
                autoFocus
                fullWidth
                required
                label="Non-catalog product description"
                value={value.non_catalog_name}
                onChange={(e) =>
                  onChange({ ...value, non_catalog_name: e.target.value })
                }
              />
            </Grid>
          )}
          <Grid size={6}>
            <TextField
              fullWidth
              required
              type="number"
              label="Quantity"
              value={value.quantity}
              onChange={(e) =>
                onChange({ ...value, quantity: Number(e.target.value) })
              }
              sx={numeric}
              slotProps={{ htmlInput: { min: 1, step: 1 } }}
            />
          </Grid>
          <Grid size={6}>
            <TextField
              fullWidth
              required
              type="number"
              label="Requested unit price"
              value={value.requested_unit_price}
              onChange={(e) =>
                onChange({ ...value, requested_unit_price: e.target.value })
              }
              sx={numeric}
              slotProps={{ htmlInput: { min: 0, step: "0.01" } }}
            />
          </Grid>
          <Grid size={12}>
            <TextField
              fullWidth
              multiline
              rows={2}
              label="Justification"
              value={value.justification}
              onChange={(e) =>
                onChange({ ...value, justification: e.target.value })
              }
            />
          </Grid>
        </Grid>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          variant="contained"
          onClick={onSave}
          disabled={
            (!value.product_id && !value.non_catalog_name.trim()) ||
            value.quantity < 1 ||
            value.requested_unit_price === ""
          }
        >
          Save item
        </Button>
      </DialogActions>
    </Dialog>
  );
}

function EndUserDialog({
  open,
  value,
  saving,
  showFieldHelp,
  onChange,
  onClose,
  onSave,
}: {
  open: boolean;
  value: EndUserCreatePayload;
  saving: boolean;
  showFieldHelp: boolean;
  onChange: (value: EndUserCreatePayload) => void;
  onClose: () => void;
  onSave: () => void;
}) {
  const governmentBranches = [
    "National government",
    "Local government",
    "Government-owned or controlled corporation",
    "Constitutional office",
    "Other government entity",
  ];
  const [organizationTypes, setOrganizationTypes] = useState<
    EndUserClassificationOption[]
  >([]);
  const [sectors, setSectors] = useState<EndUserClassificationOption[]>([]);
  const [regions, setRegions] = useState<GeographicArea[]>([]);
  const [provinces, setProvinces] = useState<GeographicArea[]>([]);
  const [cities, setCities] = useState<GeographicArea[]>([]);
  const [dataset, setDataset] = useState<GeographicDataset | null>(null);
  const selectedRegion =
    regions.find((item) => item.name === value.region) ?? null;
  const selectedProvince =
    provinces.find((item) => item.name === value.province) ?? null;
  const selectedCity =
    cities.find((item) => item.name === value.city_municipality) ?? null;
  const selectedRegionCode = selectedRegion?.code;
  const selectedProvinceCode = selectedProvince?.code;

  useEffect(() => {
    if (!open) return;
    const controller = new AbortController();
    Promise.all([
      getGeographicDataset(controller.signal),
      getGeographicAreas("region", {}, controller.signal),
    ])
      .then(([currentDataset, regionOptions]) => {
        setDataset(currentDataset);
        setRegions(regionOptions);
      })
      .catch(() => {
        setDataset(null);
        setRegions([]);
      });
    getEndUserClassifications("organization_type", controller.signal)
      .then(setOrganizationTypes)
      .catch(() => setOrganizationTypes([]));
    getEndUserClassifications("sector", controller.signal)
      .then(setSectors)
      .catch(() => setSectors([]));
    return () => controller.abort();
  }, [open]);

  useEffect(() => {
    if (!open || !selectedRegionCode) return;
    const controller = new AbortController();
    Promise.all([
      getGeographicAreas(
        "province",
        { region_code: selectedRegionCode },
        controller.signal,
      ),
      getGeographicAreas(
        "city_municipality",
        { region_code: selectedRegionCode },
        controller.signal,
      ),
    ]).then(([provinceOptions, cityOptions]) => {
      setProvinces(provinceOptions);
      setCities(cityOptions);
    });
    return () => controller.abort();
  }, [open, selectedRegionCode]);

  useEffect(() => {
    if (!open || !selectedRegionCode || !selectedProvinceCode) return;
    const controller = new AbortController();
    getGeographicAreas(
      "city_municipality",
      {
        region_code: selectedRegionCode,
        province_code: selectedProvinceCode,
      },
      controller.signal,
    ).then(setCities);
    return () => controller.abort();
  }, [open, selectedRegionCode, selectedProvinceCode]);

  const field = (name: keyof EndUserCreatePayload) => ({
    value: value[name],
    onChange: (event: ChangeEvent<HTMLInputElement>) =>
      onChange({ ...value, [name]: event.target.value }),
  });
  const help = (label: string, text: string) =>
    showFieldHelp
      ? {
          input: {
            endAdornment: (
              <InputAdornment position="end">
                <EndUserFieldHelp label={label} text={text} />
              </InputAdornment>
            ),
          },
        }
      : undefined;
  const autocompleteHelp = (
    params: AutocompleteRenderInputParams,
    label: string,
    text: string,
  ) => ({
    input: {
      ...params.InputProps,
      endAdornment: (
        <>
          {showFieldHelp && (
            <InputAdornment position="end">
              <EndUserFieldHelp label={label} text={text} />
            </InputAdornment>
          )}
          {params.InputProps.endAdornment}
        </>
      ),
    },
  });
  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="md">
      <DialogTitle>Add missing End-user</DialogTitle>
      <DialogContent>
        <Alert severity="info" sx={{ mt: 1, mb: 2 }}>
          Use the official organization name and address. The new End-user is
          immediately selectable, but an administrator must verify it before
          automatic matching or ranking can occur.
        </Alert>
        {dataset && (
          <Alert severity="success" sx={{ mb: 2 }}>
            Location choices use Philippine Standard Geographic Code{" "}
            {dataset.version}.
          </Alert>
        )}
        <Grid container spacing={2}>
          <Grid size={{ xs: 12, md: 8 }}>
            <TextField
              fullWidth
              required
              label="Official name"
              slotProps={help(
                "Official name",
                "Use the organization name shown on official documents. Examples: Department of Education; Pasig City General Services Office.",
              )}
              {...field("official_name")}
            />
          </Grid>
          <Grid size={{ xs: 12, md: 4 }}>
            <TextField
              fullWidth
              label="Acronym"
              slotProps={help(
                "Acronym",
                "Enter the commonly used short name, if one exists. Examples: DepEd; PCGSO.",
              )}
              {...field("acronym")}
            />
          </Grid>
          <Grid size={{ xs: 12, md: 4 }}>
            <Autocomplete
              disablePortal
              options={governmentBranches}
              value={value.government_branch || null}
              onChange={(_, option) =>
                onChange({ ...value, government_branch: option ?? "" })
              }
              renderInput={(params) => (
                <TextField
                  {...params}
                  label="Government branch"
                  slotProps={autocompleteHelp(
                    params,
                    "Government branch",
                    "Choose the level or branch that controls the organization. Examples: National government; Local government.",
                  )}
                />
              )}
            />
          </Grid>
          <Grid size={{ xs: 12, md: 4 }}>
            <Autocomplete
              disablePortal
              freeSolo
              options={organizationTypes.map((option) => option.name)}
              value={value.organization_type}
              onInputChange={(_, option) =>
                onChange({ ...value, organization_type: option })
              }
              renderInput={(params) => (
                <TextField
                  {...params}
                  label="Organization type"
                  helperText="A new value will be sent to an administrator for approval."
                  slotProps={autocompleteHelp(
                    params,
                    "Organization type",
                    "Choose a specific organization type or enter a missing one for administrator review. Examples: City government; Public school.",
                  )}
                />
              )}
            />
          </Grid>
          <Grid size={{ xs: 12, md: 4 }}>
            <Autocomplete
              disablePortal
              freeSolo
              options={sectors.map((option) => option.name)}
              value={value.sector}
              onInputChange={(_, option) =>
                onChange({ ...value, sector: option })
              }
              renderInput={(params) => (
                <TextField
                  {...params}
                  label="Sector"
                  helperText="A new value will be sent to an administrator for approval."
                  slotProps={autocompleteHelp(
                    params,
                    "Sector",
                    "Choose a broad service area or enter a missing one for administrator review. Examples: Education; Health.",
                  )}
                />
              )}
            />
          </Grid>
          <Grid size={{ xs: 12, md: 4 }}>
            {regions.length ? (
              <Autocomplete
                disablePortal
                options={regions}
                value={selectedRegion}
                getOptionLabel={(option) => option.name}
                onChange={(_, option) => {
                  setProvinces([]);
                  setCities([]);
                  onChange({
                    ...value,
                    region: option?.name ?? "",
                    province: "",
                    city_municipality: "",
                    postal_code: "",
                  });
                }}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    label="Region"
                    slotProps={autocompleteHelp(
                      params,
                      "Region",
                      "Use the official Philippine region name or code. Examples: National Capital Region (NCR); Region IV-A (CALABARZON).",
                    )}
                  />
                )}
              />
            ) : (
              <TextField fullWidth label="Region" {...field("region")} />
            )}
          </Grid>
          <Grid size={{ xs: 12, md: 4 }}>
            {regions.length ? (
              <Autocomplete
                disablePortal
                options={provinces}
                value={selectedProvince}
                disabled={!selectedRegion || provinces.length === 0}
                getOptionLabel={(option) => option.name}
                onChange={(_, option) => {
                  setCities([]);
                  onChange({
                    ...value,
                    province: option?.name ?? "",
                    city_municipality: "",
                    postal_code: "",
                  });
                }}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    label="Province"
                    helperText={
                      selectedRegion && provinces.length === 0
                        ? "Not applicable for this region."
                        : ""
                    }
                    slotProps={autocompleteHelp(
                      params,
                      "Province",
                      "Choose the province when applicable. Examples: Rizal; Cavite. NCR cities do not require a province.",
                    )}
                  />
                )}
              />
            ) : (
              <TextField fullWidth label="Province" {...field("province")} />
            )}
          </Grid>
          <Grid size={{ xs: 12, md: 4 }}>
            {regions.length ? (
              <Autocomplete
                disablePortal
                options={cities}
                value={selectedCity}
                disabled={!selectedRegion}
                getOptionLabel={(option) => option.name}
                onChange={(_, option) =>
                  onChange({
                    ...value,
                    city_municipality: option?.name ?? "",
                    postal_code: option?.postal_code || value.postal_code,
                  })
                }
                renderInput={(params) => (
                  <TextField
                    {...params}
                    required
                    label="City / municipality"
                    slotProps={autocompleteHelp(
                      params,
                      "City or municipality",
                      "Choose the official city or municipality. Examples: City of Pasig; City of Antipolo.",
                    )}
                  />
                )}
              />
            ) : (
              <TextField
                fullWidth
                required
                label="City / municipality"
                {...field("city_municipality")}
              />
            )}
          </Grid>
          <Grid size={12}>
            <TextField
              fullWidth
              required
              multiline
              rows={2}
              label="Street address"
              slotProps={help(
                "Street address",
                "Enter the building, street, and barangay details. Examples: Caruncho Avenue, Barangay San Nicolas; City Hall Complex, M.L. Quezon Street.",
              )}
              {...field("street_address")}
            />
          </Grid>
          <Grid size={{ xs: 12, md: 4 }}>
            <TextField
              fullWidth
              label="Postal code"
              slotProps={help(
                "Postal code",
                "Enter the four-digit Philippine postal code. Examples: 1600; 1900.",
              )}
              {...field("postal_code")}
            />
          </Grid>
          <Grid size={{ xs: 12, md: 4 }}>
            <TextField
              fullWidth
              label="PhilGEPS reference"
              slotProps={help(
                "PhilGEPS reference",
                "Enter the reference from the procurement notice, if available. Examples: PB-2027-001; RFQ-2027-014.",
              )}
              {...field("philgeps_reference")}
            />
          </Grid>
          <Grid size={{ xs: 12, md: 4 }}>
            <TextField
              fullWidth
              type="url"
              label="Source URL"
              slotProps={help(
                "Source URL",
                "Link to an official page that confirms the organization or procurement. Examples: a PhilGEPS notice page; the agency procurement page.",
              )}
              {...field("source_url")}
            />
          </Grid>
        </Grid>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={saving}>
          Cancel
        </Button>
        <Button
          variant="contained"
          onClick={onSave}
          disabled={
            saving ||
            !value.official_name.trim() ||
            !value.city_municipality.trim() ||
            !value.street_address.trim()
          }
        >
          {saving ? "Adding..." : "Add End-user"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

function EndUserFieldHelp({ label, text }: { label: string; text: string }) {
  const [anchor, setAnchor] = useState<HTMLElement | null>(null);
  return (
    <>
      <Tooltip title={`Help for ${label}`}>
        <IconButton
          size="small"
          aria-label={`Help for ${label}`}
          onClick={(event) => setAnchor(event.currentTarget)}
        >
          <InfoOutlinedIcon fontSize="small" />
        </IconButton>
      </Tooltip>
      <Popover
        open={Boolean(anchor)}
        anchorEl={anchor}
        onClose={() => setAnchor(null)}
        anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
      >
        <Typography sx={{ p: 2, maxWidth: 320 }}>{text}</Typography>
      </Popover>
    </>
  );
}

function ListAttachments({
  attachments,
  pending,
  onDeleteExisting,
  onDeletePending,
}: {
  attachments: Attachment[];
  pending: PendingAttachment[];
  onDeleteExisting: (item: Attachment) => void;
  onDeletePending: (index: number) => void;
}) {
  return (
    <Stack spacing={1} sx={{ mt: 2 }}>
      {attachments.map((item) => (
        <Stack key={item.id} direction="row" alignItems="center">
          <Link href={item.download_url} sx={{ flexGrow: 1 }}>
            {item.original_name}
          </Link>
          <IconButton
            aria-label={`Remove ${item.original_name}`}
            onClick={() => onDeleteExisting(item)}
          >
            <DeleteIcon />
          </IconButton>
        </Stack>
      ))}
      {pending.map((item, index) => (
        <Stack
          key={`${item.file.name}-${index}`}
          direction="row"
          alignItems="center"
        >
          <Typography sx={{ flexGrow: 1 }}>
            {item.file.name} (pending upload)
          </Typography>
          <IconButton
            aria-label={`Remove ${item.file.name}`}
            onClick={() => onDeletePending(index)}
          >
            <DeleteIcon />
          </IconButton>
        </Stack>
      ))}
    </Stack>
  );
}
