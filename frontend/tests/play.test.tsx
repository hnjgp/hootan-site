import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";
import { AuthProvider } from "@/components/auth/AuthProvider";
import { Account } from "@/components/header/Account";
import { Play } from "@/components/home/play/Play";
import { getDictionary } from "@/i18n";

const t = getDictionary("en").play;
const a = getDictionary("en").auth;

const renderPlay = () =>
  render(
    <AuthProvider>
      <Account t={a} />
      <Play t={t} auth={a} lang="en" />
    </AuthProvider>,
  );

const ME = {
  nickname: "satoshi",
  avatar: false,
  balance_usd: "100000",
  streak: 0,
  today: null,
  predictions: [],
};
const SUMMARY = {
  today_status: "done",
  today_started_at: null,
  start_usd: "100000",
  value_usd: "101000",
  hold_usd: "99000",
  last: { session_date: "2026-10-29", decision: "BUY", events: [] },
};
const ROWS = [
  { rank: 1, nickname: "dana", return_pct: 4.5, is_ai: false },
  { rank: 2, nickname: "AI Trading Team", return_pct: 1, is_ai: true },
];

/** A fake backend: `routes` maps a path start to [status, body]; posts are recorded. */
function backend(routes: Record<string, [number, unknown]>) {
  const all: Record<string, [number, unknown]> = {
    "/api/trading/summary": [200, SUMMARY],
    "/api/game/stats": [200, { accuracy_pct: 60, ahead_pct: null, trades: [] }],
    "/api/game/price": [200, { price: "80000" }],
    "/api/game/leaderboard": [200, { rows: ROWS }],
    "/api/market/btc": [200, { points: [] }],
    ...routes,
  };
  const fetch = vi.fn<(url: string, init?: RequestInit) => Promise<Response>>(async (url) => {
    const [status, body] = all[Object.keys(all).find((k) => url.startsWith(k))!];
    return new Response(JSON.stringify(body), { status });
  });
  vi.stubGlobal("fetch", fetch);
  return fetch;
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

test("the rules sit in one card and the table marks the AI team", async () => {
  backend({ "/api/game/me": [401, { detail: "No player" }] });
  renderPlay();

  const rules = screen.getByRole("region", { name: t.rulesTitle });
  expect(within(rules).getAllByRole("listitem")).toHaveLength(4);
  expect(await screen.findByText(t.ai)).toBeTruthy();
  expect(screen.getByText("+4.5%")).toBeTruthy();
  expect(screen.getByText("60%")).toBeTruthy();
  expect(screen.getByText(t.stats.none)).toBeTruthy();
});

test("logged out, the box asks to log in and offers sign-up with optional email and phone", async () => {
  backend({ "/api/game/me": [401, null], "/api/game/players": [409, { detail: "Nickname taken" }] });
  renderPlay();

  expect(await screen.findByText(a.loginTitle)).toBeTruthy();
  expect(screen.queryByLabelText(a.email)).toBeNull();
  fireEvent.click(within(screen.getByText(a.loginTitle).closest("form")!).getByRole("button", { name: a.signup }));
  fireEvent.change(screen.getByLabelText(a.nickname), { target: { value: "satoshi" } });
  fireEvent.change(screen.getByLabelText(a.password), { target: { value: "pw" } });
  expect(screen.getByLabelText(a.email)).toBeTruthy();
  fireEvent.submit(screen.getByLabelText(a.password).closest("form")!);

  expect(await screen.findByText(a.errTaken)).toBeTruthy();
});

test("a wrong password says so, the right one shows the wallet and the header account", async () => {
  const fetch = backend({ "/api/game/me": [401, null], "/api/game/login": [401, null] });
  renderPlay();
  fireEvent.change(await screen.findByLabelText(a.nickname), { target: { value: "satoshi" } });
  fireEvent.change(screen.getByLabelText(a.password), { target: { value: "nope" } });
  fireEvent.submit(screen.getByLabelText(a.password).closest("form")!);
  expect(await screen.findByText(a.errLogin)).toBeTruthy();

  fetch.mockImplementation(async (url) =>
    new Response(JSON.stringify(url === "/api/game/login" ? ME : { rows: [], points: [] }), { status: 200 }),
  );
  fireEvent.submit(screen.getByLabelText(a.password).closest("form")!);

  expect(await screen.findByText(t.wallet)).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: a.account }));
  expect(screen.getByText(a.logout)).toBeTruthy();
});

test("a prediction is sent with direction and stake, then shown as today's", async () => {
  const fetch = backend({
    "/api/game/me": [200, ME],
    "/api/game/predictions": [
      201,
      { game_date: "2026-10-29", direction: "down", stake_pct: 50, stake_usd: "50000", ref_price: "80000", result: null, pnl_usd: null },
    ],
  });
  renderPlay();

  // The team bought today, so "lower" earns the double bonus.
  expect(await screen.findByText(t.bonus.replace("{dir}", t.down))).toBeTruthy();
  const submit = screen.getByText(t.submit).closest("button")!;
  expect(submit.disabled).toBe(true);
  fireEvent.click(screen.getByRole("button", { name: `▼ ${t.down}` }));
  fireEvent.click(submit);

  expect(await screen.findByText(t.today)).toBeTruthy();
  const sent = fetch.mock.calls.find(([url]) => url === "/api/game/predictions")!;
  expect(JSON.parse(sent[1]!.body as string)).toEqual({ direction: "down", stake_pct: 50 });
});
