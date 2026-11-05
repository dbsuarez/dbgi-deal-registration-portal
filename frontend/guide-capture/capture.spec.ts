import {
  expect,
  test,
  type Browser,
  type Locator,
  type Page,
} from "@playwright/test";

// Walks the example deal through the real screens and saves the guide's screenshots.
// Reseed first; see docs/guides/_source/README.txt.
const SHOTS = "../docs/guides/_source/shots2";
const PASSWORD = "demo-guide-password-1";
const DEAL = "20 laser printers for the Mayor's Office";

async function settle(page: Page) {
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout(400);
}

async function shot(page: Page, name: string) {
  await settle(page);
  await page.screenshot({ path: `${SHOTS}/${name}.png` });
}

async function clip(page: Page, target: Locator, name: string) {
  await settle(page);
  await target.first().scrollIntoViewIfNeeded();
  await target.first().screenshot({ path: `${SHOTS}/${name}.png` });
}

async function dialog(page: Page, name: string) {
  await clip(page, page.getByRole("dialog"), name);
}

// The paper card around a heading, for shooting one section of a page.
function section(page: Page, heading: string | RegExp) {
  return page
    .getByRole("heading", { name: heading })
    .first()
    .locator("xpath=ancestor::*[contains(@class,'MuiPaper-root')][1]");
}

// The test-data tools only exist on the developer server, so readers never see them.
async function hideTestData(page: Page) {
  await page.addStyleTag({
    content:
      "button:has(svg[data-testid='ScienceIcon']) { display: none !important; }",
  });
  for (const target of await page.getByText(/test data/i).all()) {
    await target.evaluate((node) => {
      (node.closest("button") ?? (node as HTMLElement)).style.display = "none";
    });
  }
}

async function login(browser: Browser, username: string, first?: string) {
  const context = await browser.newContext({
    baseURL: "http://127.0.0.1:4173",
    viewport: { width: 1440, height: 900 },
  });
  const page = await context.newPage();
  await page.goto("/accounts/login/");
  await page.locator("#id_username").fill(username);
  await page.locator("#id_password").fill(PASSWORD);
  if (first) await shot(page, first);
  await page.getByRole("button", { name: "Sign in" }).click();
  await page.waitForURL((url) => !url.pathname.includes("login"));
  await settle(page);
  return page;
}

async function openDeal(page: Page, title: string) {
  await page.goto("/");
  await settle(page);
  await page
    .getByRole("row")
    .filter({ hasText: title })
    .getByRole("link")
    .first()
    .click();
  await page.waitForURL(/registrations\/\d+/);
  await settle(page);
}

