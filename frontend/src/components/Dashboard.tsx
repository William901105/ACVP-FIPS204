import type { ImportSummary, SampleInfo, ValidationResult } from "../types";

interface Props {
  samples: SampleInfo[];
  activeSummary: ImportSummary | null;
  validation: ValidationResult | null;
  onLoadSample: (sampleName: string, responseVariant: "pass" | "fail") => void;
}

export default function Dashboard({ samples, activeSummary, validation, onLoadSample }: Props) {
  return (
    <section className="panel">
      <div className="panel-header">
        <h2>Dashboard</h2>
      </div>

      <div className="support-list">
        <span>ML-DSA keyGen FIPS204</span>
        <span>ML-DSA sigGen FIPS204</span>
        <span>ML-DSA sigVer FIPS204</span>
      </div>

      <div className="metric-grid">
        <Metric label="Samples" value={samples.length} />
        <Metric label="Groups" value={activeSummary?.testGroupCount ?? 0} />
        <Metric label="Cases" value={activeSummary?.testCaseCount ?? 0} />
      </div>

      {activeSummary ? (
        <dl className="metadata-list">
          <div>
            <dt>algorithm</dt>
            <dd>{activeSummary.algorithm}</dd>
          </div>
          <div>
            <dt>mode</dt>
            <dd>{activeSummary.mode}</dd>
          </div>
          <div>
            <dt>revision</dt>
            <dd>{activeSummary.revision}</dd>
          </div>
          <div>
            <dt>vsId</dt>
            <dd>{activeSummary.vsId}</dd>
          </div>
        </dl>
      ) : null}

      {validation ? (
        <div className="compact-summary">
          <span className="status-dot passed" />
          <span>{validation.summary.passed} passed</span>
          <span className="status-dot failed" />
          <span>{validation.summary.failed} failed</span>
          <span className="status-dot missing" />
          <span>{validation.summary.missing} missing</span>
          <span className="status-dot malformed" />
          <span>{validation.summary.malformed} malformed</span>
        </div>
      ) : null}

      <div className="sample-list">
        {samples.map((sample) => (
          <div className="sample-row" key={sample.name}>
            <div>
              <strong>{sample.name}</strong>
              <small>
                {sample.testGroupCount ?? 0} groups / {sample.testCaseCount ?? 0} cases
              </small>
            </div>
            <div className="button-row">
              <button type="button" onClick={() => onLoadSample(sample.name, "pass")} disabled={!sample.hasPassResponse}>
                Pass
              </button>
              <button type="button" className="secondary" onClick={() => onLoadSample(sample.name, "fail")} disabled={!sample.hasFailResponse}>
                Fail
              </button>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

