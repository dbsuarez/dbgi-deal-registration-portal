import { expect, test, type Page } from "@playwright/test";

const session = {
  username: "dealer-a",
  display_name: "Dealer A",
  is_dbgi_admin: false,
  csrf_token: "test-token",
};

test.beforeEach(async ({ page }) => {
  await page.route("**/api/v1/session", (route) =>
    route.fulfill({ json: session }),
  );
  await page.route("**/api/v1/products", (route) =>
    route.fulfill({
      json: [
        {
          id: 1,
          code: "M1820W",
          name: "20 ppm monochrome laser printer",
          category: "Laser Printers",
        },
      ],
    }),
  );
  await page.route("**/api/v1/competitor-brands", (route) =>
    route.fulfill({ json: ["Canon", "Epson", "HP", "Lexmark"] }),
  );
  await page.route("**/api/v1/end-users", (route) =>
    route.fulfill({
      json: [
        {
          id: 7,
          official_name: "Sample municipality",
          acronym: "SM",
          full_address: "Test address, Sample City",
          government_branch: "Local government",
          organization_type: "City",
          sector: "Government",
          region: "",
          province: "",
          city_municipality: "Sample City",
          street_address: "Test address",
          postal_code: "",
          philgeps_reference: "",
          source_url: "",
          status: "verified",
          status_label: "Verified",
        },
      ],
    }),
  );
});

async function fillCompleteRegistration(page: Page) {
  await page.goto("/registrations/new/");
  await page.getByLabel("End-user").click();
  await page.getByRole("option", { name: /Sample municipality/ }).click();
  await page
    .getByLabel("Project opportunity title")
    .fill("Municipal printer project");
  await page.getByLabel("Bid date").fill("2026-11-30");
  await page.getByLabel("Delivery date").fill("2027-01-30");
  await page.getByLabel("Contact person").fill("Test person");
  await page.getByLabel("Designation").fill("Buyer");
  await page.getByLabel("Contact email").fill("test@example.invalid");
  await page.getByLabel("Contact number").fill("0000000000");

  await page.getByRole("button", { name: "Add competitor" }).click();
  await page.getByLabel("Brand").fill("Brand X");
  await page.getByLabel("Item / model").fill("Model Y");
  await page.getByLabel("Bid price").fill("100.00");
  await page.getByRole("button", { name: "Save item" }).click();

  await page.getByRole("button", { name: "Add product" }).click();
  await page.getByRole("combobox", { name: "Catalog product" }).click();
  await page.getByRole("option", { name: /M1820W/ }).click();
  await page.getByLabel("Quantity").fill("2");
  await page.getByLabel("Requested unit price").fill("90.00");
  await page.getByLabel("Justification").fill("Project request");
  await page.getByRole("button", { name: "Save item" }).click();

  await page
    .getByLabel("Evidence description")
    .fill("Public procurement notice");
  await page.getByRole("checkbox").check();
}

test("authenticated user can log out", async ({ page }) => {
  await page.route("**/api/v1/registrations?**", (route) =>
    route.fulfill({ json: { items: [], total: 0, page: 1, page_size: 25 } }),
  );
  await page.route("**/api/v1/session/logout", async (route) => {
    expect(route.request().method()).toBe("POST");
    expect(route.request().headers()["x-csrftoken"]).toBe("test-token");
    await route.fulfill({ status: 204 });
  });

  await page.goto("/");
  await page.getByRole("button", { name: "Log out" }).click();

  await expect(page).toHaveURL(/\/accounts\/login\/$/);
});

test("unknown route shows the application not-found page", async ({ page }) => {
  await page.goto("/missing-page/");

  await expect(
    page.getByRole("heading", { name: "Page not found" }),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: "Go to registrations" }),
  ).toHaveAttribute("href", "/");
});

