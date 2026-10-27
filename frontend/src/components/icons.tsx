const stroke = {
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 2,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
};

const SECTION_PATHS = [
  "M4 5h16v10H10l-5 4v-4H4z",
  "M16 10a6 6 0 1 1-12 0a6 6 0 1 1 12 0 M14.5 14.5L20 20 M7.5 10l1.8 1.8L12.8 8",
  "M3 20h18 M5 16l4-5 4 3 6-8 M15 6h4v4",
  "M3 7h6l2 2h10v10H3z",
  "M8 7l-5 5 5 5 M16 7l5 5-5 5 M13.5 5l-3 14",
];

/** Line icon for one of the five home sections: twin, job fit, trading, projects, how it's built. */
export function SectionIcon({ i, size = 24 }: { i: number; size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true">
      <path {...stroke} d={SECTION_PATHS[i]} />
    </svg>
  );
}

export function WhatsAppIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true" {...stroke}>
      <path d="M4 20l1.3-4A8 8 0 1 1 8 18.7z" />
      <path d="M9 9.5c0 3 2.5 5.5 5.5 5.5l1-1.5-2-1-1 .8a4 4 0 0 1-1.8-1.8l.8-1-1-2z" />
    </svg>
  );
}

export function TelegramIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true" {...stroke}>
      <path d="M21 4L3 11l6 2 2 6 3-4 5 4z M9 13l12-9" />
    </svg>
  );
}
