import { expect, test } from "@playwright/test";

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

test("company user can submit a complete registration", async ({ page }) => {
  await page.route("**/api/v1/registrations", async (route) => {
    if (route.request().method() !== "POST") return route.fallback();
    const payload = route.request().postDataJSON();
    expect(payload.competitor_items).toHaveLength(1);
    expect(payload.items).toHaveLength(1);
    await route.fulfill({
      status: 201,
      json: {
        id: 21,
        reference: "DBGI-000021",
        project_title: payload.project_title,
        company_name: "North Dealer",
        end_user_name: payload.end_user_name,
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

  await page.goto("/registrations/new/");
  await page.getByLabel("End user name").fill("Sample municipality");
  await page
    .getByLabel("Project opportunity title")
    .fill("Municipal printer project");
  await page.getByLabel("Complete address").fill("Test address");
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
  await page.getByRole("button", { name: "Create registration" }).click();

  await expect(page).toHaveURL(/\/registrations\/21\/$/);
  await expect(
    page.getByRole("heading", { name: "Municipal printer project" }),
  ).toBeVisible();
});
