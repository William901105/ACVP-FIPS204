import type { ImportDetail } from "../types";

interface Props {
  detail: ImportDetail | null;
}

export default function VectorSetViewer({ detail }: Props) {
  const vector = detail?.prompt;
  return (
    <section className="panel hero-panel">
      <div className="panel-header">
        <h2>Vector Set Viewer</h2>
      </div>
      {vector ? (
        <>
          <dl className="metadata-list horizontal">
            <div>
              <dt>vsId</dt>
              <dd>{vector.vsId}</dd>
            </div>
            <div>
              <dt>algorithm</dt>
              <dd>{vector.algorithm}</dd>
            </div>
            <div>
              <dt>mode</dt>
              <dd>{vector.mode}</dd>
            </div>
            <div>
              <dt>revision</dt>
              <dd>{vector.revision}</dd>
            </div>
          </dl>
          <div className="group-strip">
            {vector.testGroups.map((group) => (
              <span key={String(group.tgId)}>
                tgId {group.tgId} / {group.testType ?? "n/a"} / {group.parameterSet ?? "n/a"} / {group.tests.length} tests
              </span>
            ))}
          </div>
        </>
      ) : (
        <p className="empty-state">No vector set loaded.</p>
      )}
    </section>
  );
}

