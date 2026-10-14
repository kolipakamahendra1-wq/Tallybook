import { useMemo, useState } from "react";
import { CaretDown, Warning, Info } from "@phosphor-icons/react";
import Chart from "./Chart.jsx";

const AGENT_LABEL = {
  fundamentals: ["Agent 1", "Financial data analyst"],
  sentiment: ["Agent 2", "News sentiment scanner"],
  technicals: ["Agent 3", "Price signal reader"],
  risk_brief: ["Agent 4", "Risk and brief writer"],
};

export const ratingTone = (r) =>
  r === "Buy" ? "text-accent" : r === "Sell" ? "text-sell" : "text-steel";

/** Score -1..1 drawn as a centered bar: left of the midline is bearish, right is bullish. */
export function ScoreBar({ score }) {
  const pct = Math.min(Math.abs(score), 1) * 50;
  const pos = score >= 0;
  return (
    <div className="relative h-1.5 w-full rounded-full bg-zinc-200" role="img" aria-label={`Score ${score.toFixed(2)} on a scale of -1 to 1`}>
      <div className="absolute inset-y-[-3px] left-1/2 w-px bg-zinc-400" />
      <div
        className={`absolute inset-y-0 rounded-full ${pos ? "bg-accent" : "bg-sell"}`}
        style={{ width: `${pct}%`, left: pos ? "50%" : `${50 - pct}%` }}
      />
    </div>
  );
}

function Signals({ signals, isNews, risk }) {
  if (!signals.length) return null;
  return (
    <ul className="mt-4 divide-y divide-line border-t border-line text-sm">
      {signals.map((s, i) => (
        <li key={i} className="grid grid-cols-[1fr_auto] gap-x-4 gap-y-0.5 py-2.5">
          <span className={isNews ? "leading-snug" : "font-medium"}>{s.name}</span>
          <span className="text-right font-mono tabular-nums">{s.value}</span>
          <span className="text-xs text-steel">{s.note}</span>
          <span className={`text-right font-mono text-xs tabular-nums ${risk ? (s.effect >= 0.6 ? "text-sell" : "text-steel") : s.effect >= 0 ? "text-accent" : "text-sell"}`}>
            {risk ? `risk ${s.effect.toFixed(2)}` : `${s.effect >= 0 ? "+" : ""}${s.effect.toFixed(2)}`}
          </span>
        </li>
      ))}
    </ul>
  );
}

function AgentRow({ a, index }) {
  const [open, setOpen] = useState(false);
  const [num, name] = AGENT_LABEL[a.agent] || [a.agent, a.agent];
  const degraded = a.status !== "ok";
  const showScore = a.agent !== "risk_brief" || !degraded;
  return (
    <div className="rise py-5" style={{ "--i": index }}>
      <button className="grid w-full grid-cols-[1fr_auto] items-center gap-4 text-left md:grid-cols-[11rem_1fr_5rem_1.5rem]" onClick={() => setOpen(!open)} aria-expanded={open}>
        <span>
          <span className="block font-mono text-xs text-steel">{num}</span>
          <span className="font-medium">{name}</span>
        </span>
        <span className="col-span-2 order-last md:order-none md:col-span-1">
          {degraded ? (
            <span className="flex items-center gap-1.5 text-sm text-amber-700"><Warning size={16} weight="bold" /> Degraded: {a.error}</span>
          ) : (
            <ScoreBar score={a.score} />
          )}
        </span>
        <span className="text-right font-mono tabular-nums">{showScore && !degraded ? `${a.score >= 0 ? "+" : ""}${a.score.toFixed(2)}` : "n/a"}</span>
        <CaretDown size={16} className={`hidden transition-transform md:block ${open ? "rotate-180" : ""}`} />
      </button>
      {!degraded && <p className="mt-3 max-w-[70ch] text-sm leading-relaxed text-steel md:pl-[12rem]">{a.agent === "risk_brief" ? "Risk factors that cap bullish conviction." : a.summary}</p>}
      {open && <div className="md:pl-[12rem]"><Signals signals={a.signals} isNews={a.agent === "sentiment"} /></div>}
    </div>
  );
}

