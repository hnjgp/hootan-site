import { expect, test, type Page } from "@playwright/test";
import en from "../src/i18n/en.json";
import fa from "../src/i18n/fa.json";

/** Console errors and failed requests seen while the test runs. */
function watchErrors(page: Page) {
  const errors: string[] = [];
  page.on("console", (m) => m.type() === "error" && errors.push(m.text()));
  page.on("pageerror", (e) => errors.push(e.message));
  return errors;
}

for (const [lang, dir] of [
  ["fa", "rtl"],
  ["en", "ltr"],
] as const) {
  test(`${lang} home page loads with ${dir} and no console errors`, async ({ page }) => {
    const errors = watchErrors(page);
    await page.goto(`/${lang}`);
    await page.waitForLoadState("networkidle");

    await expect(page.locator("html")).toHaveAttribute("lang", lang);
    await expect(page.locator("html")).toHaveAttribute("dir", dir);
    for (const id of ["twin", "job-fit", "trading", "play", "projects"]) await expect(page.locator(`#${id}`)).toBeAttached();
    expect(errors, errors.join("\n")).toEqual([]);
  });
}

test("the language switch opens the other language and remembers it", async ({ page }) => {
  await page.goto("/fa");
  await page.waitForLoadState("networkidle");
  await page.getByRole("group", { name: fa.header.langLabel }).getByRole("link", { name: "EN" }).click();

  await expect(page).toHaveURL(/\/en$/);
  await expect(page.locator("html")).toHaveAttribute("dir", "ltr");
  expect((await page.context().cookies()).find((c) => c.name === "lang")?.value).toBe("en");
});

test("the theme button switches to dark and the choice survives a reload", async ({ page }) => {
  await page.emulateMedia({ colorScheme: "light" });
  await page.goto("/en");
  await page.waitForLoadState("networkidle");
  await page.getByRole("button", { name: en.header.themeLabel }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");

  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
});

test("a project opens in a panel, Escape closes it and focus returns to its card", async ({ page }) => {
  await page.goto("/en#projects");
  await page.waitForLoadState("networkidle");
  const card = page.locator("#projects").getByRole("button", { name: new RegExp(en.projects.items.astra.title) });
  await card.click();

  await expect(page.getByText(en.projects.items.astra.lead)).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.getByText(en.projects.items.astra.lead)).toHaveCount(0);
  await expect(card).toBeFocused();
});

test("a logged-out visitor who uses the order form is asked to log in", async ({ page }) => {
  await page.goto("/fa#play");
  await page.waitForLoadState("networkidle");
  await page.locator("#play form").getByRole("button").first().click();

  await expect(page.locator("#play").getByRole("alert")).toHaveText(fa.play.needLogin);
  await expect(page.locator("#play").getByLabel(fa.auth.password)).toBeVisible();
});

for (const [name, viewport] of [
  ["desktop", { width: 1440, height: 900 }],
  ["mobile", { width: 390, height: 844 }],
] as const) {
  test(`full-page screenshot on ${name} has no sideways scroll`, async ({ page }, info) => {
    await page.setViewportSize(viewport);
    await page.goto("/fa");
    await page.waitForLoadState("networkidle");

    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: info.outputPath(`${name}.png`), fullPage: true });
  });
}

test("a project deep link opens its panel and scrolls to the projects", async ({ page }) => {
  await page.goto("/en#project-price");

  await expect(page.getByText(en.projects.items.price.lead)).toBeInViewport();
});
