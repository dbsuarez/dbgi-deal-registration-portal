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
  end_user_id: number | null;
  end_user_status: string | null;
  end_user_status_label: string | null;
  status: string;
  status_label: string;
  project_status: string | null;
  project_status_label: string;
  price_status: string;
  price_status_label: string;
  total_requested_value: string;
  bid_date: string;
  age_days: number;
  needs_review: boolean;
  created_at: string;
  version: number;
};

export type RegistrationPage = {
  items: RegistrationListItem[];
  total: number;
  page: number;
  page_size: number;
  grand_total: string;
};

export type ProductOption = {
  id: number;
  code: string;
  name: string;
  category: string;
  currency: string;
  list_price: string;
};

export type EndUser = {
  id: number;
  official_name: string;
  acronym: string;
  full_address: string;
  government_branch: string;
  organization_type: string;
  sector: string;
  region: string;
  province: string;
  city_municipality: string;
  street_address: string;
  postal_code: string;
  philgeps_reference: string;
  source_url: string;
  status: string;
  status_label: string;
};

export type EndUserCreatePayload = Omit<
  EndUser,
  "id" | "full_address" | "status" | "status_label"
>;

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
  currency?: string;
  list_unit_price?: string;
  requested_discount_percent?: string | null;
  requested_total?: string;
  approved_unit_price?: string | null;
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

export type MatchingSuggestion = {
  id: number;
  outcome: string;
  outcome_label: string;
  confidence: string;
  confidence_label: string;
  score: number;
  supporting_factors: string[];
  conflicting_factors: string[];
  rule_version: string;
  candidate_scope_id: number | null;
  candidate_scope_label: string | null;
  created_at: string;
};

export type OpportunityScope = {
  id: number;
  opportunity_id: number;
  opportunity_title: string;
  name: string;
  scope_type: string;
  label: string;
};

export type RankingEntry = {
  rank: number;
  is_tied: boolean;
  registration_id: number;
  reference: string;
  company_name: string;
  project_title: string;
  original_submitted_at: string;
};

export type OpportunityRanking = {
  opportunity_id: number;
  opportunity_title: string;
  end_user_name: string;
  scope_id: number;
  scope_name: string;
  scope_type: string;
  participant_count: number;
  entries: RankingEntry[];
};

export type OpportunityRankingPage = {
  items: OpportunityRanking[];
  total: number;
  page: number;
  page_size: number;
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
  opportunity_scope_id: number | null;
  opportunity_scope_label: string | null;
  matching_suggestion: MatchingSuggestion | null;
  category_approvals: CategoryApproval[];
};

export type CategoryApproval = {
  id: number;
  category: string;
  status: string;
  status_label: string;
  rationale: string;
  reviewed_by: string | null;
  reviewed_at: string | null;
  valid_until: string | null;
  version: number;
};

