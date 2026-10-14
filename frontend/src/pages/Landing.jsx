import { Link } from "react-router-dom";
import { ArrowRight, Newspaper, Scales, ChartBar, ShieldWarning, WifiSlash, GitBranch, Gauge } from "@phosphor-icons/react";

const AGENTS = [
  { n: "Agent 1", name: "Financial data analyst", icon: Scales, weight: "35%", text: "Scores valuation, margins, growth, return on equity and leverage from fundamentals. Seven rules, each visible in the report." },
  { n: "Agent 2", name: "News sentiment scanner", icon: Newspaper, weight: "25%", text: "Reads recent headlines against a finance lexicon with negation handling. Newer stories count more." },
  { n: "Agent 3", name: "Price signal reader", icon: ChartBar, weight: "40%", text: "RSI, MACD, SMA 50 and 200, Bollinger position and ATR, computed in pandas from a year of daily bars." },
  { n: "Agent 4", name: "Risk and brief writer", icon: ShieldWarning, weight: "haircut", text: "Measures volatility, drawdown, beta and debt. Shrinks bullish conviction by up to 40%, then writes the brief." },
];

const DEMO = [
  { label: "Fundamentals", score: 0.92, w: 92 },
  { label: "Sentiment", score: 0.21, w: 21 },
  { label: "Price signals", score: 0.32, w: 32 },
  { label: "Risk haircut", score: -0.12, w: 12, neg: true },
];

function HeroPanel() {
  return (
    <div className="rounded-[2rem] border border-line bg-white p-6 shadow-[0_24px_48px_-24px_rgba(24,24,27,0.18)] md:p-8" aria-label="Animated example of a run">
      <div className="flex items-center justify-between font-mono text-xs text-steel">
        <span className="flex items-center gap-2"><span className="pulse-dot size-2 rounded-full bg-accent" />running NVDA (sample data)</span>
        <span>4 agents</span>
      </div>
      <ul className="mt-6 space-y-5">
        {DEMO.map((d, i) => (
          <li key={d.label} className="lit" style={{ "--i": i }}>
            <div className="flex justify-between text-sm"><span>{d.label}</span><span className="font-mono tabular-nums">{d.score > 0 ? "+" : ""}{d.score.toFixed(2)}</span></div>
            <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-zinc-100">
              <div className={`fill h-full w-full rounded-full ${d.neg ? "bg-sell" : "bg-accent"}`} style={{ "--i": i, width: `${d.w}%` }} />
            </div>
          </li>
        ))}
      </ul>
      <div className="verdict mt-7 flex flex-wrap items-end justify-between gap-2 border-t border-line pt-5">
        <div><p className="font-mono text-xs text-steel">Rating</p><p className="text-3xl font-semibold tracking-tight text-accent">Buy</p></div>
        <p className="font-mono text-sm tabular-nums text-steel">score +0.39 / risk moderate</p>
      </div>
    </div>
  );
}

export default function Landing() {
  return (
    <>
      <section className="mx-auto grid min-h-[calc(100dvh-3.5rem)] max-w-7xl content-center items-center gap-12 px-4 py-16 md:px-8 grid-cols-[minmax(0,1fr)] lg:grid-cols-[1.15fr_0.85fr]">
        <div>
          <p className="rise font-mono text-sm text-accent">Multi-agent stock research</p>
          <h1 className="rise mt-4 max-w-[16ch] text-4xl font-semibold leading-[1.02] tracking-tighter md:text-6xl" style={{ "--i": 1 }}>
            Four agents read the stock. One brief comes out.
          </h1>
          <p className="rise mt-6 max-w-[56ch] text-base leading-relaxed text-steel md:text-lg" style={{ "--i": 2 }}>
            Fundamentals, news sentiment, price signals and risk run in parallel on a LangGraph pipeline. A deterministic scoring engine produces every number. The language model only writes the prose.
          </p>
          <div className="rise mt-9" style={{ "--i": 3 }}>
            <Link to="/research" className="press inline-flex min-h-11 items-center gap-2 rounded-lg bg-ink px-6 py-3 text-sm font-medium text-white hover:bg-zinc-700">
              Run a brief <ArrowRight size={16} weight="bold" />
            </Link>
          </div>
        </div>
        <div className="rise" style={{ "--i": 3 }}><HeroPanel /></div>
      </section>

      <section className="mx-auto max-w-7xl px-4 py-16 md:px-8" aria-labelledby="pipe-h">
        <h2 id="pipe-h" className="max-w-[22ch] text-3xl font-semibold tracking-tighter md:text-4xl">The pipeline, one agent at a time</h2>
        <div className="mt-12 divide-y divide-line border-y border-line">
          {AGENTS.map((a, i) => (
            <div key={a.n} className="grid gap-4 py-8 md:grid-cols-[10rem_1fr_8rem] md:items-start md:gap-10">
              <p className="font-mono text-sm text-steel">{a.n}</p>
              <div className={i % 2 ? "md:order-3 md:text-right" : ""}>
                <h3 className="flex items-center gap-2 text-xl font-semibold tracking-tight md:contents"><a.icon size={20} className="text-accent md:hidden" />{a.name}</h3>
                <p className="mt-2 max-w-[58ch] leading-relaxed text-steel md:ml-0 md:inline-block">{a.text}</p>
              </div>
              <p className={`font-mono text-sm md:text-right ${i % 2 ? "md:order-1 md:text-left" : ""}`}>weight <span className="text-ink">{a.weight}</span></p>
            </div>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 py-16 md:px-8" aria-labelledby="why-h">
        <div className="grid gap-12 lg:grid-cols-[0.8fr_1.2fr]">
          <h2 id="why-h" className="max-w-[18ch] text-3xl font-semibold tracking-tighter md:text-4xl">Built so the model cannot make numbers up</h2>
          <dl className="grid gap-x-10 gap-y-9 sm:grid-cols-2">
            {[
              [Gauge, "Rules own the numbers", "Scores, weights and the rating come from tested Python. The LLM gets the finished facts and may only describe them."],
              [GitBranch, "Failures degrade, not crash", "If one agent fails, its weight is redistributed and the report says which agent is degraded and why."],
              [WifiSlash, "Works with no network", "Bundled synthetic samples and a rules-only mode give an instant demo. No model download needed."],
              [ShieldWarning, "Honest limits", "Lexicon sentiment misses nuance, free data is delayed, and nothing here is advice. The method page lists the rest."],
            ].map(([Icon, t, d]) => (
              <div key={t}>
                <dt className="flex items-center gap-2 font-semibold"><Icon size={18} className="text-accent" />{t}</dt>
                <dd className="mt-2 text-sm leading-relaxed text-steel">{d}</dd>
              </div>
            ))}
          </dl>
        </div>
      </section>
    </>
  );
}
