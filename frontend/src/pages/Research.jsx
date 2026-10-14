import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { MagnifyingGlass, WarningCircle } from "@phosphor-icons/react";
import { api, getToken, setToken } from "../api.js";
import ReportView, { ReportSkeleton } from "../components/ReportView.jsx";

export default function Research() {
  const [ticker, setTicker] = useState("NVDA");
  const [mode, setMode] = useState("offline");
  const [useLlm, setUseLlm] = useState(false);
  const [health, setHealth] = useState(null);
  const [token, setTok] = useState(getToken());
  const [state, setState] = useState({ phase: "idle" });

  useEffect(() => {
    api.health().then(setHealth).catch(() => setHealth({ down: true }));
  }, []);

  async function run(e) {
    e.preventDefault();
    setToken(token);
    setState({ phase: "loading" });
    try {
      const report = await api.research({ ticker, mode, use_llm: useLlm });
      setState({ phase: "done", report });
    } catch (err) {
      setState({ phase: "error", message: err.message });
    }
  }

  const samples = health?.offline_tickers || ["AAPL", "NVDA", "TSLA"];
  const input = "min-h-11 w-full rounded-lg border border-line bg-white px-3 text-base outline-none focus:border-accent";

  return (
    <div className="mx-auto max-w-7xl px-4 py-12 md:px-8">
      <div className="grid gap-12 lg:grid-cols-[20rem_1fr]">
        <form onSubmit={run} className="h-fit space-y-6 lg:sticky lg:top-24" aria-label="Research request">
          <div>
            <h1 className="text-3xl font-semibold tracking-tighter">Run a brief</h1>
            <p className="mt-2 text-sm text-steel">Pick a ticker and a data source.</p>
          </div>

          <div className="flex flex-col gap-2">
            <label htmlFor="ticker" className="text-sm font-medium">Ticker</label>
            <input id="ticker" className={`${input} font-mono uppercase`} value={ticker} maxLength={10} onChange={(e) => setTicker(e.target.value)} autoComplete="off" spellCheck="false" />
            <p className="text-xs text-steel">Offline samples: {samples.join(", ")}.</p>
          </div>

          <fieldset className="flex flex-col gap-2">
            <legend className="mb-2 text-sm font-medium">Data</legend>
            <div className="grid grid-cols-2 gap-1 rounded-lg bg-zinc-200/70 p-1">
              {[["offline", "Offline sample"], ["live", "Live market"]].map(([v, l]) => (
                <label key={v} className={`press grid min-h-11 cursor-pointer place-items-center rounded-md text-sm ${mode === v ? "bg-white font-medium shadow-sm" : "text-steel"}`}>
                  <input type="radio" name="mode" value={v} checked={mode === v} onChange={() => setMode(v)} className="sr-only" />{l}
                </label>
              ))}
            </div>
            <p className="text-xs text-steel">{mode === "live" ? "yfinance prices and fundamentals, Google News headlines. Takes about 10 seconds." : "Synthetic data, no network, instant."}</p>
          </fieldset>

          <label className="flex min-h-11 cursor-pointer items-start gap-3">
            <input type="checkbox" checked={useLlm} onChange={(e) => setUseLlm(e.target.checked)} className="mt-1 size-4 accent-emerald-600" />
            <span className="text-sm"><span className="font-medium">Write the brief with the LLM</span><span className="mt-0.5 block text-xs text-steel">Uses {health?.llm_provider || "the configured provider"}. A local 3B model can take a minute on CPU. Off means a rules-written brief.</span></span>
          </label>

          {health?.auth_required && (
            <div className="flex flex-col gap-2">
              <label htmlFor="tok" className="text-sm font-medium">API token</label>
              <input id="tok" type="password" className={input} value={token} onChange={(e) => setTok(e.target.value)} autoComplete="off" />
            </div>
          )}

          <button disabled={state.phase === "loading" || !ticker.trim()} className="press flex min-h-11 w-full items-center justify-center gap-2 rounded-lg bg-ink px-5 text-sm font-medium text-white hover:bg-zinc-700 disabled:opacity-50">
            <MagnifyingGlass size={16} weight="bold" /> {state.phase === "loading" ? "Running agents..." : "Run agents"}
          </button>
          {health?.down && <p className="flex items-start gap-2 text-sm text-sell"><WarningCircle size={18} className="mt-0.5 shrink-0" />Backend not reachable. Start it on port 8030.</p>}
        </form>

        <div aria-live="polite">
          {state.phase === "idle" && (
            <div className="grid min-h-80 place-content-center border border-dashed border-zinc-300 p-8 text-center">
              <p className="text-lg font-medium tracking-tight">No brief yet</p>
              <p className="mx-auto mt-2 max-w-[44ch] text-sm text-steel">Run NVDA on the offline sample to see all four agents and the charts in under a second. Earlier runs are in <Link className="underline" to="/reports">Reports</Link>.</p>
            </div>
          )}
          {state.phase === "loading" && <ReportSkeleton />}
          {state.phase === "error" && (
            <div role="alert" className="border-l-2 border-sell bg-rose-50 px-4 py-3 text-sm text-rose-900">
              <p className="font-medium">The run failed</p><p className="mt-1">{state.message}</p>
            </div>
          )}
          {state.phase === "done" && <ReportView report={state.report} />}
        </div>
      </div>
    </div>
  );
}
