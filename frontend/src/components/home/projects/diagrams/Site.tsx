import type { Dictionary } from "@/i18n";
import { Bars, Box, COLOR, dirOf, Edge, Label, Svg, type Tone } from "./kit";

type D = Dictionary["projects"]["items"]["site"]["d"];
/** Every diagram gets the same props; only the trading team uses the agent names. */
type P = { d: D; agents: string[] };

/** The five Docker services, the model provider and the price sources. */
function Arch({ d }: P) {
  return (
    <Svg w={720} h={270} label={d.arch}>
      <rect
        x={118}
        y={8}
        width={455}
        height={248}
        rx={18}
        fill="none"
        stroke="var(--muted)"
        strokeDasharray="6 6"
      />
      <Label x={130} y={250} anchor="start">
        {d.box}
      </Label>
      <Edge d="M100 130 H125" delay={0} />
      <Edge d="M240 120 C258 120 252 43 270 43" delay={0.4} />
      <Edge d="M240 140 C258 140 252 203 270 203" delay={0.4} />
      <Edge d="M335 66 V180" dashed delay={0.8} />
      <Edge d="M400 195 C415 195 415 123 430 123" tone="green" delay={1.2} />
      <Edge d="M495 195 V146" tone="green" delay={1.6} />
      <Edge d="M600 123 C580 123 580 205 560 205" tone="blue" delay={2} />
      <Edge d="M560 225 H600" tone="blue" delay={2.4} />
      <Edge d="M335 226 V262 H655 V241" tone="blue" delay={2.8} dur={3} />
      <Box x={10} y={107} w={90} title={d.user[0]} sub={d.user[1]} />
      <Box
        x={125}
        y={107}
        w={115}
        title={d.caddy[0]}
        sub={d.caddy[1]}
        tone="orange"
      />
      <Box x={270} y={20} w={130} title={d.web[0]} sub={d.web[1]} tone="blue" />
      <Box
        x={270}
        y={180}
        w={130}
        title={d.api[0]}
        sub={d.api[1]}
        tone="orange"
        glow
      />
      <Box x={430} y={100} w={130} title={d.db[0]} sub={d.db[1]} tone="green" />
      <Box
        x={430}
        y={195}
        w={130}
        title={d.worker[0]}
        sub={d.worker[1]}
        glow
        delay={1.6}
      />
      <Box x={600} y={100} w={115} title={d.prices[0]} sub={d.prices[1]} />
      <Box
        x={600}
        y={195}
        w={115}
        title={d.avalai[0]}
        sub={d.avalai[1]}
        tone="blue"
      />
    </Svg>
  );
}

/** Hybrid search: vector and keyword results are merged before the model writes the answer. */
function Twin({ d }: P) {
  return (
    <Svg w={720} h={210} label={d.twin}>
      <Edge d="M110 98 C130 98 130 43 150 43" tone="blue" delay={0} />
      <Edge d="M110 118 C130 118 130 173 150 173" tone="green" delay={0} />
      <Edge d="M300 43 C320 43 320 98 340 98" tone="blue" delay={0.8} />
      <Edge d="M300 173 C320 173 320 118 340 118" tone="green" delay={0.8} />
      <Edge d="M440 108 H480" delay={1.6} />
      <Edge d="M590 98 C602 98 603 63 615 63" tone="green" delay={2.2} />
      <Edge
        d="M590 118 C602 118 603 163 615 163"
        tone="ink"
        dashed
        delay={2.2}
      />
      <Box x={10} y={85} w={100} title={d.q[0]} sub={d.q[1]} />
      <Box x={150} y={20} w={150} title={d.vec[0]} sub={d.vec[1]} tone="blue" />
      <Box x={150} y={150} w={150} title={d.bm[0]} sub={d.bm[1]} tone="green" />
      <Box
        x={340}
        y={85}
        w={100}
        title={d.rrf[0]}
        sub={d.rrf[1]}
        tone="orange"
        glow
      />
      <Box x={480} y={85} w={110} title={d.llm[0]} sub={d.llm[1]} tone="blue" />
      <Box
        x={615}
        y={40}
        w={100}
        title={d.sse[0]}
        sub={d.sse[1]}
        tone="green"
      />
      <Box x={615} y={140} w={100} title={d.hand[0]} sub={d.hand[1]} />
    </Svg>
  );
}

const BAND_TONES: Tone[] = ["ink", "blue", "orange", "green"];
const BANDS = [
  [0, 50],
  [50, 70],
  [70, 90],
  [90, 100],
];

