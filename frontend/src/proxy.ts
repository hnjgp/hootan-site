import { NextResponse, type NextRequest } from "next/server";
import { hasLocale } from "./i18n";

/** Pick the visitor's language: saved cookie first, then the browser's Accept-Language. */
function pickLocale(request: NextRequest) {
  const saved = request.cookies.get("lang")?.value;
  if (saved && hasLocale(saved)) return saved;
  const first = request.headers.get("accept-language")?.split(",")[0] ?? "";
  return first.toLowerCase().startsWith("fa") ? "fa" : "en";
}

/** Send any path without /fa or /en in front to the visitor's language. */
export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const first = pathname.split("/")[1];
  if (hasLocale(first)) return;
  request.nextUrl.pathname = `/${pickLocale(request)}${pathname === "/" ? "" : pathname}`;
  return NextResponse.redirect(request.nextUrl);
}

export const config = {
  matcher: ["/((?!api|_next|assets|favicon.ico|.*\\.).*)"],
};
