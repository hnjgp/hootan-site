import type { Dictionary } from "@/i18n";
import { Box, COLOR, dirOf, Edge, Label, Svg, type Tone } from "./kit";

type D = Dictionary["projects"]["items"]["behengam"]["d"];

const CX = 360;
const CY = 160;
/** Where role k sits on the ellipse around the shared record, starting with the patient at the top. */
const at = (k: number) => {
  const a = ((-90 + 30 * k) * Math.PI) / 180;
  return [
    Math.round(CX + 280 * Math.cos(a)),
    Math.round(CY + 125 * Math.sin(a)),
  ];
};
const PATIENT = 0;
const DOCTOR = 1;
const PHARMACY = 2;
const LAB = 3;
const INSURANCE = 10;
/** A prescription (orange) and a lab result (green) each travel through the shared record to three roles. */
const TRIPS: [number, number[], Tone][] = [
  [DOCTOR, [PATIENT, PHARMACY, INSURANCE], "orange"],
  [LAB, [PATIENT, DOCTOR, INSURANCE], "green"],
];

function Hub({ d }: { d: D }) {
  const line = (a: number[], b: number[]) =>
    `M${a[0]} ${a[1]} L${b[0]} ${b[1]}`;
  const center = [CX, CY];
  return (
    <Svg w={720} h={330} label={d.hub}>
      {d.roles.map((_, k) => (
        <path
          key={k}
          d={line(at(k), center)}
          stroke="var(--muted)"
          strokeOpacity={0.35}
          strokeWidth={1.2}
        />
      ))}
      {TRIPS.map(([from, to, tone], t) => (
        <g key={from}>
          <Edge
            d={line(at(from), center)}
            tone={tone}
            delay={t * 2.4}
            dur={4.8}
          />
          {to.map((k) => (
            <Edge
              key={k}
              d={line(center, at(k))}
              tone={tone}
              delay={t * 2.4 + 1.2}
              dur={4.8}
            />
          ))}
        </g>
      ))}
      <circle
        cx={CX}
        cy={CY}
        r={62}
        fill="var(--card)"
        stroke={COLOR.orange}
        strokeWidth={2.5}
      />
      <circle
        cx={CX}
        cy={CY}
        r={62}
        fill={COLOR.orange}
        fillOpacity={0}
        className="glow"
      />
      <text
        x={CX}
        y={CY - 2}
        textAnchor="middle"
        direction={dirOf(d.center[0])}
        fontSize={14}
        fontWeight={700}
        fill="var(--ink)"
      >
        {d.center[0]}
      </text>
      <text
        x={CX}
        y={CY + 16}
        textAnchor="middle"
        direction={dirOf(d.center[1])}
        fontSize={10.5}
        fill="var(--muted)"
      >
        {d.center[1]}
      </text>
      {d.roles.map((role, k) => {
        const [x, y] = at(k);
        const tone: Tone =
          k === DOCTOR || k === LAB
            ? k === DOCTOR
              ? "orange"
              : "green"
            : "ink";
        return (
          <Box
            key={role}
            x={x - 66}
            y={y - 15}
            w={132}
            h={30}
            title={role}
            tone={tone}
          />
        );
      })}
      {d.legend.map((text, k) => (
        <g key={text}>
          <rect
            x={k ? 375 : 15}
            y={312}
            width={22}
            height={5}
            rx={2.5}
            fill={COLOR[k ? "green" : "orange"]}
          />
          <Label x={k ? 405 : 45} y={319} anchor="start">
            {text}
          </Label>
        </g>
      ))}
    </Svg>
  );
}

const HISTORY = [6.1, 6.3, 6.2, 6.6, 6.8, 6.7, 7.0, 7.2, 7.1];
const FORECAST = [7.1, 7.3, 7.45, 7.6, 7.7];
const SPREAD = [0, 0.15, 0.3, 0.45, 0.6];
const px = (i: number) => 50 + i * 53;
const py = (v: number) => 190 - ((v - 5.6) / 2.6) * 170;

/** A marker over time with a forecast and its confidence band; the data is made up for the picture. */
function Trend({ d }: { d: D }) {
  const today = HISTORY.length - 1;
  const hist = HISTORY.map((v, i) => `${i ? "L" : "M"}${px(i)} ${py(v)}`).join(
    " ",
  );
  const fore = FORECAST.map(
    (v, i) => `${i ? "L" : "M"}${px(today + i)} ${py(v)}`,
  ).join(" ");
  const upper = FORECAST.map((v, i) => `${px(today + i)} ${py(v + SPREAD[i])}`);
  const lower = FORECAST.map(
    (v, i) => `${px(today + i)} ${py(v - SPREAD[i])}`,
  ).reverse();
  return (
    <Svg w={720} h={232} label={d.trend}>
      <path d="M50 190 H700" stroke="var(--line)" strokeWidth={1.5} />
      <path d="M50 20 V190" stroke="var(--line)" strokeWidth={1.5} />
      <polygon
        points={[...upper, ...lower].join(" ")}
        fill={COLOR.blue}
        fillOpacity={0.18}
        className="fade-in"
        style={{ animationDelay: "2s" }}
      />
      <path
        d={fore}
        fill="none"
        stroke={COLOR.blue}
        strokeWidth={2.5}
        strokeDasharray="6 5"
        className="fade-in"
        style={{ animationDelay: "2s" }}
      />
      <path
        d={hist}
        pathLength={100}
        fill="none"
        stroke={COLOR.orange}
        strokeWidth={3}
        strokeLinejoin="round"
        className="draw"
      />
      {HISTORY.map((v, i) => (
        <circle
          key={i}
          cx={px(i)}
          cy={py(v)}
          r={4}
          fill="var(--card)"
          stroke={COLOR.orange}
          strokeWidth={2}
          className="fade-in"
          style={{ animationDelay: `${i * 0.22}s` }}
        />
      ))}
      <path
        d={`M${px(today)} 20 V190`}
        stroke="var(--muted)"
        strokeDasharray="3 4"
      />
      <Label x={px(today)} y={210}>
        {d.today}
      </Label>
      <Label x={px(2)} y={py(6.2) - 14} tone="orange">
        {d.marker}
      </Label>
      <Label x={px(today + 2)} y={py(7.45) - 16} tone="blue">
        {d.forecast}
      </Label>
      <Label x={px(today + 3)} y={py(7.6) + 42} tone="blue">
        {d.band}
      </Label>
      <Label x={64} y={30} anchor="start">
        {d.sample}
      </Label>
    </Svg>
  );
}

/** The planned pipeline of the real product, from lab messages to an AI suggestion for the doctor. */
function Road({ d }: { d: D }) {
  const spots = [
    [10, 20],
    [250, 20],
    [490, 20],
    [490, 120],
    [250, 120],
    [10, 120],
  ];
  const tones: Tone[] = ["blue", "ink", "orange", "green", "blue", "green"];
  return (
    <Svg w={720} h={190} label={d.road}>
      <Edge d="M220 43 H250" delay={0} />
      <Edge d="M460 43 H490" delay={0.5} />
      <Edge d="M595 66 V120" delay={1} />
      <Edge d="M490 143 H460" delay={1.5} />
      <Edge d="M250 143 H220" tone="green" delay={2} />
      {d.boxes.map(([title, sub], k) => (
        <Box
          key={title}
          x={spots[k][0]}
          y={spots[k][1]}
          w={210}
          title={title}
          sub={sub}
          tone={tones[k]}
          glow={k === 5}
        />
      ))}
    </Svg>
  );
}

export const BEHENGAM = { hub: Hub, trend: Trend, road: Road };
