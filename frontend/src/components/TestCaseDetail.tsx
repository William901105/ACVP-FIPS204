import type { CaseResult, ImportDetail } from "../types";
import JsonViewer from "./JsonViewer";

interface Props {
  detail: ImportDetail | null;
  selectedGroupId: number | string | null;
  selectedTcId: number | string | null;
  caseResult: CaseResult | null;
}

export default function TestCaseDetail({ detail, selectedGroupId, selectedTcId, caseResult }: Props) {
  const promptCase =
    detail?.prompt.testGroups
      .find((group) => String(group.tgId) === String(selectedGroupId))
      ?.tests.find((test) => String(test.tcId) === String(selectedTcId)) ?? null;

  return (
    <section className="panel">
      <div className="panel-header">
        <h2>Test Case Detail</h2>
        {caseResult ? <span className={`badge ${caseResult.status}`}>{caseResult.status}</span> : null}
      </div>

      {selectedTcId == null ? (
        <p className="empty-state">No test case selected.</p>
      ) : (
        <div className="case-grid">
          <JsonBlock title="Prompt Input" value={caseResult?.prompt ?? promptCase} />
          <JsonBlock title="Expected Output" value={caseResult?.expected ?? null} />
          <JsonBlock title="Response Output" value={caseResult?.response ?? null} />
          <JsonBlock title="Result Diff" value={caseResult?.failures ?? []} />
        </div>
      )}
    </section>
  );
}

function JsonBlock({ title, value }: { title: string; value: unknown }) {
  return (
    <div className="json-block">
      <h3>{title}</h3>
      <JsonViewer value={value} />
    </div>
  );
}