test("company user can open the React registration form", async ({ page }) => {
  await page.route("**/api/v1/registrations?**", (route) =>
    route.fulfill({ json: { items: [], total: 0, page: 1, page_size: 25 } }),
  );

  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Deal registrations" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "New registration" }).click();
  await expect(
    page.getByRole("heading", { name: "New registration" }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Add competitor" }),
  ).toBeVisible();
  await expect(page.getByRole("button", { name: "Add product" })).toBeVisible();
});

test("quick status filters compose and clear", async ({ page }) => {
  await page.route("**/api/v1/registrations?**", (route) =>
    route.fulfill({
      json: {
        items: [],
        total: 0,
        page: 1,
        page_size: 25,
        grand_total: "0.00",
      },
    }),
  );
  await page.goto("/");

  await page.getByRole("combobox", { name: "Project status" }).click();
  const projectRequest = page.waitForRequest((request) =>
    request.url().includes("project_status=active"),
  );
  await page.getByRole("option", { name: "Active" }).click();
  await projectRequest;

  await page.getByRole("combobox", { name: "Registration status" }).click();
  const combinedRequest = page.waitForRequest(
    (request) =>
      request.url().includes("project_status=active") &&
      request.url().includes("registration_status=under_review"),
  );
  await page.getByRole("option", { name: "Under review" }).click();
  await combinedRequest;

  await page.getByRole("button", { name: "Clear filters" }).click();
  await expect(
    page.getByRole("combobox", { name: "Project status" }),
  ).toHaveText("All Project Statuses");
  await expect(
    page.getByRole("combobox", { name: "Registration status" }),
  ).toHaveText("All Registration Statuses");
});

test("company user can submit a complete registration", async ({ page }) => {
  await page.route("**/api/v1/registrations", async (route) => {
    if (route.request().method() !== "POST") return route.fallback();
    const payload = route.request().postDataJSON();
    expect(payload.competitor_items).toHaveLength(1);
    expect(payload.items).toHaveLength(1);
    expect(payload.end_user_id).toBe(7);
    await route.fulfill({
      status: 201,
      json: {
        id: 21,
        reference: "DBGI-000021",
        project_title: payload.project_title,
        company_name: "North Dealer",
        end_user_name: "Sample municipality",
        end_user_id: 7,
        end_user_status: "verified",
        end_user_status_label: "Verified",
        status: "submitted",
        status_label: "Submitted",
        needs_review: false,
        created_at: "2026-10-19T02:00:00Z",
        version: 1,
      },
    });
  });
  await page.route("**/api/v1/registrations/21", (route) =>
    route.fulfill({
      json: {
        id: 21,
        reference: "DBGI-000021",
        project_title: "Municipal printer project",
        company_name: "North Dealer",
        end_user_name: "Sample municipality",
        end_user_id: 7,
        end_user_status: "verified",
        end_user_status_label: "Verified",
        end_user_address: "Test address",
        bid_date: "2026-11-30",
        delivery_date: "2027-01-30",
        contact_person: "Test person",
        contact_designation: "Buyer",
        contact_email: "test@example.invalid",
        contact_number: "0000000000",
        evidence_description: "Public procurement notice",
        evidence_url: "",
        evidence_sharing_confirmed: true,
        status: "submitted",
        status_label: "Submitted",
        needs_review: false,
        created_at: "2026-10-19T02:00:00Z",
        version: 1,
        can_edit: true,
        competitor_items: [
          {
            id: 1,
            brand: "Brand X",
            item_name: "Model Y",
            bid_price: "100.00",
            remarks: "",
          },
        ],
        items: [
          {
            id: 1,
            product_id: 1,
            product_code: "M1820W",
            product_name: "20 ppm monochrome laser printer",
            non_catalog_name: "",
            display_name: "M1820W - 20 ppm monochrome laser printer",
            quantity: 2,
            requested_unit_price: "90.00",
            justification: "Project request",
          },
        ],
        attachments: [],
        events: [],
      },
    }),
  );

  await fillCompleteRegistration(page);
  await page.getByRole("button", { name: "Create registration" }).click();

  await expect(page).toHaveURL(/\/registrations\/21\/$/);
  await expect(
    page.getByRole("heading", { name: "Municipal printer project" }),
  ).toBeVisible();
});

test("failed evidence upload retries the same registration", async ({
  page,
}) => {
  let createCount = 0;
  let updateCount = 0;
  let uploadCount = 0;
  let finalizeCount = 0;
  const registrationResponse = (version: number) => ({
    id: 31,
    reference: "DBGI-000031",
    project_title: "Municipal printer project",
    company_name: "North Dealer",
    end_user_name: "Sample municipality",
    end_user_id: 7,
    end_user_status: "verified",
    end_user_status_label: "Verified",
    status: "submitted",
    status_label: "Submitted",
    needs_review: false,
    created_at: "2026-10-20T08:00:00Z",
    version,
  });

  await page.route("**/api/v1/registrations", async (route) => {
    if (route.request().method() !== "POST") return route.fallback();
    createCount += 1;
    await route.fulfill({ status: 201, json: registrationResponse(1) });
  });
  await page.route("**/api/v1/registrations/31", async (route) => {
    if (route.request().method() !== "PUT") return route.fallback();
    updateCount += 1;
    expect(route.request().postDataJSON().version).toBe(1);
    await route.fulfill({ json: registrationResponse(2) });
  });
  await page.route(
    "**/api/v1/registrations/31/attachments?**",
    async (route) => {
      uploadCount += 1;
      const version = new URL(route.request().url()).searchParams.get(
        "version",
      );
      expect(version).toBe(uploadCount === 1 ? "1" : "2");
      if (uploadCount === 1) {
        await route.fulfill({
          status: 503,
          json: {
            code: "temporary_failure",
            message: "Upload interrupted.",
            details: [],
          },
        });
        return;
      }
      await route.fulfill({
        status: 201,
        json: {
          id: 9,
          original_name: "evidence.pdf",
          description: "",
          uploaded_at: "2026-10-20T08:01:00Z",
          download_url: "/attachments/9/download/",
        },
      });
    },
  );
  await page.route("**/api/v1/registrations/31/finalize", async (route) => {
    finalizeCount += 1;
    expect(route.request().postDataJSON()).toEqual({
      version: 2,
      evidence_changed: true,
    });
    await route.fulfill({ json: registrationResponse(3) });
  });

  await fillCompleteRegistration(page);
  await page.locator('input[type="file"]').setInputFiles({
    name: "evidence.pdf",
    mimeType: "application/pdf",
    buffer: Buffer.from("%PDF-1.7 test"),
  });
  await page.getByRole("button", { name: "Create registration" }).click();
  await expect(page.getByText("Upload interrupted.")).toBeVisible();

  await page.getByRole("button", { name: "Save changes" }).click();
  await expect(page).toHaveURL(/\/registrations\/31\/$/);
  expect(createCount).toBe(1);
  expect(updateCount).toBe(1);
  expect(uploadCount).toBe(2);
  expect(finalizeCount).toBe(1);
});

test("DBGI administrator can view opportunity rankings", async ({ page }) => {
  await page.route("**/api/v1/session", (route) =>
    route.fulfill({
      json: { ...session, is_dbgi_admin: true, display_name: "DBGI Admin" },
    }),
  );
  await page.route("**/api/v1/rankings?**", (route) =>
    route.fulfill({
      json: {
        items: [
          {
            opportunity_id: 1,
            opportunity_title:
              "Quezon City Public Schools Printer Procurement 2027",
            end_user_name: "Quezon City Schools Division Office",
            scope_id: 1,
            scope_name: "Lot 1: Monochrome laser printers",
            scope_type: "lot",
            participant_count: 2,
            entries: [
              {
                rank: 1,
                is_tied: false,
                registration_id: 2,
                reference: "DBGI-000002",
                company_name: "IT Avenue",
                project_title: "QCS Division Office laser printer acquisition",
                original_submitted_at: "2026-10-19T03:22:55Z",
              },
              {
                rank: 2,
                is_tied: false,
                registration_id: 3,
                reference: "DBGI-000003",
                company_name: "Lexmark",
                project_title: "Quezon City SDO monochrome printer project",
                original_submitted_at: "2026-10-19T04:22:55Z",
              },
            ],
          },
        ],
        total: 1,
        page: 1,
        page_size: 25,
      },
    }),
  );

  await page.goto("/rankings/");

  await expect(
    page.getByRole("heading", { name: "Opportunity rankings" }),
  ).toBeVisible();
  await expect(page.getByText("IT Avenue", { exact: true })).toBeVisible();
  await expect(page.getByText("Lexmark", { exact: true })).toBeVisible();
  await page.getByLabel("Explain opportunity rankings").click();
  await expect(
    page.getByRole("heading", { name: "How ranking works" }),
  ).toBeVisible();
});

test("DBGI administrator can inspect a suggestion and start review", async ({
  page,
}) => {
  await page.route("**/api/v1/session", (route) =>
    route.fulfill({
      json: { ...session, is_dbgi_admin: true, display_name: "DBGI Admin" },
    }),
  );
  const detail = {
    id: 1,
    reference: "DBGI-000001",
    project_title: "Municipal printer project",
    company_name: "North Dealer",
    end_user_name: "Sample municipality",
    end_user_address: "Test address",
    bid_date: "2026-11-30",
    delivery_date: "2027-01-30",
    contact_person: "Test person",
    contact_designation: "Buyer",
    contact_email: "test@example.invalid",
    contact_number: "0000000000",
    evidence_description: "Public procurement notice",
    evidence_url: "",
    evidence_sharing_confirmed: true,
    status: "submitted",
    status_label: "Submitted",
    needs_review: false,
    created_at: "2026-10-19T02:00:00Z",
    version: 1,
    can_edit: false,
    competitor_items: [],
    items: [],
    attachments: [],
    events: [],
    opportunity_scope_id: null,
    opportunity_scope_label: null,
    matching_suggestion: {
      id: 1,
      outcome: "clarify",
      outcome_label: "Request clarification",
      confidence: "medium",
      confidence_label: "Medium",
      score: 58,
      supporting_factors: ["The end-user names closely match."],
      conflicting_factors: ["No requested catalog product overlap was found."],
      rule_version: "matching-v1",
      candidate_scope_id: null,
      candidate_scope_label: null,
      created_at: "2026-10-19T02:00:00Z",
    },
  };
  await page.route("**/api/v1/review/opportunity-scopes", (route) =>
    route.fulfill({ json: [] }),
  );
  await page.route("**/api/v1/registrations/1", (route) =>
    route.fulfill({ json: detail }),
  );
  await page.route(
    "**/api/v1/review/registrations/1/decision",
    async (route) => {
      const payload = route.request().postDataJSON();
      expect(payload.decision).toBe("start_review");
      expect(payload.rationale).toBe("Evidence review started.");
      await route.fulfill({
        json: {
          ...detail,
          status: "under_review",
          status_label: "Under review",
          version: 2,
        },
      });
    },
  );

  await page.goto("/registrations/1/");
  await page.getByLabel("Explain matching suggestion").click();
  await expect(
    page.getByRole("heading", { name: "Why this match was suggested" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Close" }).click();
  await page.getByLabel("Decision reason").fill("Evidence review started.");
  await page.getByRole("button", { name: "Start review" }).click();
  await expect(page.getByText("Under review", { exact: true })).toBeVisible();
});
