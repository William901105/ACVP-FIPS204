import type { CaseStatus, ImportDetail, ValidationResult } from "../types";

interface Props {
  detail: ImportDetail | null;
  validation: ValidationResult | null;
  selectedGroupId: number | string | null;
  selectedTcId: number | string | null;
  onSelectGroup: (tgId: number | string) => void;
  onSelectCase: (tcId: number | string) => void;
}

export default function TestGroupTable({
  detail,
  validation,
  selectedGroupId,
  selectedTcId,
  onSelectGroup,
  onSelectCase
}: Props) {
  const groups = detail?.prompt.testGroups ?? [];
  const selectedGroup = groups.find((group) => String(group.tgId) === String(selectedGroupId)) ?? groups[0];
  const resultIndex = new Map(
    (validation?.caseResults ?? []).map((item) => [`${item.tgId}:${item.tcId}`, item.status] as const)
  );

  return (
    <section className="panel">
      <div className="panel-header">
        <h2>Test Groups</h2>
      </div>

      {groups.length ? (
        <>
          <div className="group-tabs">
            {groups.map((group) => (
              <button
                type="button"
                key={String(group.tgId)}
                className={String(group.tgId) === String(selectedGroup?.tgId) ? "active" : "secondary"}
                onClick={() => onSelectGroup(group.tgId)}
              >
                tgId {group.tgId}
              </button>
            ))}
          </div>

          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>tcId</th>
                  <th>testType</th>
                  <th>parameterSet</th>
                  <th>result</th>
                </tr>
              </thead>
              <tbody>
                {selectedGroup?.tests.map((test) => {
                  const status = resultIndex.get(`${selectedGroup.tgId}:${test.tcId}`);
                  return (
                    <tr
                      key={String(test.tcId)}
                      className={String(test.tcId) === String(selectedTcId) ? "selected-row" : ""}
                      onClick={() => onSelectCase(test.tcId)}
                    >
                      <td>{test.tcId}</td>
                      <td>{selectedGroup.testType ?? "n/a"}</td>
                      <td>{selectedGroup.parameterSet ?? "n/a"}</td>
                      <td>{status ? <StatusBadge status={status} /> : "not run"}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </>
      ) : (
        <p className="empty-state">No test groups.</p>
      )}
    </section>
  );
}

function StatusBadge({ status }: { status: CaseStatus }) {
  return <span className={`badge ${status}`}>{status}</span>;
}

