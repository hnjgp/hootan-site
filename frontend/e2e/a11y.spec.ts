import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

for (const lang of ["fa", "en"]) {
  for (const colorScheme of ["light", "dark"] as const) {
    test(`home page has no WCAG A or AA violations (${lang}, ${colorScheme})`, async ({ page }) => {
      await page.emulateMedia({ colorScheme });
      await page.goto(`/${lang}`);
      await page.waitForLoadState("networkidle");

      const { violations } = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa"]).exclude('[aria-hidden="true"]').analyze();
      const found = violations.flatMap((v) => v.nodes.map((n) => `${v.id} ${n.target.join(" ")}: ${n.any[0]?.message ?? v.help}`));

      expect(found, found.join("\n")).toEqual([]);
    });
  }
}
