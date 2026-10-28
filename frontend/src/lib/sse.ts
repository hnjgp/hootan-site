/**
 * Turns Server-Sent Events text, arriving in arbitrary chunks, into whole events.
 * Returns a push function; each complete event calls onEvent(name, parsed JSON data).
 */
export function sseParser(onEvent: (name: string, data: unknown) => void) {
  let buffer = "";
  return (chunk: string) => {
    buffer += chunk.replace(/\r\n?/g, "\n");
    let end;
    while ((end = buffer.indexOf("\n\n")) >= 0) {
      const block = buffer.slice(0, end);
      buffer = buffer.slice(end + 2);
      let name = "message";
      const data: string[] = [];
      for (const line of block.split("\n")) {
        if (line.startsWith("event:")) name = line.slice(6).trim();
        else if (line.startsWith("data:")) data.push(line.slice(5).trimStart());
      }
      if (data.length) onEvent(name, JSON.parse(data.join("\n")));
    }
  };
}
