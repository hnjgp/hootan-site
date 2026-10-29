import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, test } from "vitest";
import { Projects } from "@/components/home/projects/Projects";
import { getDictionary } from "@/i18n";

const dict = getDictionary("en");
const t = dict.projects;

beforeEach(() => {
  Element.prototype.scrollIntoView = () => {};
});
afterEach(cleanup);

function renderProjects() {
  render(<Projects t={t} agents={dict.trading.agents} lang="en" />);
}

test("a card opens its project in the large box and the cross brings the cards back", () => {
  renderProjects();

  fireEvent.click(screen.getByText(t.items.astra.title));
  expect(
    screen.getByRole("region", { name: t.items.astra.title }),
  ).toBeTruthy();
  expect(screen.getByText(t.items.astra.lead)).toBeTruthy();
  expect(screen.getByText(t.github).closest("a")!.href).toBe(
    "https://github.com/hnjgp/astra-ai-platform",
  );

  fireEvent.click(screen.getByLabelText(t.close));
  expect(screen.queryByRole("region")).toBeNull();
  expect(screen.getByText(t.items.site.title)).toBeTruthy();
});

test("Price Estimate opens with its diagrams and links to its repository", () => {
  renderProjects();

  fireEvent.click(screen.getByText(t.items.price.title));

  expect(screen.getByRole("img", { name: t.items.price.d.flow })).toBeTruthy();
  expect(
    screen.getByRole("img", { name: t.items.price.d.ladder }),
  ).toBeTruthy();
  expect(screen.getByText(t.github).closest("a")!.href).toBe(
    "https://github.com/hnjgp/price-estimate",
  );
});

test("Escape closes the box", () => {
  renderProjects();

  fireEvent.click(screen.getByText(t.items.notes.title));
  fireEvent.keyDown(window, { key: "Escape" });

  expect(screen.queryByRole("region")).toBeNull();
});

test("a project without public code links to the GitHub profile and says so", () => {
  renderProjects();

  fireEvent.click(screen.getByText(t.items.behengam.title));

  expect(screen.getByText(t.private)).toBeTruthy();
  expect(screen.getByText(t.profile).closest("a")!.href).toBe(
    "https://github.com/hnjgp",
  );
});

test("a link to #project-site anywhere on the page opens this site's project", () => {
  renderProjects();
  const link = document.createElement("a");
  link.href = "#project-site";
  document.body.append(link);

  fireEvent.click(link);

  expect(screen.getByRole("region", { name: t.items.site.title })).toBeTruthy();
  link.remove();
});
