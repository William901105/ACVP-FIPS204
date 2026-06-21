import type { FailureDetail } from "../types";

interface Props {
  failures: FailureDetail[];
  onSelectCase: (tgId: number | string, tcId: number | string) => void;
}

export default function FailureList({ failures, onSelectCase }: Props) {
  return (
    <section className="panel">
      <div className="panel-header">
        <h2>Failure Details</h2>
        <span className="count-pill">{failures.length}</span>
      </div>

      {failures.length ? (
        <div className="table-wrap failures">
          <table>
            <thead>
              <tr>
                <th>tgId</th>
                <th>tcId</th>
                <th>field</th>
                <th>reason</th>
                <th>expected</th>
                <th>provided</th>
              </tr>
            </thead>
            <tbody>
              {failures.map((failure, index) => (
                <tr key={`${failure.tgId}:${failure.tcId}:${failure.field}:${index}`} onClick={() => onSelectCase(failure.tgId, failure.tcId)}>
                  <td>{failure.tgId}</td>
                  <td>{failure.tcId}</td>
                  <td>{failure.field}</td>
                  <td>{failure.reason}</td>
                  <td className="truncate">{String(failure.expected ?? "")}</td>
                  <td className="truncate">{String(failure.provided ?? "")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="empty-state">No failures.</p>
      )}
    </section>
  );
}