export type RegistrationPayload = {
  version?: number;
  end_user_id: number;
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
  readonly code: string;
  readonly details: ApiError["details"];

  constructor(
    message: string,
    status: number,
    code = "request_failed",
    details: ApiError["details"] = [],
  ) {
    super(message);
    this.name = "RequestError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

function requestError(response: Response, body: ApiError | null) {
  return new RequestError(
    body?.message ?? "The request could not be completed.",
    response.status,
    body?.code,
    body?.details,
  );
}

function redirectToLogin() {
  const next = encodeURIComponent(
    window.location.pathname + window.location.search,
  );
  window.location.assign(`/accounts/login/?next=${next}`);
}

async function request<T>(url: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(url, { credentials: "same-origin", signal });
  if (response.status === 401) {
    redirectToLogin();
    throw new RequestError("Sign in to continue.", 401);
  }
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as ApiError | null;
    throw requestError(response, body);
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
    redirectToLogin();
    throw new RequestError("Sign in to continue.", 401);
  }
  if (!response.ok) {
    const result = (await response.json().catch(() => null)) as ApiError | null;
    throw requestError(response, result);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export function getSession(signal?: AbortSignal) {
  return request<Session>("/api/v1/session", signal);
}

export function logoutSession(csrfToken: string) {
  return mutation<void>("/api/v1/session/logout", "POST", csrfToken);
}

export function getRegistrations(
  page: number,
  pageSize: number,
  search: string,
  sort: string,
  projectStatus: string,
  registrationStatus: string,
  signal?: AbortSignal,
) {
  const params = new URLSearchParams({
    page: String(page + 1),
    page_size: String(pageSize),
    search,
    sort,
  });
  if (projectStatus) params.set("project_status", projectStatus);
  if (registrationStatus) params.set("registration_status", registrationStatus);
  return request<RegistrationPage>(`/api/v1/registrations?${params}`, signal);
}

export function getRegistration(id: number, signal?: AbortSignal) {
  return request<RegistrationDetail>(`/api/v1/registrations/${id}`, signal);
}

export function getProducts(signal?: AbortSignal) {
  return request<ProductOption[]>("/api/v1/products", signal);
}

export function getCompetitorBrands(signal?: AbortSignal) {
  return request<string[]>("/api/v1/competitor-brands", signal);
}

export function getEndUsers(signal?: AbortSignal) {
  return request<EndUser[]>("/api/v1/end-users", signal);
}

export function createEndUser(
  payload: EndUserCreatePayload,
  csrfToken: string,
) {
  return mutation<EndUser>(
    "/api/v1/end-users",
    "POST",
    csrfToken,
    JSON.stringify(payload),
    "application/json",
  );
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
  version: number,
  csrfToken: string,
) {
  const data = new FormData();
  data.append("file", file);
  const params = new URLSearchParams({
    description,
    version: String(version),
  });
  return mutation<Attachment>(
    `/api/v1/registrations/${registrationId}/attachments?${params}`,
    "POST",
    csrfToken,
    data,
  );
}

export function deleteAttachment(
  id: number,
  version: number,
  csrfToken: string,
) {
  const params = new URLSearchParams({ version: String(version) });
  return mutation<void>(
    `/api/v1/attachments/${id}?${params}`,
    "DELETE",
    csrfToken,
  );
}

export function finalizeRegistration(
  id: number,
  version: number,
  evidenceChanged: boolean,
  csrfToken: string,
) {
  return mutation<RegistrationListItem>(
    `/api/v1/registrations/${id}/finalize`,
    "POST",
    csrfToken,
    JSON.stringify({ version, evidence_changed: evidenceChanged }),
    "application/json",
  );
}

export function getOpportunityScopes(signal?: AbortSignal) {
  return request<OpportunityScope[]>(
    "/api/v1/review/opportunity-scopes",
    signal,
  );
}

export function getOpportunityRankings(
  page: number,
  pageSize: number,
  search: string,
  signal?: AbortSignal,
) {
  const params = new URLSearchParams({
    page: String(page + 1),
    page_size: String(pageSize),
  });
  if (search) params.set("search", search);
  return request<OpportunityRankingPage>(`/api/v1/rankings?${params}`, signal);
}

export function refreshMatchingSuggestion(
  registrationId: number,
  csrfToken: string,
) {
  return mutation<MatchingSuggestion>(
    `/api/v1/review/registrations/${registrationId}/suggestion`,
    "POST",
    csrfToken,
  );
}

export function reviewRegistration(
  registrationId: number,
  payload: {
    version: number;
    decision: "start_review" | "request_changes" | "confirm_match" | "reject";
    rationale: string;
    opportunity_scope_id?: number | null;
    create_new_opportunity?: boolean;
  },
  csrfToken: string,
) {
  return mutation<RegistrationDetail>(
    `/api/v1/review/registrations/${registrationId}/decision`,
    "POST",
    csrfToken,
    JSON.stringify(payload),
    "application/json",
  );
}
