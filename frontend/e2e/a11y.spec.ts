import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

for (const lang of ["fa", "en"]) {
  for (const theme of ["light", "dark"]) {
    test(`home page has no WCAG A or AA violations (${lang}, ${theme})`, async ({ page }) => {
      await page.addInitScript((t) => localStorage.setItem("theme", t), theme);
      await page.goto(`/${lang}`);
      await page.waitForLoadState("networkidle");

      const { violations } = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa"]).exclude('[aria-hidden="true"]').analyze();
      const found = violations.flatMap((v) => v.nodes.map((n) => `${v.id} ${n.target.join(" ")}: ${n.any[0]?.message ?? v.help}`));

      expect(found, found.join("\n")).toEqual([]);
    });
  }
}
