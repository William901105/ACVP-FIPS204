import type { Report } from "../types";
import JsonViewer from "./JsonViewer";

interface Props {
  report: Report | null;
}

export default function ReportViewer({ report }: Props) {
  function download(filename: string, content: string, type: string) {
    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
  }

  return (
    <section className="panel">
      <div className="panel-header">
        <h2>Report Export</h2>
        {report ? (
          <div className="button-row">
            <button
              type="button"
              onClick={() => download(`report-${report.importId}.json`, JSON.stringify(report, null, 2), "application/json")}
            >
              JSON
            </button>
            <button type="button" className="secondary" onClick={() => download(`report-${report.importId}.md`, report.markdown, "text/markdown")}>
              Markdown
            </button>
          </div>
        ) : null}
      </div>
      {report ? (
        <div className="report-grid">
          <pre className="markdown-preview">{report.markdown}</pre>
          <JsonViewer value={report} />
        </div>
      ) : (
        <p className="empty-state">No report generated.</p>
      )}
    </section>
  );
}

