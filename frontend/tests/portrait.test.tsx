import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, test } from "vitest";
import { Portrait } from "@/components/home/twin/Portrait";
import { getDictionary } from "@/i18n";

const t = getDictionary("fa").twin;

afterEach(cleanup);

function visible() {
  return screen.getAllByRole("img", { hidden: true }).find((img) => img.parentElement!.style.opacity === "1")?.getAttribute("src");
}

test("listening shows the listening picture and label", () => {
  render(<Portrait t={t} phase="listen" word={0} />);

  expect(visible()).toBe("/assets/me_listen.webp");
  expect(screen.getByText(t.listen)).toBeTruthy();
});

test("searching shows the thinking picture, an old word and the file", () => {
  render(<Portrait t={t} phase="search" word={0} file="resume_fa.md" />);

  expect(visible()).toBe("/assets/me_think.webp");
  expect(screen.getByText(t.words.search[0][0])).toBeTruthy();
  expect(screen.getByText(`${t.searching} resume_fa.md`)).toBeTruthy();
});

test("writing shows the talking picture and a writing word", () => {
  render(<Portrait t={t} phase="talk" word={1} />);

  expect(visible()).toBe("/assets/me_talk.webp");
  expect(screen.getByText(t.words.talk[1][0])).toBeTruthy();
});
