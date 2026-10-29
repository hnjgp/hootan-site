import type { Dictionary } from "@/i18n";
import { Bars, Box, Edge, Label, Svg } from "./kit";

type D = Dictionary["projects"]["items"]["price"]["d"];

/** Products are cleaned and summarized, priced by three models, and blended into one estimate. */
function Flow({ d }: { d: D }) {
  return (
    <Svg w={720} h={240} label={d.flow}>
      <Edge d="M130 91 H150" delay={0} />
      <Edge d="M265 91 H278 V33 H290" delay={0.4} />
      <Edge d="M265 91 H290" tone="blue" delay={0.5} />
      <Edge d="M265 91 H278 V149 H290" tone="green" delay={0.6} />
      <Edge d="M365 184 V172" tone="green" delay={0.9} dur={1.6} dashed />
      <Edge d="M440 33 H455 V91 H470" delay={1.2} />
      <Edge d="M440 91 H470" tone="blue" delay={1.3} />
      <Edge d="M440 149 H455 V91 H470" tone="green" delay={1.4} />
      <Edge d="M580 91 H592 V63 H605" delay={1.9} />
      <Edge d="M580 91 H592 V119 H605" delay={2.1} />
      <Box x={5} y={68} w={125} title={d.data[0]} sub={d.data[1]} />
      <Box x={150} y={68} w={115} title={d.sum[0]} sub={d.sum[1]} />
      <Box
        x={290}
        y={10}
        w={150}
        title={d.dnn[0]}
        sub={d.dnn[1]}
        tone="orange"
      />
      <Box
        x={290}
        y={68}
        w={150}
        title={d.lora[0]}
        sub={d.lora[1]}
        tone="blue"
      />
      <Box
        x={290}
        y={126}
        w={150}
        title={d.rag[0]}
        sub={d.rag[1]}
        tone="green"
      />
      <Box x={290} y={184} w={150} title={d.chroma[0]} sub={d.chroma[1]} />
      <Box
        x={470}
        y={68}
        w={110}
        title={d.ens[0]}
        sub={d.ens[1]}
        tone="orange"
        glow
        delay={1.4}
      />
      <Box x={605} y={40} w={110} title={d.api[0]} sub={d.api[1]} />
      <Box x={605} y={96} w={110} title={d.agents[0]} sub={d.agents[1]} />
    </Svg>
  );
}

/** Mean absolute error of each classic model on the same 200 test items; shorter is better. */
function Ladder({ d }: { d: D }) {
  const [constant, linear, words, xgb, forest, nn] = d.rows;
  const row = (
    r: string[],
    value: number,
    tone: "ink" | "blue" | "orange" | "green",
  ) => ({
    name: r[0],
    value,
    max: 110,
    text: r[1],
    tone,
  });
  return (
    <Bars
      label={d.ladder}
      rows={[
        row(constant, 106, "ink"),
        row(linear, 92, "blue"),
        row(words, 80, "blue"),
        row(xgb, 74, "orange"),
        row(forest, 71, "orange"),
        row(nn, 72, "green"),
      ]}
    />
  );
}

/** The scanner finds deals, the planner asks the ensemble for each one's value and alerts on the best. */
function Agents({ d }: { d: D }) {
  return (
    <Svg w={720} h={190} label={d.agentsFlow}>
      <Edge d="M130 43 H160" delay={0} />
      <Edge d="M310 43 H345" delay={0.4} />
      <Edge d="M495 35 H560" tone="blue" delay={0.8} dur={1.8} />
      <Edge d="M560 51 H495" tone="green" delay={1.4} dur={1.8} />
      <Edge d="M420 66 V130" tone="orange" delay={2} dur={1.8} />
      <Edge d="M495 153 H545" tone="green" delay={2.6} dur={1.8} />
      <Edge d="M345 153 H310" delay={2.8} dur={1.6} dashed />
      <Edge d="M235 130 V66" tone="blue" delay={0.2} dur={1.8} dashed />
      <Label x={527} y={12}>
        {d.edges[0]}
      </Label>
      <Label x={430} y={102} anchor="start" tone="orange">
        {d.edges[1]}
      </Label>
      <Label x={225} y={102} anchor="end">
        {d.edges[2]}
      </Label>
      <Box x={10} y={20} w={120} title={d.rss[0]} sub={d.rss[1]} />
      <Box
        x={160}
        y={20}
        w={150}
        title={d.scan[0]}
        sub={d.scan[1]}
        tone="blue"
      />
      <Box
        x={345}
        y={20}
        w={150}
        title={d.plan[0]}
        sub={d.plan[1]}
        tone="orange"
        glow
      />
      <Box x={560} y={20} w={150} title={d.est[0]} sub={d.est[1]} tone="blue" />
      <Box x={160} y={130} w={150} title={d.mem[0]} sub={d.mem[1]} />
      <Box
        x={345}
        y={130}
        w={150}
        title={d.msg[0]}
        sub={d.msg[1]}
        tone="green"
      />
      <Box
        x={545}
        y={130}
        w={165}
        title={d.you[0]}
        sub={d.you[1]}
        tone="green"
        glow
        delay={2.6}
      />
    </Svg>
  );
}

export const PRICE = { flow: Flow, ladder: Ladder, agents: Agents };
