import { Link } from "react-router-dom";
import { Logo } from "./Nav.jsx";

export default function Footer() {
  return (
    <footer className="mt-24 border-t border-line">
      <div className="mx-auto grid max-w-7xl grid-cols-[minmax(0,1fr)] gap-8 px-4 py-12 md:grid-cols-[1.4fr_1fr] md:px-8">
        <div>
          <Logo />
          <p className="mt-4 max-w-[52ch] text-sm leading-relaxed text-steel">
            Educational research tool. Output is not financial advice. Offline mode runs on synthetic sample data, clearly labelled in every report.
          </p>
        </div>
        <nav className="flex flex-wrap content-start gap-x-6 gap-y-1 text-sm md:justify-end" aria-label="Footer">
          <Link className="flex min-h-11 items-center text-steel hover:text-ink" to="/research">Research</Link>
          <Link className="flex min-h-11 items-center text-steel hover:text-ink" to="/reports">Reports</Link>
          <Link className="flex min-h-11 items-center text-steel hover:text-ink" to="/docs">Method</Link>
        </nav>
      </div>
    </footer>
  );
}
