import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft } from "@phosphor-icons/react";
import { api } from "../api.js";
import ReportView, { ReportSkeleton } from "../components/ReportView.jsx";

export default function ReportDetail() {
  const { id } = useParams();
  const [report, setReport] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    setReport(null);
    setError("");
    api.report(id).then(setReport).catch((e) => setError(e.message));
  }, [id]);

  return (
    <div className="mx-auto max-w-7xl px-4 py-12 md:px-8">
      <Link to="/reports" className="mb-8 inline-flex min-h-11 items-center gap-2 text-sm text-steel hover:text-ink"><ArrowLeft size={16} /> All reports</Link>
      {error && <p role="alert" className="border-l-2 border-sell bg-rose-50 px-4 py-3 text-sm text-rose-900">{error}</p>}
      {!report && !error && <ReportSkeleton />}
      {report && <ReportView report={report} />}
    </div>
  );
}
