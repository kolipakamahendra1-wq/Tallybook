import { useState } from "react";
import { Link, NavLink } from "react-router-dom";
import { ChartLineUp, List, X } from "@phosphor-icons/react";

const links = [
  ["/research", "Research"],
  ["/reports", "Reports"],
  ["/docs", "Method"],
];

export function Logo() {
  return (
    <Link to="/" className="flex items-center gap-2.5 font-semibold tracking-tight">
      <span className="grid size-7 place-items-center rounded-md bg-ink text-emerald-400">
        <ChartLineUp size={16} weight="bold" />
      </span>
      Tallybook
    </Link>
  );
}

export default function Nav() {
  const [open, setOpen] = useState(false);
  const cls = ({ isActive }) =>
    `rounded-md px-3 py-2 text-sm transition-colors ${isActive ? "bg-zinc-200/70 text-ink" : "text-steel hover:text-ink"}`;

  return (
    <header className="sticky top-0 z-40 border-b border-line bg-canvas/85 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4 md:px-8">
        <Logo />
        <nav className="hidden items-center gap-1 md:flex" aria-label="Main">
          {links.map(([to, label]) => (
            <NavLink key={to} to={to} className={cls}>{label}</NavLink>
          ))}
          <Link to="/research" className="press ml-3 rounded-md bg-ink px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700">
            Run a brief
          </Link>
        </nav>
        <button className="grid size-11 place-items-center md:hidden" aria-label={open ? "Close menu" : "Open menu"} aria-expanded={open} onClick={() => setOpen(!open)}>
          {open ? <X size={22} /> : <List size={22} />}
        </button>
      </div>
      {open && (
        <nav className="border-t border-line bg-canvas px-4 pb-4 md:hidden" aria-label="Mobile">
          {links.map(([to, label]) => (
            <NavLink key={to} to={to} className={cls} onClick={() => setOpen(false)}>
              <span className="flex min-h-11 items-center">{label}</span>
            </NavLink>
          ))}
        </nav>
      )}
    </header>
  );
}
