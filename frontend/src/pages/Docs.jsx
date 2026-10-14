const SECTIONS = [
  ["Scoring", [
    "Each agent returns a score from -1 to +1 built from small rule contributions. Every contribution is shown in the report when you expand an agent.",
    "The composite is a weighted mean: fundamentals 35%, sentiment 25%, price signals 40%. If an agent is degraded its weight is dropped and the rest are renormalised.",
    "Risk is the mean of four 0 to 1 inputs: annualised volatility (60% = 1), max drawdown (50% = 1), beta and debt to equity. Bullish scores shrink by up to 40% at maximum risk. Bearish scores are not softened.",
    "Rating: Buy at +0.25 or above after the haircut, Sell at -0.25 or below, otherwise Hold.",
  ]],
  ["Where the LLM sits", [
    "The model receives the finished scores and one-line summaries, and writes four to six sentences. It never computes or chooses a number. If it fails or returns something too short, the rules-based brief is used and the reason is shown.",
    "Provider is set with LLM_PROVIDER: ollama (default, local and free), openai or anthropic.",
  ]],
  ["Data sources", [
    "Live mode: yfinance for one year of daily bars and fundamentals, Google News RSS for headlines. Set NEWSAPI_KEY to prefer NewsAPI. Set ALPHAVANTAGE_API_KEY to fill missing fundamentals.",
    "Offline mode: synthetic fixtures for AAPL, NVDA and TSLA. They are seeded random walks with invented fundamentals and headlines. Reports built on them carry a warning banner.",
    "TA-Lib is replaced by pandas implementations of RSI (Wilder), MACD, SMA, Bollinger Bands and ATR, so nothing needs a C toolchain.",
  ]],
  ["Limits", [
    "Sentiment is a keyword lexicon. It reads headlines, not articles, and many real headlines score neutral.",
    "Free data is delayed and yfinance can rate-limit or return gaps. The report degrades instead of failing.",
    "The weights and thresholds are reasoned defaults, not fitted or backtested. This is a research aid, not advice.",
  ]],
];

export default function Docs() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-12 md:px-8">
      <h1 className="text-3xl font-semibold tracking-tighter md:text-4xl">Method</h1>
      <p className="mt-3 max-w-[60ch] text-steel">How a brief is built, what the model is allowed to do, and where it is weak.</p>
      <div className="mt-12 divide-y divide-line border-t border-line">
        {SECTIONS.map(([title, paras]) => (
          <section key={title} className="grid gap-4 py-10 lg:grid-cols-[14rem_1fr] lg:gap-12">
            <h2 className="text-xl font-semibold tracking-tight">{title}</h2>
            <div className="max-w-[68ch] space-y-4 leading-relaxed text-steel">{paras.map((p) => <p key={p}>{p}</p>)}</div>
          </section>
        ))}
      </div>
    </div>
  );
}
