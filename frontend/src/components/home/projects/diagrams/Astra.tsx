import type { Dictionary } from "@/i18n";
import { Bars, Box, COLOR, dirOf, Edge, Label, Svg, type Tone } from "./kit";

type D = Dictionary["projects"]["items"]["astra"]["d"];

/** One request: middleware, auth and the input guardrail, then the agent with its tools, RAG and the model. */
function Flow({ d }: { d: D }) {
  return (
    <Svg w={720} h={252} label={d.flow}>
      <Edge d="M110 43 H140" delay={0} />
      <Edge d="M270 43 H300" delay={0.3} />
      <Edge d="M420 43 H450" delay={0.6} />
      <Edge d="M570 43 H600" delay={0.9} />
      <Edge d="M655 66 V110" tone="blue" delay={1.2} />
      <Edge d="M615 66 C590 90 560 95 535 110" delay={1.4} />
      <Edge d="M430 133 H400" tone="green" delay={1.8} />
      <Edge d="M250 133 H220" tone="green" delay={2.1} />
      <Edge d="M655 156 V219 H580" tone="green" delay={2.4} />
      <Box x={10} y={20} w={100} title={d.client[0]} sub={d.client[1]} />
      <Box x={140} y={20} w={130} title={d.mw[0]} sub={d.mw[1]} />
      <Box
        x={300}
        y={20}
        w={120}
        title={d.auth[0]}
        sub={d.auth[1]}
        tone="blue"
      />
      <Box
        x={450}
        y={20}
        w={120}
        title={d.guard[0]}
        sub={d.guard[1]}
        tone="orange"
      />
      <Box
        x={600}
        y={20}
        w={115}
        title={d.agent[0]}
        sub={d.agent[1]}
        tone="orange"
        glow
      />
      <Box
        x={600}
        y={110}
        w={115}
        title={d.llm[0]}
        sub={d.llm[1]}
        tone="blue"
      />
      <Box x={400} y={110} w={170} title={d.exec[0]} sub={d.exec[1]} />
      <Box
        x={220}
        y={110}
        w={180}
        title={d.rag[0]}
        sub={d.rag[1]}
        tone="green"
        glow
        delay={1.6}
      />
      <Box x={70} y={110} w={150} title={d.pg[0]} sub={d.pg[1]} tone="green" />
      <Box
        x={250}
        y={196}
        w={330}
        title={d.out[0]}
        sub={d.out[1]}
        tone="green"
      />
    </Svg>
  );
}

/** The graph: model and tools in a loop, a recovery path for errors and a pause for human approval. */
function Loop({ d }: { d: D }) {
  const [calls, result, error, sensitive, done] = d.edges;
  return (
    <Svg w={720} h={215} label={d.loop}>
      <Edge d="M335 66 V140" delay={0} />
      <Edge d="M385 140 V66" tone="green" delay={1.2} />
      <Edge
        d="M280 163 C200 170 115 165 115 126"
        tone="orange"
        delay={0.6}
        dur={3}
      />
      <Edge
        d="M115 80 C115 50 200 43 280 43"
        tone="orange"
        delay={1.6}
        dur={3}
      />
      <Edge d="M440 163 H530" tone="blue" delay={0.8} />
      <Edge d="M440 43 H530" tone="green" delay={2} />
      <Label x={320} y={108} anchor="end">
        {calls}
      </Label>
      <Label x={400} y={108} anchor="start" tone="green">
        {result}
      </Label>
      <Label x={180} y={186} tone="orange">
        {error}
      </Label>
      <Label x={485} y={155} tone="blue">
        {sensitive}
      </Label>
      <Label x={485} y={35} tone="green">
        {done}
      </Label>
      <Box
        x={280}
        y={20}
        w={160}
        title={d.model[0]}
        sub={d.model[1]}
        tone="orange"
        glow
      />
      <Box
        x={280}
        y={140}
        w={160}
        title={d.tools[0]}
        sub={d.tools[1]}
        glow
        delay={1.6}
      />
      <Box
        x={40}
        y={80}
        w={150}
        title={d.recovery[0]}
        sub={d.recovery[1]}
        tone="orange"
      />
      <Box
        x={530}
        y={140}
        w={180}
        title={d.approval[0]}
        sub={d.approval[1]}
        tone="blue"
      />
      <Box
        x={530}
        y={20}
        w={180}
        title={d.answer[0]}
        sub={d.answer[1]}
        tone="green"
      />
    </Svg>
  );
}

const ROUTE_TONES: Tone[] = ["ink", "blue", "green", "orange"];

/** The agent chooses one of four routes for each question. */
function Routes({ d }: { d: D }) {
  return (
    <Svg w={720} h={200} label={d.routes}>
      <Edge d="M130 100 H170" delay={0} />
      {d.r.map((_, k) => (
        <Edge
          key={k}
          d={`M300 100 C340 100 340 ${25 + k * 50} 380 ${25 + k * 50}`}
          tone={ROUTE_TONES[k] === "ink" ? "orange" : ROUTE_TONES[k]}
          delay={0.6 + k * 0.5}
          dur={3}
        />
      ))}
      <Box x={10} y={77} w={120} title={d.q} />
      <Box x={170} y={77} w={130} title={d.decide} tone="orange" glow />
      {d.r.map(([name, what], k) => (
        <Box
          key={name}
          x={380}
          y={5 + k * 50}
          w={330}
          h={40}
          title={name}
          sub={what}
          tone={ROUTE_TONES[k]}
        />
      ))}
    </Svg>
  );
}

const LAYER_TONES: Tone[] = ["blue", "ink", "orange", "green", "blue"];

/** Five nested layers around the model; a request has to cross every one of them. */
function Layers({ d }: { d: D }) {
  return (
    <Svg w={720} h={262} label={d.layers}>
      {d.l.map(([name, what], k) => {
        const x = 10 + k * 115;
        const y = 10 + k * 18;
        return (
          <g key={name}>
            <rect
              x={x}
              y={y}
              width={700 - 115 * k}
              height={242 - 36 * k}
              rx={16}
              fill={k % 2 ? "var(--card)" : "var(--soft)"}
              stroke={COLOR[LAYER_TONES[k]]}
              strokeWidth={2}
            />
            <text
              x={x + 57}
              y={112}
              textAnchor="middle"
              fontSize={12}
              fontWeight={700}
              fill="var(--ink)"
            >
              {name}
            </text>
            <text
              x={x + 57}
              y={127}
              textAnchor="middle"
              direction={dirOf(what)}
              fontSize={10}
              fill="var(--muted)"
            >
              {what}
            </text>
          </g>
        );
      })}
      <Box
        x={565}
        y={124}
        w={135}
        h={52}
        title={d.core[0]}
        sub={d.core[1]}
        tone="orange"
        glow
      />
      <Edge d="M0 150 H565" delay={0} dur={3.2} />
    </Svg>
  );
}

function Quality({ d }: { d: D }) {
  const [cov, recall, mrr, tests] = d.rows;
  return (
    <Bars
      label={d.bars}
      rows={[
        { name: cov[0], value: 93, max: 100, text: cov[1], tone: "green" },
        { name: recall[0], value: 1, max: 1, text: recall[1], tone: "blue" },
        { name: mrr[0], value: 1, max: 1, text: mrr[1], tone: "blue" },
        {
          name: tests[0],
          value: 407,
          max: 407,
          text: tests[1],
          tone: "orange",
        },
      ]}
    />
  );
}

export const ASTRA = {
  flow: Flow,
  loop: Loop,
  routes: Routes,
  layers: Layers,
  bars: Quality,
};
