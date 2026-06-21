import type { ValidationResult } from "../types";

interface Props {
  validation: ValidationResult | null;
}

export default function ValidationSummary({ validation }: Props) {
  if (!validation) {
    return (
      <section className="panel">
        <div className="panel-header">
          <h2>Validation Summary</h2>
        </div>
        <p className="empty-state">No validation result.</p>
      </section>
    );
  }

  const rows = [
    ["total", validation.summary.total],
    ["passed", validation.summary.passed],
    ["failed", validation.summary.failed],
    ["missing", validation.summary.missing],
    ["malformed", validation.summary.malformed]
  ] as const;

  return (
    <section className="panel">
      <div className="panel-header">
        <h2>Validation Summary</h2>
      </div>
      <div className="metric-grid wide">
        {rows.map(([label, value]) => (
          <div className="metric" key={label}>
            <span>{label}</span>
            <strong>{value}</strong>
          </div>
        ))}
      </div>
    </section>
  );
}

