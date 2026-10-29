import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";
import { AuthProvider } from "@/components/auth/AuthProvider";
import { Account } from "@/components/header/Account";
import { summary } from "@/components/home/play/Leaderboard";
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
  return_pct: 0,
  hold_usd: "110000",
  ai_return_pct: 1,
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
    "/api/trading/trades": [200, []],
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

test("the rules sit in one card, the table marks the AI team, and logged out the tiles are dashes", async () => {
  backend({ "/api/game/me": [401, { detail: "No player" }] });
  renderPlay();

  const rules = screen.getByRole("region", { name: t.rulesTitle });
  expect(within(rules).getAllByRole("listitem")).toHaveLength(4);
  expect(await screen.findByText(t.ai)).toBeTruthy();
  expect(screen.getByText("+4.5%")).toBeTruthy();
  expect(screen.getAllByText("—")).toHaveLength(4);
});

test("logged out, the form shows but using it asks to log in", async () => {
  backend({ "/api/game/me": [401, null] });
  renderPlay();

  fireEvent.click(await screen.findByRole("button", { name: `▲ ${t.up}` }));

  expect(await screen.findByText(t.needLogin)).toBeTruthy();
  expect(screen.getAllByLabelText(a.password).length).toBeGreaterThan(0);
});

test("logged in, the tiles show the player's own numbers", async () => {
  backend({ "/api/game/me": [200, ME] });
  renderPlay();

  expect(await screen.findByText("$110,000")).toBeTruthy();
  // Return 0% against the team's +1%: not ahead.
  expect(screen.getByText(t.mine.no)).toBeTruthy();
});

test("the summary shows the top five, the AI team and the player, with gaps", () => {
  const rows = Array.from({ length: 70 }, (_, k) => ({
    rank: k + 1,
    nickname: k === 29 ? "AI Trading Team" : `p${k + 1}`,
    return_pct: 70 - k,
    is_ai: k === 29,
  }));

  const ranks = summary(rows, "p70").map((r) => r?.rank ?? null);

  expect(ranks).toEqual([1, 2, 3, 4, 5, null, 30, null, 70]);
});

test("sign-up asks for an email and an optional phone, and a taken name says so", async () => {
  backend({ "/api/game/me": [401, null], "/api/game/players": [409, { detail: "Nickname taken" }] });
  renderPlay();

  fireEvent.click(await screen.findByRole("button", { name: `▲ ${t.up}` }));
  expect(screen.queryByLabelText(a.email)).toBeNull();
  fireEvent.click(within(screen.getByText(t.needLogin).closest("form")!).getByRole("button", { name: a.signup }));
  fireEvent.change(screen.getByLabelText(a.nickname), { target: { value: "satoshi" } });
  fireEvent.change(screen.getByLabelText(a.password), { target: { value: "pw" } });
  expect((screen.getByLabelText(a.email) as HTMLInputElement).required).toBe(true);
  expect((screen.getByLabelText(a.phone) as HTMLInputElement).required).toBe(false);
  fireEvent.submit(screen.getByLabelText(a.password).closest("form")!);

  expect(await screen.findByText(a.errTaken)).toBeTruthy();
});

test("a wrong password says so, the right one shows the wallet and the header account", async () => {
  const fetch = backend({ "/api/game/me": [401, null], "/api/game/login": [401, null] });
  renderPlay();
  fireEvent.click(await screen.findByRole("button", { name: `▲ ${t.up}` }));
  fireEvent.change(screen.getByLabelText(a.nickname), { target: { value: "satoshi" } });
  fireEvent.change(screen.getByLabelText(a.password), { target: { value: "nope" } });
  fireEvent.submit(screen.getByLabelText(a.password).closest("form")!);
  expect(await screen.findByText(a.errLogin)).toBeTruthy();

  fetch.mockImplementation(async (url) =>
    new Response(JSON.stringify(url === "/api/game/login" ? ME : { rows: [], points: [] }), { status: 200 }),
  );
  fireEvent.submit(screen.getByLabelText(a.password).closest("form")!);

  expect(await screen.findByText(t.mine.balance)).toBeTruthy();
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