export default function ReportView({ report }) {
  const tech = report.agents.find((a) => a.agent === "technicals");
  const chart = tech?.status === "ok" ? tech.data.chart : null;
  const brief = report.agents.find((a) => a.agent === "risk_brief");
  const rating = report.rating;

  const priceTraces = useMemo(() => chart && [
    { x: chart.dates, y: chart.close, name: "Close", type: "scatter", mode: "lines", line: { color: "#18181b", width: 1.8 } },
    { x: chart.dates, y: chart.sma20, name: "SMA 20", type: "scatter", mode: "lines", line: { color: "#059669", width: 1.2 } },
    { x: chart.dates, y: chart.sma50, name: "SMA 50", type: "scatter", mode: "lines", line: { color: "#a1a1aa", width: 1.2, dash: "dot" } },
  ], [chart]);
  const rsiTraces = useMemo(() => chart && [
    { x: chart.dates, y: chart.rsi, name: "RSI 14", type: "scatter", mode: "lines", line: { color: "#18181b", width: 1.4 } },
  ], [chart]);
  const rsiLayout = useMemo(() => ({
    yaxis: { range: [0, 100], gridcolor: "#e4e4e7", tickvals: [30, 50, 70] },
    shapes: [30, 70].map((y) => ({ type: "line", xref: "paper", x0: 0, x1: 1, y0: y, y1: y, line: { color: "#a1a1aa", width: 1, dash: "dot" } })),
    showlegend: false,
  }), []);

  return (
    <article>
      {report.synthetic && (
        <p className="mb-6 flex items-start gap-2 border-l-2 border-amber-500 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          <Info size={18} weight="bold" className="mt-0.5 shrink-0" />
          Synthetic sample data. Prices, fundamentals and headlines were generated for demonstration and do not describe the real company.
        </p>
      )}
      <header className="grid gap-6 md:grid-cols-[1fr_auto] md:items-end">
        <div>
          <p className="font-mono text-sm text-steel">{report.mode} / {report.llm === "none" ? "rules only" : report.llm} / {report.elapsed_ms} ms</p>
          <h1 className="mt-1 text-5xl font-semibold tracking-tighter">{report.ticker}</h1>
        </div>
        <dl className="grid grid-cols-3 gap-8 font-mono">
          <div><dt className="text-xs text-steel">Rating</dt><dd className={`text-2xl font-semibold ${ratingTone(rating)}`}>{rating || "n/a"}</dd></div>
          <div><dt className="text-xs text-steel">Score</dt><dd className="text-2xl font-semibold tabular-nums">{report.score == null ? "n/a" : `${report.score >= 0 ? "+" : ""}${report.score.toFixed(2)}`}</dd></div>
          <div><dt className="text-xs text-steel">Risk</dt><dd className="text-2xl font-semibold">{report.risk_label || "n/a"}</dd></div>
        </dl>
      </header>

      <section className="mt-10 border-t border-line pt-8" aria-labelledby="brief-h">
        <h2 id="brief-h" className="font-mono text-xs uppercase tracking-wide text-steel">Brief</h2>
        <p className="mt-3 max-w-[68ch] text-lg leading-relaxed">{report.brief}</p>
        {brief?.data?.llm_error && (
          <p className="mt-3 text-sm text-amber-800">LLM unavailable, showing the rules-based brief. {brief.data.llm_error}</p>
        )}
        {report.degraded.length > 0 && (
          <p className="mt-3 text-sm text-amber-800">Degraded agents: {report.degraded.join(", ")}. The score uses the remaining agents.</p>
        )}
      </section>

      <section className="mt-10 border-t border-line" aria-label="Agents">
        <div className="divide-y divide-line">
          {report.agents.map((a, i) => <AgentRow key={a.agent} a={a} index={i} />)}
        </div>
        {brief?.signals?.length > 0 && (
          <div className="border-t border-line pt-5">
            <h3 className="font-mono text-xs uppercase tracking-wide text-steel">Risk inputs</h3>
            <Signals signals={brief.signals} risk />
          </div>
        )}
      </section>

      {chart && (
        <section className="mt-10 grid gap-8 border-t border-line pt-8 lg:grid-cols-[2fr_1fr]" aria-label="Charts">
          <div>
            <h3 className="font-mono text-xs uppercase tracking-wide text-steel">Price, last {chart.dates.length} sessions</h3>
            <Chart traces={priceTraces} label={`${report.ticker} price with moving averages`} />
          </div>
          <div>
            <h3 className="font-mono text-xs uppercase tracking-wide text-steel">RSI</h3>
            <Chart traces={rsiTraces} layout={rsiLayout} label={`${report.ticker} RSI`} />
          </div>
        </section>
      )}
    </article>
  );
}

export function ReportSkeleton() {
  return (
    <div aria-busy="true" aria-label="Running four agents">
      <div className="skeleton h-4 w-40" />
      <div className="skeleton mt-3 h-12 w-56" />
      <div className="mt-10 space-y-3 border-t border-line pt-8">
        <div className="skeleton h-5 w-full max-w-[68ch]" /><div className="skeleton h-5 w-full max-w-[60ch]" /><div className="skeleton h-5 w-2/3 max-w-[40ch]" />
      </div>
      <div className="mt-10 divide-y divide-line border-t border-line">
        {[0, 1, 2, 3].map((i) => <div key={i} className="py-5"><div className="skeleton h-5 w-48" /><div className="skeleton mt-3 h-1.5 w-full" /></div>)}
      </div>
    </div>
  );
}
