import { expect, test, type Page } from "@playwright/test";

const session = {
  username: "dealer-a",
  display_name: "Dealer A",
  email: "dealer-a@example.invalid",
  designation: "Product Specialist",
  phone_number: "09170000000",
  is_dbgi_admin: false,
  is_debug: true,
  end_user_field_help_available: true,
  show_end_user_field_help: true,
  csrf_token: "test-token",
};

test.beforeEach(async ({ page }) => {
  let savedTestPresets: Array<Record<string, unknown>> = [];
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
        {
          id: 2,
          code: "P1820W",
          name: "20 ppm monochrome multifunction printer",
          category: "Laser Printers",
        },
      ],
    }),
  );
  await page.route("**/api/v1/competitor-brands", (route) =>
    route.fulfill({ json: ["Canon", "Epson", "HP", "Lexmark"] }),
  );
  await page.route("**/api/v1/competitor-models", (route) =>
    route.fulfill({
      json: [
        { brand: "Canon", item_name: "imageCLASS LBP246dw" },
        { brand: "HP", item_name: "LaserJet Pro 4003dn" },
      ],
    }),
  );
  await page.route(
    "**/api/v1/development/registration-test-presets**",
    async (route) => {
      const method = route.request().method();
      const id = Number(route.request().url().split("/").pop());
      if (method === "GET") return route.fulfill({ json: savedTestPresets });
      if (method === "POST") {
        const body = route.request().postDataJSON();
        const created = {
          id: 91,
          ...body,
          updated_at: "2026-10-22T06:00:00Z",
        };
        savedTestPresets = [...savedTestPresets, created];
        return route.fulfill({ status: 201, json: created });
      }
      if (method === "PUT") {
        const body = route.request().postDataJSON();
        const updated = {
          id,
          ...body,
          updated_at: "2026-10-22T06:05:00Z",
        };
        savedTestPresets = savedTestPresets.map((item) =>
          item.id === id ? updated : item,
        );
        return route.fulfill({ json: updated });
      }
      savedTestPresets = savedTestPresets.filter((item) => item.id !== id);
      return route.fulfill({ status: 204 });
    },
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
  await page.route("**/api/v1/geographic-dataset", (route) =>
    route.fulfill({
      json: {
        version: "2026-Q3",
        source_url: "https://psgc.cloud/api/v2",
        imported_at: "2026-10-22T06:30:00Z",
      },
    }),
  );
  await page.route("**/api/v1/end-user-classifications*", (route) => {
    const category = new URL(route.request().url()).searchParams.get(
      "category",
    );
    return route.fulfill({
      json:
        category === "organization_type"
          ? [{ name: "City government", status: "approved" }]
          : [{ name: "General government", status: "approved" }],
    });
  });
  await page.route("**/api/v1/geographic-areas*", (route) => {
    const level = new URL(route.request().url()).searchParams.get("level");
    if (level === "region") {
      return route.fulfill({
        json: [
          {
            code: "1300000000",
            name: "National Capital Region (NCR)",
            level: "region",
            area_type: "",
            postal_code: "",
          },
        ],
      });
    }
    if (level === "city_municipality") {
      return route.fulfill({
        json: [
          {
            code: "1307400000",
            name: "City of Pasig",
            level: "city_municipality",
            area_type: "City",
            postal_code: "1600",
          },
        ],
      });
    }
    return route.fulfill({ json: [] });
  });
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
  await expect(page.getByLabel("Contact person")).toHaveValue("Dealer A");
  await expect(page.getByLabel("Designation")).toHaveValue(
    "Product Specialist",
  );
  await expect(page.getByLabel("Contact email")).toHaveValue(
    "dealer-a@example.invalid",
  );
  await expect(page.getByLabel("Contact number")).toHaveValue("09170000000");
  await expect(
    page.getByRole("button", { name: "Add competitor" }),
  ).toBeVisible();
  await expect(page.getByRole("button", { name: "Add product" })).toBeVisible();

  await page.getByRole("button", { name: "Add competitor" }).click();
  await page.getByLabel("Brand").fill("Canon");
  await page.getByLabel("Item / model").click();
  await expect(
    page.getByRole("option", { name: "imageCLASS LBP246dw" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Cancel" }).click();

  await page.getByRole("button", { name: "Add missing End-user" }).click();
  const endUserDialog = page.getByRole("dialog", {
    name: "Add missing End-user",
  });
  await expect(
    endUserDialog.getByRole("button", { name: /^Help for / }),
  ).toHaveCount(12);
  await endUserDialog
    .getByRole("button", { name: "Help for Official name" })
    .click();
  await expect(
    page.getByText(
      /Examples: Department of Education; Pasig City General Services Office/,
    ),
  ).toBeVisible();
  await page.keyboard.press("Escape");
  await endUserDialog.getByRole("button", { name: "Cancel" }).click();
});

test("End-user location fields use cascading PSGC options", async ({
  page,
}) => {
  await page.goto("/registrations/new/");
  await page.getByRole("button", { name: "Add missing End-user" }).click();
  const endUserDialog = page.getByRole("dialog", {
    name: "Add missing End-user",
  });
  const regionField = endUserDialog.getByRole("combobox", { name: "Region" });
  await regionField.click();
  await page
    .locator(".MuiAutocomplete-option")
    .filter({ hasText: "National Capital Region (NCR)" })
    .click();
  const cityField = endUserDialog.getByRole("combobox", {
    name: "City / municipality",
  });
  await expect(cityField).toBeEnabled();
  await cityField.click();
  await page
    .locator(".MuiAutocomplete-option")
    .filter({ hasText: "City of Pasig" })
    .click();
  await expect(
    endUserDialog.getByRole("textbox", { name: "Postal code" }),
  ).toHaveValue("1600");
  await endUserDialog.getByRole("button", { name: "Cancel" }).click();
});

test("End-user classification fields use controlled and proposal lists", async ({
  page,
}) => {
  await page.goto("/registrations/new/");
  await page.getByRole("button", { name: "Add missing End-user" }).click();
  const dialog = page.getByRole("dialog", { name: "Add missing End-user" });

  await dialog.getByRole("combobox", { name: "Government branch" }).click();
  await page.getByText("Local government", { exact: true }).click();
  await dialog
    .getByRole("combobox", { name: "Organization type" })
    .fill("City government");
  await expect(
    page
      .locator(".MuiAutocomplete-option")
      .filter({ hasText: "City government" }),
  ).toBeVisible();
  await dialog.getByRole("combobox", { name: "Sector" }).fill("New sector");
  await expect(
    dialog.getByText(
      "A new value will be sent to an administrator for approval.",
    ),
  ).toHaveCount(2);
});

test("superadmin setting can hide End-user field help", async ({ page }) => {
  await page.route("**/api/v1/session", (route) =>
    route.fulfill({
      json: {
        ...session,
        end_user_field_help_available: false,
        show_end_user_field_help: false,
      },
    }),
  );
  await page.goto("/registrations/new/");

  await page.getByRole("button", { name: "Add missing End-user" }).click();

  const dialog = page.getByRole("dialog", { name: "Add missing End-user" });
  await expect(dialog.getByRole("button", { name: /^Help for / })).toHaveCount(
    0,
  );
  await expect(
    dialog.getByRole("switch", { name: "Show field information buttons" }),
  ).toHaveCount(0);
});

test("user can hide End-user field help and keep the preference", async ({
  page,
}) => {
  let showFieldHelp = true;
  await page.route(
    "**/api/v1/session/preferences/end-user-field-help",
    async (route) => {
      showFieldHelp = route.request().postDataJSON().show_end_user_field_help;
      await route.fulfill({
        json: { show_end_user_field_help: showFieldHelp },
      });
    },
  );
  await page.goto("/registrations/new/");
  await page.getByRole("button", { name: "Add missing End-user" }).click();
  const dialog = page.getByRole("dialog", { name: "Add missing End-user" });
  const toggle = dialog.getByRole("switch", {
    name: "Show field information buttons",
  });

  await expect(toggle).toBeChecked();
  await toggle.click();
  await expect(toggle).not.toBeChecked();
  await expect(dialog.getByRole("button", { name: /^Help for / })).toHaveCount(
    0,
  );
  await dialog.getByRole("button", { name: "Cancel" }).click();
  await page.getByRole("button", { name: "Add missing End-user" }).click();

  await expect(
    page
      .getByRole("dialog", { name: "Add missing End-user" })
      .getByRole("switch", { name: "Show field information buttons" }),
  ).not.toBeChecked();
  expect(showFieldHelp).toBe(false);
});

test("debug test-data panel fills five registration scenarios", async ({
  page,
}) => {
  await page.goto("/registrations/new/");

  await page.getByRole("button", { name: "Test data", exact: true }).click();
  const drawer = page.getByRole("presentation").filter({
    has: page.getByRole("heading", { name: "Registration test data" }),
  });
  await expect(drawer.getByText("Pasig competing bid A")).toBeVisible();
  await expect(drawer.getByText("Pasig competing bid B")).toBeVisible();
  await expect(
    drawer.getByRole("button", { name: "Fill this registration" }),
  ).toHaveCount(5);

  await drawer
    .getByRole("button", { name: "Fill this registration" })
    .first()
    .click();

  await expect(page.getByLabel("Project opportunity title")).toHaveValue(
    "Pasig Schools Printer Procurement A",
  );
  await expect(page.getByLabel("End-user")).toHaveValue(
    "Sample municipality (SM)",
  );
  await expect(page.getByText("LaserJet Pro 4003dn")).toBeVisible();
  await expect(page.getByText(/P1820W/)).toBeVisible();
  await expect(
    page.getByLabel(
      "I confirm that I am authorized to share this evidence with DBGI for review.",
    ),
  ).toBeChecked();
  await expect(
    page.getByText(/Loaded test data: Pasig competing bid A/),
  ).toBeVisible();

  await page.getByRole("button", { name: "Save as test data" }).click();
  await page.getByLabel("Test data name").fill("My Pasig test");
  await page
    .getByRole("textbox", { name: "Description", exact: true })
    .fill("Reusable test registration");
  await page.getByRole("button", { name: "Save test data" }).click();
  await page.getByRole("button", { name: "Test data", exact: true }).click();
  await expect(page.getByText("My Pasig test", { exact: true })).toBeVisible();

  const savedCard = page
    .getByText("My Pasig test", { exact: true })
    .locator("..");
  await savedCard.getByRole("button", { name: "Edit" }).click();
  await expect(
    page.getByRole("button", { name: "Update test data" }),
  ).toBeVisible();
  await page.getByLabel("Project opportunity title").fill("Updated Pasig test");
  await page.getByRole("button", { name: "Update test data" }).click();
  await page.getByRole("button", { name: "Test data", exact: true }).click();
  await page
    .getByText("My Pasig test", { exact: true })
    .locator("..")
    .getByRole("button", { name: "Delete" })
    .click();
  await page.getByRole("button", { name: "Delete test data" }).click();
  await expect(page.getByText("My Pasig test", { exact: true })).toHaveCount(0);
});

test("test-data panel is hidden outside debug mode", async ({ page }) => {
  await page.route("**/api/v1/session", (route) =>
    route.fulfill({ json: { ...session, is_debug: false } }),
  );

  await page.goto("/registrations/new/");

  await expect(
    page.getByRole("button", { name: "Test data", exact: true }),
  ).toHaveCount(0);
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

  await page.getByRole("button", { name: "Clear all filters" }).click();
  await expect(
    page.getByRole("combobox", { name: "Project status" }),
  ).toHaveText("All Project Statuses");
  await expect(
    page.getByRole("combobox", { name: "Registration status" }),
  ).toHaveText("All Registration Statuses");
});

test("advanced filters can be cleared from the grid toolbar", async ({
  page,
}) => {
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

  const clearAdvancedFilters = page.getByRole("button", {
    name: "Clear filters",
    exact: true,
  });
  await expect(clearAdvancedFilters).toBeDisabled();

  await page.getByRole("button", { name: "Show filters" }).click();
  await page.getByLabel("Value").fill("Municipal");
  await expect(clearAdvancedFilters).toBeEnabled();

  await clearAdvancedFilters.click();

  await expect(clearAdvancedFilters).toBeDisabled();
  await expect(page.getByLabel("Value")).toHaveCount(0);
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

test("competitor dialog supports keyboard focus and Escape restoration", async ({
  page,
}) => {
  await page.goto("/registrations/new/");
  const trigger = page.getByRole("button", { name: "Add competitor" });

  await trigger.focus();
  await page.keyboard.press("Enter");

  const dialog = page.getByRole("dialog", { name: "Competitor item" });
  await expect(dialog).toBeVisible();
  await expect(page.getByLabel("Brand")).toBeFocused();

  await page.keyboard.press("Escape");

  await expect(dialog).toBeHidden();
  await expect(trigger).toBeFocused();
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
  const explainButton = page.getByLabel("Explain opportunity rankings");
  await explainButton.focus();
  await page.keyboard.press("Enter");
  const dialog = page.getByRole("dialog", { name: "How ranking works" });
  await expect(dialog).toBeVisible();
  await expect(dialog.getByRole("button", { name: "Close" })).toBeFocused();

  await page.keyboard.press("Escape");

  await expect(dialog).toBeHidden();
  await expect(explainButton).toBeFocused();
});

test("ranking request failure is announced as an alert", async ({ page }) => {
  await page.route("**/api/v1/session", (route) =>
    route.fulfill({
      json: { ...session, is_dbgi_admin: true, display_name: "DBGI Admin" },
    }),
  );
  await page.route("**/api/v1/rankings?**", (route) =>
    route.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({
        code: "service_unavailable",
        message: "Rankings are temporarily unavailable.",
      }),
    }),
  );

  await page.goto("/rankings/");

  await expect(page.getByRole("alert")).toContainText(
    "Rankings are temporarily unavailable.",
  );
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
    project_status: null,
    project_status_label: "Not linked",
    price_status: "pending",
    price_status_label: "Pending",
    needs_review: true,
    created_at: "2026-10-19T02:00:00Z",
    version: 1,
    can_edit: false,
    competitor_items: [],
    items: [],
    attachments: [],
    events: [],
    opportunity_scope_id: null,
    opportunity_scope_label: null,
    category_approvals: [],
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
  await page.getByText("Submitted", { exact: true }).hover();
  await expect(
    page.getByRole("tooltip", { name: /DBGI received this registration/ }),
  ).toBeVisible();
  await page.getByText("Project: Not linked", { exact: true }).hover();
  await expect(
    page.getByRole("tooltip", {
      name: /not connected to a shared project opportunity/,
    }),
  ).toBeVisible();
  await page.getByText("Pricing: Pending", { exact: true }).hover();
  await expect(
    page.getByRole("tooltip", {
      name: /has not made a final pricing decision/,
    }),
  ).toBeVisible();
  await page.getByText("Review required", { exact: true }).hover();
  await expect(
    page.getByRole("tooltip", {
      name: /A DBGI administrator must review this registration/,
    }),
  ).toBeVisible();
  await page.getByLabel("Explain matching suggestion").click();
  await expect(
    page.getByRole("heading", { name: "Why this match was suggested" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Close" }).click();
  await page.getByLabel("Decision reason").fill("Evidence review started.");
  await page.getByRole("button", { name: "Start review" }).click();
  await expect(page.getByText("Under review", { exact: true })).toBeVisible();
});
