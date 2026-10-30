import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, test } from "vitest";
import { ScoreRing } from "@/components/home/jobfit/ScoreRing";
import { media } from "./setup";

afterEach(() => {
  cleanup();
  media.reduceMotion = false;
});

test("with reduced motion the score ring shows the final score without counting up", async () => {
  media.reduceMotion = true;
  render(<ScoreRing score={78} of="of 100" lang="en" />);

  expect(await screen.findByText("78")).toBeTruthy();
});