/** The score bands the code enforces from the share of must-have skills. */
function Fit({ d }: P) {
  const x = (v: number) => 40 + v * 6.4;
  return (
    <Svg w={720} h={110} label={d.fit}>
      {BANDS.map(([from, to], k) => (
        <g key={from}>
          <rect
            x={x(from) + 2}
            y={36}
            width={x(to) - x(from) - 4}
            height={26}
            rx={8}
            fill={COLOR[BAND_TONES[k]]}
            fillOpacity={k ? 0.85 : 0.25}
            className="grow-bar"
            style={{ animationDelay: `${0.2 + k * 0.3}s` }}
          />
          <text
            x={(x(from) + x(to)) / 2}
            y={26}
            textAnchor="middle"
            fontSize={12.5}
            fontWeight={700}
            fontFamily="var(--font-mono)"
            fill="var(--ink)"
          >
            {d.bands[k][0]}
          </text>
          <text
            x={(x(from) + x(to)) / 2}
            y={84}
            textAnchor="middle"
            direction={dirOf(d.bands[k][1])}
            fontSize={11}
            fill="var(--muted)"
          >
            {d.bands[k][1]}
          </text>
        </g>
      ))}
    </Svg>
  );
}

/** Meeting order of the agents; `agents` and the avatar files follow the building's window order. */
const ORDER = [0, 1, 2, 3, 5, 4, 6];
const FILES = ["data", "news", "bull", "bear", "risk", "trader", "pm"];

/** One meeting: seven agents in a fixed order, the risk rules in code and the virtual portfolio. */
function Team({ d, agents }: P) {
  const ax = (k: number) => 55 + k * 102;
  return (
    <Svg w={720} h={215} label={d.team}>
      <defs>
        <clipPath id="team-avatar">
          <circle cx={0} cy={0} r={27} />
        </clipPath>
      </defs>
      {ORDER.slice(1).map((_, k) => (
        <Edge
          key={k}
          d={`M${ax(k) + 30} 50 H${ax(k + 1) - 30}`}
          delay={k * 0.45}
          dur={2.2}
        />
      ))}
      <Edge d={`M${ax(0)} 160 V102`} tone="blue" delay={0} />
      <Edge d={`M${ax(4)} 102 V140`} tone="orange" delay={1.8} />
      <Edge d={`M${ax(5)} 140 V102`} tone="orange" delay={2.3} />
      <Edge d={`M${ax(6)} 102 V140`} tone="green" delay={2.8} />
      {ORDER.map((i, k) => (
        <g key={i} transform={`translate(${ax(k)} 50)`}>
          <image
            href={`/assets/av_${FILES[i]}.jpg`}
            x={-27}
            y={-27}
            width={54}
            height={54}
            clipPath="url(#team-avatar)"
          />
          <circle
            r={27}
            fill="none"
            stroke="var(--line)"
            strokeWidth={1.8}
            className="ring-pulse"
            style={{ animationDelay: `${k * 0.45}s` }}
          />
          <text
            y={44}
            textAnchor="middle"
            direction={dirOf(agents[i])}
            fontSize={11}
            fontWeight={600}
            fill="var(--ink)"
          >
            {agents[i]}
          </text>
        </g>
      ))}
      <Box
        x={10}
        y={160}
        w={180}
        title={d.start[0]}
        sub={d.start[1]}
        tone="blue"
      />
      <Box
        x={ax(4) - 80}
        y={140}
        w={ax(5) - ax(4) + 105}
        title={d.rules[0]}
        sub={d.rules[1]}
        tone="orange"
      />
      <Box
        x={600}
        y={140}
        w={115}
        title={d.book[0]}
        sub={d.book[1]}
        tone="green"
      />
    </Svg>
  );
}

function Cost({ d }: P) {
  const [trading, twin, fit, cap] = d.rows;
  return (
    <Bars
      label={d.cost}
      rows={[
        {
          name: trading[0],
          value: 1.5,
          max: 5,
          text: trading[1],
          tone: "orange",
        },
        { name: twin[0], value: 0.6, max: 5, text: twin[1], tone: "blue" },
        { name: fit[0], value: 0.2, max: 5, text: fit[1], tone: "green" },
        { name: cap[0], value: 5, max: 5, text: cap[1], tone: "ink" },
      ]}
    />
  );
}

export const SITE = {
  arch: Arch,
  twin: Twin,
  fit: Fit,
  team: Team,
  cost: Cost,
};
