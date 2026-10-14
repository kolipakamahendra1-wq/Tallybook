import { useEffect, useRef } from "react";

const base = {
  margin: { l: 44, r: 12, t: 8, b: 28 },
  paper_bgcolor: "rgba(0,0,0,0)",
  plot_bgcolor: "rgba(0,0,0,0)",
  font: { family: "Geist Mono, monospace", size: 11, color: "#71717a" },
  xaxis: { gridcolor: "#e4e4e7", linecolor: "#e4e4e7", showspikes: false },
  yaxis: { gridcolor: "#e4e4e7", zeroline: false },
  legend: { orientation: "h", y: 1.12, x: 0 },
  hovermode: "x unified",
};

/** Plotly is loaded on demand so landing and docs pages do not pay for it. */
export default function Chart({ traces, layout = {}, height = 260, label }) {
  const ref = useRef(null);

  useEffect(() => {
    let plotly;
    let cancelled = false;
    const el = ref.current;
    import("plotly.js-basic-dist-min").then((mod) => {
      if (cancelled || !el) return;
      plotly = mod.default;
      plotly.react(el, traces, { ...base, ...layout, height }, { displayModeBar: false, responsive: true });
    });
    return () => {
      cancelled = true;
      if (plotly && el) plotly.purge(el);
    };
  }, [traces, layout, height]);

  return <div ref={ref} role="img" aria-label={label} style={{ minHeight: height }} />;
}
