export type ApiError = {
  code: string;
  message: string;
  details: Array<{ field: string | null; message: string }>;
};

export type Session = {
  username: string;
  display_name: string;
  is_dbgi_admin: boolean;
  csrf_token: string;
};

export type RegistrationListItem = {
  id: number;
  reference: string;
  project_title: string;
  company_name: string;
  end_user_name: string;
  status: string;
  status_label: string;
  needs_review: boolean;
  created_at: string;
  version: number;
};

export type RegistrationPage = {
  items: RegistrationListItem[];
  total: number;
  page: number;
  page_size: number;
};

export type ProductOption = {
  id: number;
  code: string;
  name: string;
  category: string;
};

export type CompetitorItem = {
  id?: number;
  brand: string;
  item_name: string;
  bid_price: string;
  remarks: string;
};

export type RequestedItem = {
  id?: number;
  product_id: number | null;
  product_code?: string | null;
  product_name?: string | null;
  non_catalog_name: string;
  display_name?: string;
  quantity: number;
  requested_unit_price: string;
  justification: string;
};

export type Attachment = {
  id: number;
  original_name: string;
  description: string;
  uploaded_at: string;
  download_url: string;
};

export type RegistrationEvent = {
  id: number;
  event_type: string;
  details: string;
  actor_name: string;
  created_at: string;
};

export type RegistrationDetail = RegistrationListItem & {
  end_user_address: string;
  bid_date: string;
  delivery_date: string;
  contact_person: string;
  contact_designation: string;
  contact_email: string;
  contact_number: string;
  evidence_description: string;
  evidence_url: string;
  evidence_sharing_confirmed: boolean;
  can_edit: boolean;
  competitor_items: CompetitorItem[];
  items: RequestedItem[];
  attachments: Attachment[];
  events: RegistrationEvent[];
};

export type RegistrationPayload = {
  version?: number;
  end_user_name: string;
  end_user_address: string;
  project_title: string;
  bid_date: string;
  delivery_date: string;
  contact_person: string;
  contact_designation: string;
  contact_email: string;
  contact_number: string;
  evidence_description: string;
  evidence_url: string;
  evidence_sharing_confirmed: boolean;
  competitor_items: Omit<CompetitorItem, "id">[];
  items: Array<
    Omit<RequestedItem, "id" | "product_code" | "product_name" | "display_name">
  >;
};

export class RequestError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function request<T>(url: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(url, { credentials: "same-origin", signal });
  if (response.status === 401) {
    const next = encodeURIComponent(
      window.location.pathname + window.location.search,
    );
    window.location.assign(`/accounts/login/?next=${next}`);
    throw new RequestError("Sign in to continue.", 401);
  }
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as ApiError | null;
    throw new RequestError(
      body?.message ?? "The request could not be completed.",
      response.status,
    );
  }
  return response.json() as Promise<T>;
}

async function mutation<T>(
  url: string,
  method: "POST" | "PUT" | "DELETE",
  csrfToken: string,
  body?: BodyInit,
  contentType?: string,
): Promise<T> {
  const headers: HeadersInit = { "X-CSRFToken": csrfToken };
  if (contentType) headers["Content-Type"] = contentType;
  const response = await fetch(url, {
    method,
    credentials: "same-origin",
    headers,
    body,
  });
  if (response.status === 401) {
    window.location.assign("/accounts/login/");
    throw new RequestError("Sign in to continue.", 401);
  }
  if (!response.ok) {
    const result = (await response.json().catch(() => null)) as ApiError | null;
    throw new RequestError(
      result?.message ?? "The request could not be completed.",
      response.status,
    );
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export function getSession(signal?: AbortSignal) {
  return request<Session>("/api/v1/session", signal);
}

export function getRegistrations(
  page: number,
  pageSize: number,
  search: string,
  sort: string,
  signal?: AbortSignal,
) {
  const params = new URLSearchParams({
    page: String(page + 1),
    page_size: String(pageSize),
    search,
    sort,
  });
  return request<RegistrationPage>(`/api/v1/registrations?${params}`, signal);
}

export function getRegistration(id: number, signal?: AbortSignal) {
  return request<RegistrationDetail>(`/api/v1/registrations/${id}`, signal);
}

export function getProducts(signal?: AbortSignal) {
  return request<ProductOption[]>("/api/v1/products", signal);
}

export function createRegistration(
  payload: RegistrationPayload,
  csrfToken: string,
) {
  return mutation<RegistrationListItem>(
    "/api/v1/registrations",
    "POST",
    csrfToken,
    JSON.stringify(payload),
    "application/json",
  );
}

export function updateRegistration(
  id: number,
  payload: RegistrationPayload,
  csrfToken: string,
) {
  return mutation<RegistrationListItem>(
    `/api/v1/registrations/${id}`,
    "PUT",
    csrfToken,
    JSON.stringify(payload),
    "application/json",
  );
}

export function uploadAttachment(
  registrationId: number,
  file: File,
  description: string,
  csrfToken: string,
) {
  const data = new FormData();
  data.append("file", file);
  const params = new URLSearchParams({ description });
  return mutation<Attachment>(
    `/api/v1/registrations/${registrationId}/attachments?${params}`,
    "POST",
    csrfToken,
    data,
  );
}

export function deleteAttachment(id: number, csrfToken: string) {
  return mutation<void>(`/api/v1/attachments/${id}`, "DELETE", csrfToken);
}
