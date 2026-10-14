import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api.js";
import { ratingTone } from "../components/ReportView.jsx";

export default function Reports() {
  const [rows, setRows] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.reports().then(setRows).catch((e) => setError(e.message));
  }, []);

  return (
    <div className="mx-auto max-w-7xl px-4 py-12 md:px-8">
      <h1 className="text-3xl font-semibold tracking-tighter">Reports</h1>
      <p className="mt-2 text-sm text-steel">Every run is saved to SQLite on the backend.</p>

      <div className="mt-10" aria-live="polite">
        {error && <p role="alert" className="border-l-2 border-sell bg-rose-50 px-4 py-3 text-sm text-rose-900">{error}</p>}
        {!rows && !error && <div className="space-y-3">{[0, 1, 2, 3].map((i) => <div key={i} className="skeleton h-12 w-full" />)}</div>}
        {rows?.length === 0 && (
          <div className="grid min-h-60 place-content-center border border-dashed border-zinc-300 p-8 text-center">
            <p className="text-lg font-medium tracking-tight">Nothing saved yet</p>
            <p className="mt-2 text-sm text-steel">Run your first brief on the <Link className="underline" to="/research">Research</Link> page.</p>
          </div>
        )}
        {rows?.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[34rem] text-left text-sm">
              <thead className="border-b border-line font-mono text-xs uppercase text-steel">
                <tr><th className="py-3 font-normal">Ticker</th><th className="font-normal">Rating</th><th className="text-right font-normal">Score</th><th className="font-normal pl-8">Data</th><th className="text-right font-normal">When (UTC)</th></tr>
              </thead>
              <tbody className="divide-y divide-line">
                {rows.map((r) => (
                  <tr key={r.id} className="hover:bg-zinc-100/70">
                    <td className="py-3"><Link to={`/reports/${r.id}`} className="font-mono font-medium underline-offset-4 hover:underline">{r.ticker}</Link></td>
                    <td className={`font-medium ${ratingTone(r.rating)}`}>{r.rating || "n/a"}</td>
                    <td className="text-right font-mono tabular-nums">{r.score == null ? "n/a" : `${r.score >= 0 ? "+" : ""}${r.score.toFixed(2)}`}</td>
                    <td className="pl-8 text-steel">{r.mode}</td>
                    <td className="text-right font-mono text-xs text-steel">{r.created_at.replace("T", " ").slice(0, 16)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