test("capture the guide screenshots", async ({ browser }) => {
  const partner = await login(browser, "demo-partner", "login");
  const dbgi = await login(browser, "demo-dbgi");

  // Part 1: getting started
  await partner.goto("/");
  await shot(partner, "list");
  await partner.goto("/help/");
  await shot(partner, "help");

  // Part 2: register a deal
  await partner.goto("/");
  await settle(partner);
  await partner.getByRole("button", { name: "New registration" }).click();
  await settle(partner);
  await partner.getByLabel("End-user").fill("Lucena");
  await partner.getByRole("option", { name: /Mayor/ }).first().click();
  await partner.getByLabel("Project opportunity title").fill(DEAL);
  await partner.getByLabel("Bid date").fill("2026-12-15");
  await partner.getByLabel("Delivery date").fill("2027-02-01");
  await partner.getByLabel("Contact person").fill("Demo Partner");
  await partner.getByLabel("Designation").fill("Account Manager");
  await partner
    .getByLabel("Contact email")
    .fill("demo-partner@example.invalid");
  await partner.getByLabel("Contact number").fill("(042) 788-2298");
  await shot(partner, "form-top");

  await partner.getByRole("button", { name: "Add competitor" }).click();
  const competitor = partner.getByRole("dialog");
  await competitor.getByLabel("Brand").fill("Canon");
  await partner.keyboard.press("Tab");
  await competitor.getByLabel("Item / model").fill("imageCLASS LBP246dw");
  await partner.keyboard.press("Tab");
  await competitor.getByLabel("Bid price").fill("9300");
  await dialog(partner, "competitor");
  await competitor.getByRole("button", { name: "Save item" }).click();

  await partner.getByRole("button", { name: "Add product" }).click();
  const product = partner.getByRole("dialog");
  await product.getByRole("combobox", { name: "Catalog product" }).click();
  await partner.getByRole("option", { name: /M1820W/ }).click();
  await product.getByLabel("Quantity").fill("20");
  await product.getByLabel("Requested unit price").fill("9000");
  await product
    .getByLabel("Justification")
    .fill("Canon offered 9,300 to the same office.");
  await dialog(partner, "product");
  await product.getByRole("button", { name: "Save item" }).click();

  await partner
    .getByLabel("Attachment description")
    .fill("Request for quotation from the Mayor's Office.");
  await partner.getByRole("checkbox", { name: /authorized/ }).check();
  await hideTestData(partner);
  await settle(partner);
  await partner.screenshot({ path: `${SHOTS}/form-full.png`, fullPage: true });
  await partner.getByRole("button", { name: "Create registration" }).click();
  await partner.waitForURL(/registrations\/\d+\/$/);
  const dealUrl = new URL(partner.url()).pathname;

  // Part 3: follow your deal
  await settle(partner);
  await partner.screenshot({
    path: `${SHOTS}/submitted-full.png`,
    fullPage: true,
  });
  await clip(partner, section(partner, "What happens next?"), "sub-next");
  await clip(partner, section(partner, "Requested products"), "sub-products");
  await clip(
    partner,
    section(partner, "Commercial approvals"),
    "sub-approvals",
  );
  await clip(partner, section(partner, "Activity"), "sub-activity");

  // Part 4: review a deal
  await dbgi.goto("/admin/");
  await shot(dbgi, "dashboard");
  await dbgi.goto("/");
  await shot(dbgi, "dbgi-list");
  await dbgi.goto(dealUrl);
  await settle(dbgi);
  await dbgi.screenshot({ path: `${SHOTS}/review-before.png` });
  await clip(dbgi, section(dbgi, "DBGI review"), "review-card");
  await dbgi
    .getByLabel("Review reason")
    .fill("Checking the request for quotation.");
  await dbgi.getByRole("button", { name: "Start review" }).click();
  await settle(dbgi);
  await dbgi.screenshot({
    path: `${SHOTS}/review-options-full.png`,
    fullPage: true,
  });
  await clip(dbgi, section(dbgi, "DBGI review"), "options-card");

  // Part 5: fix a returned deal
  await dbgi.getByRole("radio", { name: /Request changes/ }).check();
  await dbgi
    .getByLabel(/Instructions for company/)
    .fill(
      "Please add the name of the person who sent you the request for quotation.",
    );
  await clip(dbgi, section(dbgi, "DBGI review"), "changes-card");
  await dbgi.getByRole("button", { name: "Request changes" }).click();
  await settle(dbgi);
  await partner.goto(dealUrl);
  await settle(partner);
  await partner.screenshot({
    path: `${SHOTS}/returned-full.png`,
    fullPage: true,
  });
  await clip(partner, section(partner, "What happens next?"), "ret-next");
  await clip(partner, section(partner, "Activity"), "ret-activity");
  await partner.getByRole("button", { name: "Edit registration" }).click();
  await settle(partner);
  await partner
    .getByLabel("Attachment description")
    .fill(
      "Request for quotation from the Mayor's Office, sent by the Records Officer.",
    );
  await hideTestData(partner);
  await partner.screenshot({ path: `${SHOTS}/edit-full.png`, fullPage: true });
  await partner.getByRole("button", { name: "Save changes" }).click();
  await partner.waitForURL(/registrations\/\d+\/$/);
  await settle(partner);

  // Part 6: confirm the deal
  await dbgi.goto(dealUrl);
  await settle(dbgi);
  if (await dbgi.getByRole("button", { name: "Start review" }).isVisible()) {
    await dbgi
      .getByLabel("Review reason")
      .fill("Checking the corrected details.");
    await dbgi.getByRole("button", { name: "Start review" }).click();
    await settle(dbgi);
  }
  await dbgi
    .getByRole("radio", { name: /Create a new whole opportunity/ })
    .check();
  await settle(dbgi);
  await dbgi
    .getByLabel(/Decision reason/)
    .fill("First registration for this project.");
  await dbgi.screenshot({ path: `${SHOTS}/confirm-full.png`, fullPage: true });
  await clip(dbgi, section(dbgi, "DBGI review"), "confirm-card");
  await dbgi
    .getByRole("button", { name: "Create and link new opportunity" })
    .click();
  await settle(dbgi);
  await dbgi.screenshot({
    path: `${SHOTS}/confirmed-full.png`,
    fullPage: true,
  });

  // Part 7: approve the price
  await dbgi.goto(
    `/admin/registrations/registrationcategoryapproval/?q=${encodeURIComponent("Mayor's")}`,
  );
  await settle(dbgi);
  await shot(dbgi, "price-list");
  await dbgi
    .locator("#result_list tbody tr a, table tbody tr a")
    .first()
    .click();
  await settle(dbgi);
  await dbgi.setViewportSize({ width: 1440, height: 1500 });
  await dbgi.locator("[name=status]").selectOption("approved");
  await dbgi.locator("[name=rationale]").fill("Within the allowed discount.");
  await dbgi.getByText(/Add another Registration item approval/).click();
  await dbgi
    .locator('[name="item_approvals-0-registration_item"]')
    .selectOption({ index: 1 });
  await dbgi
    .locator('[name="item_approvals-0-approved_unit_price"]')
    .fill("9000");
  await shot(dbgi, "price-form");
  await dbgi.locator("[name=_save]").first().click();
  await settle(dbgi);
  await dbgi.setViewportSize({ width: 1440, height: 900 });

  // Part 8: see the result, renew, rank
  await partner.goto(dealUrl);
  await settle(partner);
  await partner.screenshot({
    path: `${SHOTS}/approved-full.png`,
    fullPage: true,
  });
  await clip(
    partner,
    section(partner, "Commercial approvals"),
    "app-approvals",
  );
  await clip(partner, section(partner, "Requested products"), "app-products");
  await partner.getByRole("button", { name: "Request renewal" }).click();
  await partner
    .getByRole("dialog")
    .getByLabel(/Reason/)
    .fill("The office moved the bid date to next month.");
  await dialog(partner, "renewal-request");
  await partner.getByRole("button", { name: "Send request" }).click();
  await expect(partner.getByText("Waiting for DBGI")).toBeVisible();
  await dbgi.goto(dealUrl);
  await settle(dbgi);
  await dbgi.screenshot({
    path: `${SHOTS}/renewal-dbgi-full.png`,
    fullPage: true,
  });
  await clip(dbgi, section(dbgi, "Commercial approvals"), "ren-approvals");
  await dbgi
    .getByRole("button", { name: "Approve", exact: true })
    .first()
    .click();
  await dbgi
    .getByRole("dialog")
    .getByLabel(/Reason/)
    .fill("The new bid date is confirmed.");
  await dialog(dbgi, "renewal-decide");
  await dbgi.getByRole("button", { name: "Approve renewal" }).click();
  await settle(dbgi);
  await partner.goto("/rankings/");
  await shot(partner, "rank-partner");

  // Part 9: change a deal
  await partner.goto(dealUrl);
  await settle(partner);
  await partner.screenshot({
    path: `${SHOTS}/after-renewal-full.png`,
    fullPage: true,
  });
  await clip(
    partner,
    section(partner, "Commercial approvals"),
    "after-approvals",
  );

  // Part 10: withdraw a deal
  await openDeal(partner, "Printers for the Lucena City Library");
  await partner.getByRole("button", { name: "Withdraw registration" }).click();
  await partner
    .getByRole("dialog")
    .getByLabel(/Reason for withdrawing/)
    .fill("The library cancelled its plan to buy printers.");
  await dialog(partner, "withdraw");
  await partner
    .getByRole("dialog")
    .getByRole("button", { name: "Withdraw registration" })
    .click();
  await settle(partner);
  await partner.screenshot({
    path: `${SHOTS}/withdrawn-full.png`,
    fullPage: true,
  });

  // Part 11: report the result
  await partner.goto(dealUrl);
  await settle(partner);
  await partner.getByRole("button", { name: "Report project outcome" }).click();
  await partner.getByRole("dialog").getByRole("radio", { name: "Won" }).check();
  await partner
    .getByRole("dialog")
    .getByLabel(/What happened/)
    .fill(
      "The office awarded the project to us. We got the award notice today.",
    );
  await dialog(partner, "outcome");
  await partner.getByRole("button", { name: "Send report" }).click();
  await settle(partner);
  await partner.screenshot({
    path: `${SHOTS}/outcome-sent-full.png`,
    fullPage: true,
  });
  await clip(
    partner,
    section(partner, "Project outcome reports"),
    "out-partner",
  );
  await dbgi.goto(dealUrl);
  await settle(dbgi);
  await dbgi.screenshot({
    path: `${SHOTS}/outcome-dbgi-full.png`,
    fullPage: true,
  });
  await clip(dbgi, section(dbgi, "Project outcome reports"), "out-dbgi");

  // Part 12: time limits
  await partner.goto("/notifications/");
  await shot(partner, "notifications");
  await dbgi.goto(
    `/admin/registrations/opportunity/?q=${encodeURIComponent("Mayor's")}`,
  );
  await settle(dbgi);
  await dbgi.locator("table tbody tr a").first().click();
  await settle(dbgi);
  await dbgi.setViewportSize({ width: 1440, height: 1100 });
  await shot(dbgi, "project-status");

  // Part 13: DBGI tasks
  await dbgi.goto("/admin/registrations/product/?q=M1820W");
  await settle(dbgi);
  await dbgi.locator("table tbody tr a").first().click();
  await settle(dbgi);
  await dbgi.setViewportSize({ width: 1440, height: 1300 });
  await shot(dbgi, "price-add");
  await dbgi.setViewportSize({ width: 1440, height: 900 });
  await openDeal(dbgi, "Scanners for the City Treasurer's Office");
  await dbgi.getByRole("button", { name: "Add to catalog" }).click();
  const catalog = dbgi.getByRole("dialog");
  await catalog.getByLabel(/Product code/).fill("HDS-100");
  await catalog.getByLabel(/Category/).fill("Scanners");
  await catalog.getByLabel(/List price/).fill("12000");
  await catalog
    .getByLabel(/^Reason/)
    .fill("This scanner is now part of our product line.");
  await dialog(dbgi, "catalog");
  await dbgi
    .getByRole("dialog")
    .getByRole("button", { name: "Cancel" })
    .click();
  await openDeal(dbgi, "Printers for the City Engineer's Office");
  const reprice = dbgi.getByRole("button", {
    name: "Apply current list prices",
  });
  await reprice.click();
  await dbgi
    .getByRole("dialog")
    .getByLabel(/Reason for repricing/)
    .fill("The list price changed before review started.");
  await dialog(dbgi, "reprice");
  await dbgi
    .getByRole("dialog")
    .getByRole("button", { name: "Cancel" })
    .click();
  await dbgi.goto("/rankings/");
  await shot(dbgi, "rank-dbgi");
  await dbgi.getByRole("button", { name: "Decide tie" }).first().click();
  await dbgi
    .getByRole("dialog")
    .getByLabel(/Reason for this order/)
    .fill("Sample Partner showed the earlier signed quotation.");
  await dialog(dbgi, "tie");
});
