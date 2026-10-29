import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";
import { Play } from "@/components/home/play/Play";
import { getDictionary } from "@/i18n";

test("the game section shows the four rules and the virtual money notice", () => {
  const t = getDictionary("fa").play;
  render(<Play t={t} />);

  expect(screen.getAllByRole("listitem")).toHaveLength(4);
  expect(screen.getByText(t.rules[3][0])).toBeTruthy();
  expect(screen.getByText(t.virtual)).toBeTruthy();
});
