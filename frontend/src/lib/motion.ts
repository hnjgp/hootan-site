/** True when the visitor asked the system for less motion; scripted motion then jumps straight to its end. */
export const still = () => matchMedia("(prefers-reduced-motion: reduce)").matches;

/** Scroll behaviour that respects the reduced-motion setting. */
export const glide = (): ScrollBehavior => (still() ? "auto" : "smooth");
