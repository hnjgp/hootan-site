import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";
import { JobFit } from "@/components/home/jobfit/JobFit";
import { getDictionary } from "@/i18n";

const t = getDictionary("en").jobfit;

const RESULT = {
  strengths: [{ point: "Python and FastAPI", evidence: "Used in Astra" }],
  gaps: ["No Kubernetes in shipped work"],
  summary: "Strong technical match.",
  questions: ["How do the agents stay inside risk limits?"],
  score: 78,
};

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

function submitSample() {
  render(<JobFit t={t} lang="en" />);
  fireEvent.click(screen.getByText(t.sample));
  fireEvent.click(screen.getByText(t.check));
}

test("the check button stays off until the ad is long enough", () => {
  render(<JobFit t={t} lang="en" />);

  expect(screen.getByText(t.check).closest("button")!.disabled).toBe(true);
  fireEvent.click(screen.getByText(t.sample));
  expect(screen.getByText(t.check).closest("button")!.disabled).toBe(false);
});

test("while waiting an old word shows, then the result appears", async () => {
  let reply!: (r: Response) => void;
  vi.stubGlobal("fetch", vi.fn(() => new Promise<Response>((r) => (reply = r))));
  submitSample();

  expect(t.words.some(([w]) => screen.queryByText(w))).toBe(true);
  reply(new Response(JSON.stringify(RESULT)));

  expect(await screen.findByText(RESULT.summary)).toBeTruthy();
  expect(screen.getByText(RESULT.gaps[0])).toBeTruthy();
  expect(screen.getByText(RESULT.questions[0])).toBeTruthy();
});

test("the daily limit shows the friendly budget note", async () => {
  vi.stubGlobal("fetch", vi.fn(async () => new Response("{}", { status: 429 })));
  submitSample();

  expect(await screen.findByText(t.limit)).toBeTruthy();
});
