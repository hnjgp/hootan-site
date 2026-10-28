import { expect, test } from "vitest";
import { sseParser } from "@/lib/sse";

function collect(chunks: string[]) {
  const events: [string, unknown][] = [];
  const push = sseParser((name, data) => events.push([name, data]));
  chunks.forEach(push);
  return events;
}

test("events split across chunks arrive whole", () => {
  const events = collect(['event: token\r\ndata: {"te', 'xt": "Hi"}\r\n', "\r\nevent: done\r\ndata: {}\r\n\r\n"]);

  expect(events).toEqual([
    ["token", { text: "Hi" }],
    ["done", {}],
  ]);
});

test("an unfinished event waits for the rest", () => {
  expect(collect(["event: status\ndata: {}\n"])).toEqual([]);
});
