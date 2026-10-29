const PERSIAN = "۰۱۲۳۴۵۶۷۸۹";
const ARABIC = "٠١٢٣٤٥٦٧٨٩";
const SIGNS: Record<string, string> = { "٬": ",", "٫": ".", "٪": "%" };

/** The site writes every number with Latin digits, also in Persian; model text may not. */
export const latinDigits = (text: string) =>
  text.replace(
    /[۰-۹٠-٩٬٫٪]/g,
    (c) => SIGNS[c] ?? String(Math.max(PERSIAN.indexOf(c), ARABIC.indexOf(c))),
  );

/** Dollars with an explicit sign and no space, the same in both languages: "+$1,250.5", "-$4". */
export const signedUsd = (value: number, loc: string, digits = 2) =>
  (value < 0 ? "-" : "+") + "$" + Math.abs(value).toLocaleString(loc, { maximumFractionDigits: digits });
