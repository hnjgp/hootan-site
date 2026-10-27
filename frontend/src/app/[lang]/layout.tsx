import type { Metadata } from "next";
import { notFound } from "next/navigation";
import "@fontsource-variable/dm-sans";
import "@fontsource-variable/caveat";
import "@fontsource/ibm-plex-mono/400.css";
import "@fontsource/ibm-plex-mono/500.css";
import "@fontsource-variable/vazirmatn";
import "../globals.css";
import { dirOf, hasLocale, locales } from "@/i18n";

export const metadata: Metadata = {
  title: "Hootan Seifi",
  description: "AI Engineer portfolio and AI Trading Floor",
};

const themeScript = `(function(){try{var t=localStorage.getItem("theme");if(t)document.documentElement.setAttribute("data-theme",t)}catch(e){}})()`;

export function generateStaticParams() {
  return locales.map((lang) => ({ lang }));
}

export default async function RootLayout({ children, params }: LayoutProps<"/[lang]">) {
  const { lang } = await params;
  if (!hasLocale(lang)) notFound();
  return (
    <html lang={lang} dir={dirOf(lang)} suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body className="min-h-screen overflow-x-hidden antialiased">{children}</body>
    </html>
  );
}
