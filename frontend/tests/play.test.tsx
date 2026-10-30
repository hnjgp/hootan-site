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

const POSITION = {
  id: 7,
  side: "long",
  entry_price: "80000",
  margin_usd: "1000",
  leverage: 10,
  qty: "0.125",
  tp_price: null,
  sl_price: null,
  liq_price: "72000",
  fee_usd: "5",
  opened_at: "2026-10-30T08:00:00Z",
  closed_at: null,
  close_price: null,
  close_reason: null,
  pnl_usd: "250",
};
const ME = {
  nickname: "satoshi",
  avatar: false,
  price: "82000",
  cash_usd: "8995",
  equity_usd: "10245",
  return_pct: 2.45,
  hold_usd: "10250",
  ai_return_pct: 0,
  open: [POSITION],
  closed: [],
};
const ROWS = [
  { rank: 1, nickname: "dana", return_pct: 4.5, is_ai: false },
  { rank: 2, nickname: "AI Trading Team", return_pct: 1, is_ai: true },
];

/** A fake backend: `routes` maps a path start to [status, body]; posts are recorded. */
function backend(routes: Record<string, [number, unknown]>) {
  const all: Record<string, [number, unknown]> = {
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

const longButton = () => screen.findByRole("button", { name: new RegExp(`^▲ ${t.long}`) });

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

test("the rules sit in one card, the table marks the AI team, and logged out the strip is dashes", async () => {
  backend({ "/api/game/me": [401, { detail: "No player" }] });
  renderPlay();

  const rules = screen.getByRole("region", { name: t.rulesTitle });
  expect(within(rules).getAllByRole("listitem")).toHaveLength(4);
  expect(await screen.findByText(t.ai)).toBeTruthy();
  expect(screen.getByText("+4.5%")).toBeTruthy();
  expect(screen.getAllByText("—")).toHaveLength(3);
});

test("logged out, the form shows but using it asks to log in", async () => {
  backend({ "/api/game/me": [401, null] });
  renderPlay();

  fireEvent.click(await longButton());

  expect(await screen.findByText(t.needLogin)).toBeTruthy();
  expect(screen.getAllByLabelText(a.password).length).toBeGreaterThan(0);
});

test("logged in, the strip and the open positions show live numbers, and close sends the id", async () => {
  const fetch = backend({
    "/api/game/me": [200, ME],
    "/api/game/positions/7/close": [200, { ...ME, open: [], closed: [{ ...POSITION, closed_at: "x", close_price: "82000", close_reason: "manual", pnl_usd: "240" }] }],
  });
  renderPlay();

  expect(await screen.findByText("$10,245")).toBeTruthy();
  expect(screen.getByText("+$245")).toBeTruthy();
  expect(screen.getByText("+$250")).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: t.close }));

  expect(await screen.findByText(t.noPositions)).toBeTruthy();
  expect(fetch.mock.calls.some(([url]) => url === "/api/game/positions/7/close")).toBe(true);
});

test("an order sends side, the dollar amount, leverage and levels", async () => {
  const fetch = backend({ "/api/game/me": [200, { ...ME, open: [] }], "/api/game/positions": [201, ME] });
  renderPlay();

  fireEvent.click(await screen.findByRole("button", { name: new RegExp(`^▼ ${t.short}`) }));
  fireEvent.change(screen.getByLabelText(t.amount), { target: { value: "750" } });
  fireEvent.change(screen.getByRole("slider"), { target: { value: "20" } });
  fireEvent.change(screen.getByLabelText(t.sl), { target: { value: "84000" } });
  fireEvent.click(screen.getByRole("button", { name: t.open.replace("{side}", t.short) }));

  await vi.waitFor(() => expect(fetch.mock.calls.some(([url]) => url === "/api/game/positions")).toBe(true));
  const sent = fetch.mock.calls.find(([url]) => url === "/api/game/positions")!;
  expect(JSON.parse(sent[1]!.body as string)).toEqual({
    side: "short",
    margin_usd: "750.00",
    leverage: 20,
    tp_price: null,
    sl_price: "84000",
  });
});

test("a refused order explains why", async () => {
  backend({ "/api/game/me": [200, ME], "/api/game/positions": [422, { detail: "tp" }] });
  renderPlay();

  fireEvent.click(await screen.findByRole("button", { name: t.open.replace("{side}", t.long) }));

  expect((await screen.findByRole("alert")).textContent).toBe(t.errors.tp);
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

  fireEvent.click(await longButton());
  expect(screen.queryByLabelText(a.email)).toBeNull();
  fireEvent.click(within(screen.getByText(t.needLogin).closest("form")!).getByRole("button", { name: a.signup }));
  fireEvent.change(screen.getByLabelText(a.nickname), { target: { value: "satoshi" } });
  fireEvent.change(screen.getByLabelText(a.password), { target: { value: "pw" } });
  expect((screen.getByLabelText(a.email) as HTMLInputElement).required).toBe(true);
  expect((screen.getByLabelText(a.phone) as HTMLInputElement).required).toBe(false);
  fireEvent.submit(screen.getByLabelText(a.password).closest("form")!);

  expect(await screen.findByText(a.errTaken)).toBeTruthy();
});

test("a wrong password says so, the right one shows the account and the header menu", async () => {
  const fetch = backend({ "/api/game/me": [401, null], "/api/game/login": [401, null] });
  renderPlay();
  fireEvent.click(await longButton());
  fireEvent.change(screen.getByLabelText(a.nickname), { target: { value: "satoshi" } });
  fireEvent.change(screen.getByLabelText(a.password), { target: { value: "nope" } });
  fireEvent.submit(screen.getByLabelText(a.password).closest("form")!);
  expect(await screen.findByText(a.errLogin)).toBeTruthy();

  fetch.mockImplementation(async (url) =>
    new Response(JSON.stringify(url === "/api/game/login" || url === "/api/game/me" ? ME : { rows: [], points: [] }), { status: 200 }),
  );
  fireEvent.submit(screen.getByLabelText(a.password).closest("form")!);

  expect(await screen.findByText("$10,245")).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: a.account }));
  expect(screen.getByText(a.logout)).toBeTruthy();
});
