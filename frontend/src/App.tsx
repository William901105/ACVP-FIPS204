import { useEffect, useMemo, useState } from "react";
import { getImport, getReport, listSamples, loadSample, validateImport } from "./api";
import Dashboard from "./components/Dashboard";
import FailureList from "./components/FailureList";
import JsonUpload from "./components/JsonUpload";
import ReportViewer from "./components/ReportViewer";
import TestCaseDetail from "./components/TestCaseDetail";
import TestGroupTable from "./components/TestGroupTable";
import ValidationSummary from "./components/ValidationSummary";
import VectorSetViewer from "./components/VectorSetViewer";
import type { ImportDetail, ImportSummary, Report, SampleInfo, ValidationResult } from "./types";

export default function App() {
  const [samples, setSamples] = useState<SampleInfo[]>([]);
  const [activeSummary, setActiveSummary] = useState<ImportSummary | null>(null);
  const [detail, setDetail] = useState<ImportDetail | null>(null);
  const [validation, setValidation] = useState<ValidationResult | null>(null);
  const [report, setReport] = useState<Report | null>(null);
  const [selectedGroupId, setSelectedGroupId] = useState<number | string | null>(null);
  const [selectedTcId, setSelectedTcId] = useState<number | string | null>(null);
  const [message, setMessage] = useState<string>("");
  const [isBusy, setIsBusy] = useState(false);

  useEffect(() => {
    listSamples()
      .then(setSamples)
      .catch((error: Error) => setMessage(error.message));
  }, []);

  useEffect(() => {
    const firstGroup = detail?.prompt.testGroups?.[0];
    if (!firstGroup) {
      setSelectedGroupId(null);
      setSelectedTcId(null);
      return;
    }
    setSelectedGroupId(firstGroup.tgId);
    setSelectedTcId(firstGroup.tests?.[0]?.tcId ?? null);
  }, [detail?.importId]);

  const selectedCaseResult = useMemo(() => {
    if (!validation || selectedGroupId == null || selectedTcId == null) {
      return null;
    }
    return (
      validation.caseResults.find(
        (item) => String(item.tgId) === String(selectedGroupId) && String(item.tcId) === String(selectedTcId)
      ) ?? null
    );
  }, [selectedGroupId, selectedTcId, validation]);

  async function activateImport(summary: ImportSummary) {
    const importDetail = await getImport(summary.importId);
    setActiveSummary(summary);
    setDetail(importDetail);
    setValidation(importDetail.validationResult ?? null);
    setReport(null);
  }

  async function handleLoadSample(sampleName: string, responseVariant: "pass" | "fail") {
    await runBusy(async () => {
      const summary = await loadSample(sampleName, responseVariant);
      await activateImport(summary);
      setMessage(`Loaded ${sampleName} (${responseVariant})`);
    });
  }

  async function handleImported(summary: ImportSummary) {
    await runBusy(async () => {
      await activateImport(summary);
      setMessage("Imported JSON bundle");
    });
  }

  async function handleValidate() {
    if (!activeSummary) {
      setMessage("Load or import a bundle first");
      return;
    }
    await runBusy(async () => {
      const result = await validateImport(activeSummary.importId);
      const importDetail = await getImport(activeSummary.importId);
      setValidation(result);
      setDetail(importDetail);
      setReport(null);
      setMessage("Validation complete");
    });
  }

  async function handleBuildReport() {
    if (!activeSummary) {
      setMessage("Load or import a bundle first");
      return;
    }
    await runBusy(async () => {
      setReport(await getReport(activeSummary.importId));
      setMessage("Report ready");
    });
  }

  async function runBusy(work: () => Promise<void>) {
    setIsBusy(true);
    setMessage("");
    try {
      await work();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Operation failed");
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">FIPS 204 / ML-DSA</p>
          <h1>ACVP JSON Viewer + Local Validator</h1>
        </div>
        <div className="actions">
          <button type="button" onClick={handleValidate} disabled={!activeSummary || isBusy}>
            Validate
          </button>
          <button type="button" className="secondary" onClick={handleBuildReport} disabled={!activeSummary || isBusy}>
            Report
          </button>
        </div>
      </header>

      {message ? <div className="notice">{message}</div> : null}

      <section className="layout">
        <aside className="side-panel">
          <Dashboard samples={samples} activeSummary={activeSummary} validation={validation} onLoadSample={handleLoadSample} />
          <JsonUpload onImported={handleImported} />
        </aside>

        <section className="content-panel">
          <VectorSetViewer detail={detail} />
          <div className="split">
            <TestGroupTable
              detail={detail}
              validation={validation}
              selectedGroupId={selectedGroupId}
              selectedTcId={selectedTcId}
              onSelectGroup={setSelectedGroupId}
              onSelectCase={setSelectedTcId}
            />
            <TestCaseDetail detail={detail} selectedGroupId={selectedGroupId} selectedTcId={selectedTcId} caseResult={selectedCaseResult} />
          </div>
          <ValidationSummary validation={validation} />
          <FailureList failures={validation?.failures ?? []} onSelectCase={(tgId, tcId) => {
            setSelectedGroupId(tgId);
            setSelectedTcId(tcId);
          }} />
          <ReportViewer report={report} />
        </section>
      </section>
    </main>
  );
}

