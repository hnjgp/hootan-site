import { expect, test } from "vitest";
import { latinDigits } from "@/lib/digits";

test("Persian and Arabic digits and number signs become Latin", () => {
  expect(latinDigits("قیمت ۸۰٬۲۰۰٫۵ و ۲۰٪، سال ١٣٧١")).toBe(
    "قیمت 80,200.5 و 20%، سال 1371",
  );
});
