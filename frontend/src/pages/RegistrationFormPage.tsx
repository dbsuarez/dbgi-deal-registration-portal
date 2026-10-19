import AddIcon from "@mui/icons-material/Add";
import DeleteIcon from "@mui/icons-material/Delete";
import EditIcon from "@mui/icons-material/Edit";
import {
  Alert,
  Box,
  Breadcrumbs,
  Button,
  Checkbox,
  Container,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControlLabel,
  Grid,
  IconButton,
  Link,
  MenuItem,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";
import { useEffect, useMemo, useState, type FormEvent } from "react";
import { useNavigate, useParams } from "react-router-dom";

import {
  createRegistration,
  deleteAttachment,
  getProducts,
  getRegistration,
  type Attachment,
  type CompetitorItem,
  type ProductOption,
  type RegistrationPayload,
  type RequestedItem,
  updateRegistration,
  uploadAttachment,
} from "../api";
import { useSession } from "../session";

type MainFields = Omit<
  RegistrationPayload,
  "version" | "competitor_items" | "items"
>;
type PendingAttachment = { file: File; description: string };

const emptyMain: MainFields = {
  end_user_name: "",
  end_user_address: "",
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
  const [main, setMain] = useState<MainFields>(emptyMain);
  const [version, setVersion] = useState<number | undefined>();
  const [competitors, setCompetitors] = useState<CompetitorItem[]>([]);
  const [items, setItems] = useState<RequestedItem[]>([]);
  const [products, setProducts] = useState<ProductOption[]>([]);
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

  useEffect(() => {
    const controller = new AbortController();
    getProducts(controller.signal)
      .then(setProducts)
      .catch((reason: Error) => {
        if (reason.name !== "AbortError") setError(reason.message);
      });
    if (registrationId) {
      getRegistration(registrationId, controller.signal)
        .then((registration) => {
          if (!registration.can_edit)
            throw new Error("This account cannot edit registrations.");
          setMain({
            end_user_name: registration.end_user_name,
            end_user_address: registration.end_user_address,
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
  }, [registrationId]);

  useEffect(() => {
    const warn = (event: BeforeUnloadEvent) => {
      if (!dirty) return;
      event.preventDefault();
    };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [dirty]);

  const title = registrationId ? "Edit registration" : "New registration";
  const productMap = useMemo(
    () => new Map(products.map((product) => [product.id, product])),
    [products],
  );

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

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!competitors.length || !items.length) {
      setError("Add at least one competitor item and one requested product.");
      return;
    }
    setSaving(true);
    setError("");
    const payload: RegistrationPayload = {
      ...main,
      ...(registrationId ? { version } : {}),
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
      const saved = registrationId
        ? await updateRegistration(registrationId, payload, session.csrf_token)
        : await createRegistration(payload, session.csrf_token);
      for (const attachment of pendingAttachments) {
        await uploadAttachment(
          saved.id,
          attachment.file,
          attachment.description,
          session.csrf_token,
        );
      }
      for (const attachmentId of attachmentIdsToDelete) {
        await deleteAttachment(attachmentId, session.csrf_token);
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
        {registrationId && (
          <Link href={`/registrations/${registrationId}/`}>
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
      <Box component="form" onSubmit={submit}>
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h2" gutterBottom>
            Opportunity and contact
          </Typography>
          <Grid container spacing={2}>
            <Grid size={{ xs: 12, md: 6 }}>
              <TextField
                fullWidth
                required
                label="End user name"
                value={main.end_user_name}
                onChange={(e) => updateMain("end_user_name", e.target.value)}
              />
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <TextField
                fullWidth
                required
                label="Project opportunity title"
                value={main.project_title}
                onChange={(e) => updateMain("project_title", e.target.value)}
              />
            </Grid>
            <Grid size={12}>
              <TextField
                fullWidth
                required
                multiline
                rows={3}
                label="Complete address"
                value={main.end_user_address}
                onChange={(e) => updateMain("end_user_address", e.target.value)}
              />
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
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
            <Grid size={{ xs: 12, md: 6 }}>
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
                  registrationId ? `/registrations/${registrationId}/` : "/",
                );
            }}
          >
            Cancel
          </Button>
          <Button type="submit" variant="contained" disabled={saving}>
            {saving
              ? "Saving..."
              : registrationId
                ? "Save changes"
                : "Create registration"}
          </Button>
        </Stack>
      </Box>

      <CompetitorDialog
        open={competitorEditor !== null}
        value={competitorDraft}
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
    </Container>
  );
}

function CompetitorDialog({
  open,
  value,
  onChange,
  onClose,
  onSave,
}: {
  open: boolean;
  value: CompetitorItem;
  onChange: (value: CompetitorItem) => void;
  onClose: () => void;
  onSave: () => void;
}) {
  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle>Competitor item</DialogTitle>
      <DialogContent>
        <Grid container spacing={2} sx={{ pt: 1 }}>
          <Grid size={6}>
            <TextField
              autoFocus
              fullWidth
              required
              label="Brand"
              value={value.brand}
              onChange={(e) => onChange({ ...value, brand: e.target.value })}
            />
          </Grid>
          <Grid size={6}>
            <TextField
              fullWidth
              required
              label="Item / model"
              value={value.item_name}
              onChange={(e) =>
                onChange({ ...value, item_name: e.target.value })
              }
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
              onChange={(e) =>
                onChange({
                  ...value,
                  product_id: e.target.value ? Number(e.target.value) : null,
                  non_catalog_name: e.target.value
                    ? ""
                    : value.non_catalog_name,
                })
              }
            >
              <MenuItem value="">Not in catalog</MenuItem>
              {products.map((product) => (
                <MenuItem key={product.id} value={product.id}>
                  {product.code} - {product.name} ({product.category})
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
