import en from "./en.json";
import fa from "./fa.json";

const dictionaries = { en, fa };

export type Locale = keyof typeof dictionaries;
export type Dictionary = typeof en;

export const locales: Locale[] = ["en", "fa"];

export const hasLocale = (value: string): value is Locale => value in dictionaries;

export const getDictionary = (locale: Locale): Dictionary => dictionaries[locale];

export const dirOf = (locale: Locale) => (locale === "fa" ? "rtl" : "ltr");
