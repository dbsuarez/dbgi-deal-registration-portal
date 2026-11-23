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
  const owner = await login(browser, "demo-owner");

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

  // Part 7: approve the price on the deal page
  await dbgi.goto(dealUrl);
  await settle(dbgi);
  await clip(dbgi, section(dbgi, "Commercial approvals"), "price-open");
  await dbgi.getByRole("button", { name: "Decide price" }).first().click();
  const decide = dbgi.getByRole("dialog");
  for (const input of await decide.getByLabel(/Approved price for/).all())
    await input.fill("9000");
  await decide.getByLabel(/Reason/).fill("Within the allowed discount.");
  await dialog(dbgi, "price-decide");
  await decide.getByRole("button", { name: "Save decision" }).click();
  // Above the admin limit, the box says it went to the owner; close it.
  const close = decide.getByRole("button", { name: "Close" });
  await close
    .waitFor({ timeout: 10_000 })
    .then(() => close.click())
    .catch(() => undefined);
  await expect(decide).toBeHidden();
  await settle(dbgi);

  // Part 16: a 10% discount is above the admin limit, so the owner approves it
  await owner.goto("/owner-approvals/");
  await shot(owner, "owner-approvals");
  await owner.getByLabel(/Your note/).fill("Approved for this bid.");
  await owner.getByRole("button", { name: "Approve" }).click();
  await expect(
    owner.getByText(/approved\. The company is told\./),
  ).toBeVisible();

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

  // Part 10: close a deal
  await openDeal(partner, "Printers for the Lucena City Library");
  await partner.getByRole("button", { name: "Cancel deal" }).click();
  await partner
    .getByRole("dialog")
    .getByLabel(/Reason/)
    .fill("The library cancelled its plan to buy printers.");
  await dialog(partner, "withdraw");
  await partner
    .getByRole("dialog")
    .getByRole("button", { name: "Cancel deal" })
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
  await partner
    .getByRole("dialog")
    .getByLabel("Notice of Award file")
    .setInputFiles({
      name: "notice-of-award.pdf",
      mimeType: "application/pdf",
      buffer: Buffer.from("%PDF-1.4 sample notice of award"),
    });
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
  await dbgi.goto(dealUrl);
  await settle(dbgi);
  await dbgi.getByRole("button", { name: "Change project status" }).click();
  const statusBox = dbgi.getByRole("dialog");
  await statusBox.getByRole("combobox", { name: /Project status/ }).click();
  await dbgi.getByRole("option", { name: "On hold" }).click();
  await statusBox.getByLabel(/Reason/).fill("The bidding was postponed.");
  await dialog(dbgi, "project-status");
  await statusBox.getByRole("button", { name: "Cancel" }).click();

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

  // Portal settings: the rules DBGI can change
  await dbgi.goto("/admin/registrations/portalsetting/");
  await settle(dbgi);
  const existing = dbgi.locator("table tbody tr a").first();
  if (await existing.count()) await existing.click();
  else await dbgi.goto("/admin/registrations/portalsetting/add/");
  await dbgi.setViewportSize({ width: 1440, height: 1400 });
  await shot(dbgi, "portal-settings");
  await dbgi.setViewportSize({ width: 1440, height: 900 });

  // Part 16: the owner's home page
  await owner.goto("/");
  await owner.setViewportSize({ width: 1440, height: 1100 });
  await shot(owner, "owner-overview");
});
