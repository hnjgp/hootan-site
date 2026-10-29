import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";
import { AuthForm } from "@/components/auth/AuthForm";
import { AuthProvider } from "@/components/auth/AuthProvider";
import { getDictionary } from "@/i18n";

const t = getDictionary("en").auth;

/** A fake backend answering by path; every call is recorded. */
function backend(routes: Record<string, [number, unknown]>) {
  const fetch = vi.fn<(url: string, init?: RequestInit) => Promise<Response>>(async (url) => {
    const [status, body] = routes[url] ?? [401, null];
    return new Response(body === null ? null : JSON.stringify(body), { status });
  });
  vi.stubGlobal("fetch", fetch);
  return fetch;
}

const type = (name: string, value: string) => fireEvent.change(screen.getByPlaceholderText(name), { target: { value } });
const sent = (fetch: ReturnType<typeof backend>, url: string) =>
  JSON.parse(String(fetch.mock.calls.find(([u]) => u === url)![1]!.body));

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

test("a forgotten password: email, then the code and a new password log in", async () => {
  const fetch = backend({
    "/api/game/password/forgot": [204, null],
    "/api/game/password/reset": [200, { nickname: "satoshi" }],
  });
  const done = vi.fn();
  render(
    <AuthProvider>
      <AuthForm t={t} onDone={done} />
    </AuthProvider>,
  );

  fireEvent.click(screen.getByRole("button", { name: t.forgot }));
  type(t.email, "a@b.com");
  fireEvent.click(screen.getByRole("button", { name: t.send }));
  expect(await screen.findByText(t.sent)).toBeTruthy();
  expect(sent(fetch, "/api/game/password/forgot").email).toBe("a@b.com");

  type(t.code, "123456");
  type(t.newPassword, "new");
  fireEvent.click(screen.getByRole("button", { name: t.reset }));

  await vi.waitFor(() => expect(done).toHaveBeenCalled());
  expect(sent(fetch, "/api/game/password/reset")).toMatchObject({ email: "a@b.com", code: "123456", password: "new" });
});

test("a wrong code says so and keeps the form", async () => {
  backend({ "/api/game/password/forgot": [204, null], "/api/game/password/reset": [400, { detail: "x" }] });
  render(
    <AuthProvider>
      <AuthForm t={t} />
    </AuthProvider>,
  );

  fireEvent.click(screen.getByRole("button", { name: t.forgot }));
  type(t.email, "a@b.com");
  fireEvent.click(screen.getByRole("button", { name: t.send }));
  await screen.findByPlaceholderText(t.code);
  type(t.code, "000000");
  type(t.newPassword, "new");
  fireEvent.click(screen.getByRole("button", { name: t.reset }));

  expect((await screen.findByRole("alert")).textContent).toBe(t.errCode);
});

test("signing up with an email that has an account names the email", async () => {
  backend({ "/api/game/players": [409, { detail: "Email taken" }] });
  render(
    <AuthProvider>
      <AuthForm t={t} start="signup" />
    </AuthProvider>,
  );

  type(t.email, "a@b.com");
  type(t.nickname, "new_one");
  type(t.password, "pw");
  fireEvent.click(screen.getByRole("button", { name: t.signup }));

  expect((await screen.findByRole("alert")).textContent).toBe(t.errEmailTaken);
});
