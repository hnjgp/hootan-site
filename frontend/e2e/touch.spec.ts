import { expect, test } from "@playwright/test";

test.use({ viewport: { width: 390, height: 844 }, hasTouch: true, isMobile: true });

test("on a phone every visible control is at least 44px tall", async ({ page }) => {
  await page.goto("/fa");
  await page.waitForLoadState("networkidle");

  const small = await page.evaluate(() =>
    [...document.querySelectorAll<HTMLElement>("a[href], button, input, select, textarea")]
      .filter((el) => el.getClientRects().length && getComputedStyle(el).visibility !== "hidden")
      .map((el) => ({ el, r: el.getBoundingClientRect() }))
      .filter(({ r }) => r.height < 44)
      .map(({ el, r }) => `${el.tagName} ${Math.round(r.width)}x${Math.round(r.height)} ${(el.getAttribute("aria-label") || el.textContent || el.getAttribute("type") || "").trim().slice(0, 30)}`),
  );

  expect(small, small.join("\n")).toEqual([]);
});
