import type { Dictionary } from "@/i18n";
import { Box, Edge, Label, Svg } from "./kit";

type D = Dictionary["projects"]["items"]["notes"]["d"];

/** The doctor's notes go through Clerk and FastAPI to OpenAI, and the answer streams back to the browser. */
function Flow({ d }: { d: D }) {
  return (
    <Svg w={720} h={185} label={d.flow}>
      <Edge d="M130 43 H165" delay={0} />
      <Edge d="M285 43 H320" tone="blue" delay={0.4} />
      <Edge d="M470 43 H505" delay={0.8} />
      <Edge d="M607 66 V143 H310" tone="green" delay={1.2} dur={2} />
      <Edge d="M580 66 V125 H310" tone="green" delay={1.6} dur={2} />
      <Label x={450} y={116} tone="green">
        {d.sse}
      </Label>
      <Box x={10} y={20} w={120} title={d.doc[0]} sub={d.doc[1]} />
      <Box
        x={165}
        y={20}
        w={120}
        title={d.clerk[0]}
        sub={d.clerk[1]}
        tone="blue"
      />
      <Box
        x={320}
        y={20}
        w={150}
        title={d.api[0]}
        sub={d.api[1]}
        tone="orange"
        glow
      />
      <Box x={505} y={20} w={205} title={d.ai[0]} sub={d.ai[1]} tone="blue" />
      <Box
        x={10}
        y={112}
        w={300}
        title={d.browser[0]}
        sub={d.browser[1]}
        tone="green"
        glow
        delay={1.6}
      />
    </Svg>
  );
}

const WIDTHS = [92, 78, 86, 60];

/** Three texts for three readers fill in line by line, like the streamed answer. */
function Outputs({ d }: { d: D }) {
  return (
    <div className="grid gap-3 sm:grid-cols-3">
      {d.outputs.map(([title, who], k) => (
        <div
          key={title}
          className="rounded-2xl border-[1.5px] border-line bg-bg p-4"
        >
          <div className="text-[15px] font-bold">{title}</div>
          <div className="mb-3 text-[12.5px] text-muted">{who}</div>
          {WIDTHS.map((w, i) => (
            <div
              key={i}
              className="grow-bar mb-2 h-2 rounded-full"
              style={{
                width: `${w}%`,
                background: ["var(--orange)", "var(--blue)", "var(--green)"][k],
                opacity: 0.75,
                animationDelay: `${0.3 + k * 0.4 + i * 0.35}s`,
              }}
            />
          ))}
        </div>
      ))}
    </div>
  );
}

export const NOTES = { flow: Flow, outputs: Outputs };
