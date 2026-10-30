/** jsdom has no matchMedia; tests run as a visitor with no media preferences unless a test sets `reduceMotion`. */
export const media = { reduceMotion: false };

window.matchMedia = (query: string) =>
  ({
    matches: query.includes("prefers-reduced-motion") && media.reduceMotion,
    media: query,
    addEventListener: () => {},
    removeEventListener: () => {},
  }) as unknown as MediaQueryList;
