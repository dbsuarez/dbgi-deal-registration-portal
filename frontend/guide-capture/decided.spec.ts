import { expect, test, type Browser, type Page } from "@playwright/test";

// Runs repeat orders, merges, and splits on the real server and demo database.
// Reseed first with guide_seed.py and guide_seed_decided.py.
const SHOTS = "../docs/guides/_source/shots2";
const PASSWORD = "demo-guide-password-1";
const PDF = (name: string) => ({
  name,
  mimeType: "application/pdf",
  buffer: Buffer.from(`%PDF-1.4 ${name}`),
});

async function settle(page: Page) {
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout(300);
}

async function login(browser: Browser, username: string) {
  const context = await browser.newContext({
    baseURL: "http://127.0.0.1:4173",
    viewport: { width: 1440, height: 900 },
  });
  const page = await context.newPage();
  await page.goto("/accounts/login/");
  await page.locator("#id_username").fill(username);
  await page.locator("#id_password").fill(PASSWORD);
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

test("repeat order, merge, and split on the real server", async ({
  browser,
}) => {
  const partner = await login(browser, "demo-partner");
  const dbgi = await login(browser, "demo-dbgi");

  // Repeat order: the partner asks with both letters, and DBGI accepts
  await openDeal(partner, "Repeat order example");
  const dealUrl = new URL(partner.url()).pathname;
  await partner.getByRole("button", { name: "Request repeat order" }).click();
  const request = partner.getByRole("dialog");
  await request.getByLabel(/Quantity of/).fill("5");
  await request
    .getByLabel("Notice of Award file")
    .setInputFiles(PDF("noa.pdf"));
  await request
    .getByLabel("Notice to Proceed file")
    .setInputFiles(PDF("ntp.pdf"));
  await request.getByRole("checkbox").check();
  await request
    .getByLabel(/Note/)
    .fill("Five more printers for the same office.");
  await settle(partner);
  await request.screenshot({ path: `${SHOTS}/repeat-request.png` });
  await request.getByRole("button", { name: "Send request" }).click();
  await expect(partner.getByText("Waiting for DBGI")).toBeVisible();
  await expect(partner.getByRole("cell", { name: "40,000.00" })).toBeVisible();

  await dbgi.goto(dealUrl);
  await settle(dbgi);
  const letter = await dbgi.request.get(
    await dbgi
      .getByRole("link", { name: "NOA" })
      .getAttribute("href")
      .then(String),
  );
  expect(letter.status()).toBe(200);
  await dbgi.getByRole("button", { name: "Accept", exact: true }).click();
  await dbgi
    .getByRole("dialog")
    .getByLabel(/Reason/)
    .fill("Both letters say it is a repeat order.");
  await settle(dbgi);
  await dbgi
    .getByRole("dialog")
    .screenshot({ path: `${SHOTS}/repeat-decide.png` });
  await dbgi.getByRole("button", { name: "Accept repeat order" }).click();
  await settle(dbgi);
  await partner.reload();
  await settle(partner);
  await expect(partner.getByRole("cell", { name: "Accepted" })).toBeVisible();
  await partner
    .getByRole("heading", { name: "Repeat orders" })
    .locator("xpath=ancestor::*[contains(@class,'MuiPaper-root')][1]")
    .screenshot({ path: `${SHOTS}/repeat-section.png` });

  // Merge: DBGI combines two projects from Rankings
  await dbgi.goto("/rankings/");
  await settle(dbgi);
  await dbgi
    .getByRole("row")
    .filter({ hasText: "Merge example: same tender" })
    .getByRole("button", { name: "Merge" })
    .click();
  const merge = dbgi.getByRole("dialog");
  await merge.getByRole("combobox", { name: /Merge into/ }).click();
  await dbgi
    .getByRole("option", { name: /Merge example: main project/ })
    .click();
  await expect(merge.getByText(/1\. DEMO ONLY - Sample Partner/)).toBeVisible();
  await expect(merge.getByText(/2\. DEMO ONLY - Second Partner/)).toBeVisible();
  await merge
    .getByLabel(/Reason/)
    .fill("DBGI learned these are the same tender.");
  await settle(dbgi);
  await merge.screenshot({ path: `${SHOTS}/merge-dialog.png` });
  await merge.getByRole("button", { name: "Merge projects" }).click();
  await expect(merge).toBeHidden();
  await settle(dbgi);
  await expect(
    dbgi.getByRole("row").filter({ hasText: "Merge example: same tender" }),
  ).toHaveCount(0);
  const merged = dbgi
    .getByRole("row")
    .filter({ hasText: "DEMO ONLY - Second Partner" })
    .filter({ hasText: "Merge example: main project" });
  await expect(merged).toHaveCount(1);

  // Split: DBGI moves one product to a new deal on a new lot
  await openDeal(dbgi, "Split example");
  await dbgi.getByRole("button", { name: "Split deal" }).click();
  const split = dbgi.getByRole("dialog");
  await split.getByRole("checkbox").nth(1).check();
  await split.getByLabel("New lot name").fill("Lot 2");
  await split.getByLabel(/Reason/).fill("The tender has two separate lots.");
  await settle(dbgi);
  await split.screenshot({ path: `${SHOTS}/split-dialog.png` });
  await split.getByRole("button", { name: "Split deal" }).click();
  await expect(split).toBeHidden();
  await settle(dbgi);
  const newDeal = new URL(dbgi.url()).pathname;
  await expect(dbgi.getByText("Registered").first()).toBeVisible();
  await expect(dbgi.getByText(/Lot: .*Lot 2/)).toBeVisible();

  // The partner sees the split without DBGI's reason
  await partner.goto(newDeal);
  await settle(partner);
  await expect(partner.getByText(/DBGI split this deal from/)).toBeVisible();
  await expect(partner.getByText(/two separate lots/)).toHaveCount(0);
});
