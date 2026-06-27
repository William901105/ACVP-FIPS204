import { useEffect, useMemo, useState } from "react";
import {
  createAcvpSession,
  getAcvpExpectedResults,
  getAcvpSession,
  getAcvpSessionResults,
  getAcvpSessionVectorSets,
  getAcvpVectorSet,
  listAcvpSessions,
  submitAcvpVectorSetResults
} from "./api";
import JsonViewer from "./components/JsonViewer";
import { FIPS_REGISTRY, getFipsConfig } from "./registry";
import type {
  AcvpExpectedResults,
  AcvpSessionDetail,
  AcvpSessionResults,
  AcvpSessionSummary,
  AcvpVectorSetDownload,
  AcvpVectorSetResult,
  AcvpVectorSetSummary,
  CapabilityMode,
  FipsVersionConfig,
  FipsVersionId,
  JsonObject,
  JsonValue,
  Report
} from "./types";

const DEFAULT_TESTS_PER_GROUP = 1;
const DEFAULT_CAMPAIGN_SEED = "00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF";

type IutResponseStatus = "waiting" | "loaded" | "ready" | "error";

export default function App() {
  const [fipsId, setFipsId] = useState<FipsVersionId>("FIPS204");
  const config = useMemo(() => getFipsConfig(fipsId), [fipsId]);
  const [selectedModes, setSelectedModes] = useState<CapabilityMode[]>(["keyGen"]);
  const [selectedParameterSets, setSelectedParameterSets] = useState<string[]>(["ML-DSA-44"]);
  const [campaignSeed, setCampaignSeed] = useState(DEFAULT_CAMPAIGN_SEED);
  const [testsPerGroup, setTestsPerGroup] = useState(DEFAULT_TESTS_PER_GROUP);
  const [label, setLabel] = useState("local ML-DSA registration");
  const [sessions, setSessions] = useState<AcvpSessionSummary[]>([]);
  const [activeSession, setActiveSession] = useState<AcvpSessionDetail | null>(null);
  const [vectorSets, setVectorSets] = useState<AcvpVectorSetSummary[]>([]);
  const [activeVectorSetId, setActiveVectorSetId] = useState<string | null>(null);
  const [activeVectorSet, setActiveVectorSet] = useState<AcvpVectorSetDownload | null>(null);
  const [expectedResults, setExpectedResults] = useState<AcvpExpectedResults | null>(null);
  const [uploadedResponse, setUploadedResponse] = useState<JsonValue | null>(null);
  const [uploadedResponseName, setUploadedResponseName] = useState("");
  const [iutResponseStatus, setIutResponseStatus] = useState<IutResponseStatus>("waiting");
  const [iutResponseErrorDetail, setIutResponseErrorDetail] = useState("");
  const [promptImportName, setPromptImportName] = useState("");
  const [vectorResult, setVectorResult] = useState<AcvpVectorSetResult | null>(null);
  const [sessionResults, setSessionResults] = useState<AcvpSessionResults | null>(null);
  const [message, setMessage] = useState("");
  const [isBusy, setIsBusy] = useState(false);

  const isEnabled = config.enabled;
  const activeVectorSummary = vectorSets.find((item) => item.vectorSetId === activeVectorSetId) ?? null;
  const activeReport = vectorResult?.report ?? null;
  const canUploadResponse = Boolean(activeSession && activeVectorSetId) && !isBusy;
  const campaignSeedValidation = useMemo(() => validateCampaignSeed(campaignSeed), [campaignSeed]);
  const campaignSeedInvalid = isEnabled && !campaignSeedValidation.valid;
  const iutResponseLabel = responseStatusLabel(iutResponseStatus);
  const canValidateResponse = Boolean(activeVectorSetId && uploadedResponse != null && iutResponseStatus === "ready") && !isBusy;

  useEffect(() => {
    setSelectedModes(config.modes.filter((mode) => mode.enabled).slice(0, 1).map((mode) => mode.id));
    setSelectedParameterSets(config.defaultParameterSets);
    clearWorkspace();
    if (config.enabled) {
      refreshSessions().catch((error: Error) => setMessage(error.message));
    } else {
      setSessions([]);
    }
  }, [config.id]);

  async function refreshSessions() {
    if (!config.enabled) {
      return;
    }
    setSessions(await listAcvpSessions());
  }

  async function createRegistrationSession() {
    if (!isEnabled) {
      return;
    }
    if (selectedModes.length === 0 || selectedParameterSets.length === 0) {
      setMessage("Select at least one mode and one parameter set.");
      return;
    }
    if (!campaignSeedValidation.valid) {
      setMessage(campaignSeedValidation.message);
      return;
    }
    await runBusy(async () => {
      const payload = {
        algorithms: buildRegistrationAlgorithms(config, selectedModes, selectedParameterSets),
        label,
        campaignSeed: campaignSeed.trim() || undefined,
        testsPerGroup,
        autoGenerateVectorSets: true
      };
      const created = await createAcvpSession(payload as JsonValue);
      await refreshSessions();
      await activateSession(created.testSessionId);
      setMessage("Capability registration accepted.");
    });
  }

  async function importPrompt(file: File | null) {
    if (!file || !isEnabled) {
      return;
    }
    await runBusy(async () => {
      const prompt = await readJsonFile(file);
      const created = await createAcvpSession({
        prompt,
        label: `prompt:${file.name}`,
        autoGenerateExpectedResults: true
      } as JsonValue);
      setPromptImportName(file.name);
      await refreshSessions();
      await activateSession(created.testSessionId);
      setMessage("Prompt imported.");
    });
  }

  async function activateSession(sessionId: string) {
    await runBusy(async () => {
      const detail = await getAcvpSession(sessionId);
      const vectors = await getAcvpSessionVectorSets(sessionId);
      setActiveSession(detail);
      setVectorSets(vectors);
      setSessionResults(null);
      setVectorResult(null);
      setUploadedResponse(null);
      setUploadedResponseName("");
      setIutResponseStatus("waiting");
      setIutResponseErrorDetail("");
      const firstVectorId = vectors[0]?.vectorSetId ?? null;
      setActiveVectorSetId(firstVectorId);
      if (firstVectorId) {
        await loadVectorSet(firstVectorId, detail.testSessionId);
      } else {
        setActiveVectorSet(null);
        setExpectedResults(null);
      }
    });
  }

  async function activateVectorSet(vectorSetId: string) {
    await runBusy(async () => {
      await loadVectorSet(vectorSetId, activeSession?.testSessionId);
    });
  }

  async function loadVectorSet(vectorSetId: string, sessionId?: string) {
    const vector = await getAcvpVectorSet(vectorSetId);
    const expected = await getAcvpExpectedResults(vectorSetId);
    setActiveVectorSetId(vectorSetId);
    setActiveVectorSet(vector);
    setExpectedResults(expected);
    setVectorResult(null);
    setUploadedResponse(null);
    setUploadedResponseName("");
    setIutResponseStatus("waiting");
    setIutResponseErrorDetail("");
    if (sessionId) {
      setVectorSets(await getAcvpSessionVectorSets(sessionId));
    }
  }

  async function loadResponseFile(file: File | null) {
    if (!file) {
      return;
    }
    try {
      setUploadedResponse(await readJsonFile(file));
      setUploadedResponseName(file.name);
      setIutResponseStatus("ready");
      setIutResponseErrorDetail("");
      setVectorResult(null);
      setSessionResults(null);
      setMessage("");
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Invalid response JSON.";
      setIutResponseStatus("error");
      setIutResponseErrorDetail(errorMessage);
      setMessage(errorMessage);
    }
  }

  async function submitResponse() {
    if (!activeVectorSetId || uploadedResponse == null) {
      setMessage("Select a vector set and upload a response JSON.");
      return;
    }
    await runBusy(async () => {
      setIutResponseStatus("loaded");
      setIutResponseErrorDetail("");
      const result = await submitAcvpVectorSetResults(activeVectorSetId, uploadedResponse);
      setVectorResult(result);
      setIutResponseStatus("ready");
      setIutResponseErrorDetail("");
      if (activeSession) {
        setActiveSession(await getAcvpSession(activeSession.testSessionId));
        setVectorSets(await getAcvpSessionVectorSets(activeSession.testSessionId));
        setSessionResults(await getAcvpSessionResults(activeSession.testSessionId));
      }
      setMessage("Response validated.");
    }, (errorMessage) => {
      setIutResponseStatus("error");
      setIutResponseErrorDetail(errorMessage);
    });
  }

  function clearWorkspace() {
    setActiveSession(null);
    setVectorSets([]);
    setActiveVectorSetId(null);
    setActiveVectorSet(null);
    setExpectedResults(null);
    setUploadedResponse(null);
    setUploadedResponseName("");
    setIutResponseStatus("waiting");
    setIutResponseErrorDetail("");
    setPromptImportName("");
    setVectorResult(null);
    setSessionResults(null);
    setMessage("");
  }

  async function runBusy(work: () => Promise<void>, onError?: (message: string) => void) {
    setIsBusy(true);
    setMessage("");
    try {
      await work();
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Operation failed.";
      setMessage(errorMessage);
      onError?.(errorMessage);
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">ACVP local client</p>
          <h1>Capability, vector set, response, report</h1>
        </div>
        <div className="actions">
          <button type="button" onClick={refreshSessions} disabled={!isEnabled || isBusy}>
            Refresh
          </button>
          <button type="button" className="secondary" onClick={clearWorkspace} disabled={isBusy}>
            Clear
          </button>
        </div>
      </header>

      {message ? <div className="notice">{message}</div> : null}

      <section className="workflow-grid">
        <section className="panel stack">
          <div className="panel-header">
            <h2>Registry</h2>
            <span className={`state-chip ${isEnabled ? "ready" : "pending"}`}>{config.status}</span>
          </div>
          <label className="field">
            <span>FIPS version</span>
            <select value={fipsId} onChange={(event) => setFipsId(event.target.value as FipsVersionId)}>
              {FIPS_REGISTRY.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>
          {!isEnabled ? <div className="development-banner">開發中</div> : null}

          <CapabilityControls
            config={config}
            selectedModes={selectedModes}
            selectedParameterSets={selectedParameterSets}
            disabled={!isEnabled || isBusy}
            onToggleMode={(mode) => setSelectedModes((current) => toggleValue(current, mode))}
            onToggleParameterSet={(parameterSet) => setSelectedParameterSets((current) => toggleValue(current, parameterSet))}
          />

          <label className="field">
            <span>Label</span>
            <input value={label} onChange={(event) => setLabel(event.target.value)} disabled={!isEnabled || isBusy} />
          </label>
          <label className={`field ${campaignSeedInvalid ? "invalid" : ""}`}>
            <span>Campaign seed</span>
            <input
              value={campaignSeed}
              onChange={(event) => setCampaignSeed(event.target.value)}
              disabled={!isEnabled || isBusy}
              aria-invalid={campaignSeedInvalid}
              aria-describedby="campaign-seed-hint"
            />
            <small id="campaign-seed-hint" className={campaignSeedInvalid ? "field-error" : "field-hint"}>
              {campaignSeedValidation.message}
            </small>
          </label>
          <label className="field short">
            <span>Tests per group</span>
            <input
              type="number"
              min={1}
              max={10}
              value={testsPerGroup}
              onChange={(event) => setTestsPerGroup(Number(event.target.value))}
              disabled={!isEnabled || isBusy}
            />
          </label>
          <button type="button" onClick={createRegistrationSession} disabled={!isEnabled || isBusy || campaignSeedInvalid}>
            Register capabilities
          </button>
          <label className="file-button">
            <span>Import prompt JSON</span>
            <input
              type="file"
              accept="application/json,.json"
              disabled={!isEnabled || isBusy}
              onChange={(event) => {
                const file = event.currentTarget.files?.[0] ?? null;
                void importPrompt(file);
                event.currentTarget.value = "";
              }}
            />
          </label>
          {promptImportName ? <p className="subtle">{promptImportName}</p> : null}
        </section>

        <section className="panel stack">
          <div className="panel-header">
            <h2>Test Sessions</h2>
            <span className="count-pill">{sessions.length}</span>
          </div>
          <div className="session-list">
            {sessions.map((session) => (
              <button
                type="button"
                key={session.testSessionId}
                className={`session-row ${session.testSessionId === activeSession?.testSessionId ? "active-row" : ""}`}
                onClick={() => activateSession(session.testSessionId)}
                disabled={!isEnabled || isBusy}
              >
                <span>{session.label ?? session.testSessionId}</span>
                <strong>{session.status}</strong>
                <small>{session.vectorSetCount} vector sets</small>
              </button>
            ))}
            {sessions.length === 0 ? <p className="empty-state">No sessions.</p> : null}
          </div>
        </section>

        <section className="panel stack wide-panel">
          <div className="panel-header">
            <h2>Vector Sets</h2>
            <span className="count-pill">{vectorSets.length}</span>
          </div>
          <div className="vector-toolbar">
            {vectorSets.map((vector) => (
              <button
                type="button"
                key={vector.vectorSetId}
                className={vector.vectorSetId === activeVectorSetId ? "active" : "secondary"}
                onClick={() => activateVectorSet(vector.vectorSetId)}
                disabled={!isEnabled || isBusy}
              >
                {vector.mode ?? "vector"} / {vector.status}
              </button>
            ))}
          </div>
          <MetadataGrid session={activeSession} vector={activeVectorSummary} />
          <div className="actions">
            <button
              type="button"
              onClick={() => activeVectorSet && downloadJson(`prompt-${activeVectorSet.vectorSetId}.json`, activeVectorSet.prompt)}
              disabled={!activeVectorSet}
            >
              Download prompt
            </button>
            <button
              type="button"
              className="secondary"
              onClick={() => expectedResults && downloadJson(`expectedResults-${expectedResults.vectorSetId}.json`, expectedResults.expectedResults)}
              disabled={!expectedResults}
            >
              Download expected
            </button>
          </div>
          <JsonPane title="Prompt" value={activeVectorSet?.prompt ?? null} />
        </section>

        <section className="panel stack">
          <div className="panel-header">
            <h2>IUT Response</h2>
            <span className={`state-chip ${iutResponseStatus}`} title={iutResponseErrorDetail}>
              {iutResponseLabel}
            </span>
          </div>
          <label
            className={`file-button ${canUploadResponse ? "" : "disabled"}`}
            aria-disabled={!canUploadResponse}
          >
            <span>Upload response JSON</span>
            <input
              type="file"
              accept="application/json,.json"
              disabled={!canUploadResponse}
              onChange={(event) => {
                const file = event.currentTarget.files?.[0] ?? null;
                void loadResponseFile(file);
                event.currentTarget.value = "";
              }}
            />
          </label>

          {!activeSession ? (
            <p className="subtle">Select a Test Session before uploading a response JSON.</p>
          ) : !activeVectorSetId ? (
            <p className="subtle">Select a Vector Set before uploading a response JSON.</p>
          ) : null}
          {uploadedResponseName ? <p className="subtle">{uploadedResponseName}</p> : null}
          {iutResponseStatus === "error" && iutResponseErrorDetail ? (
            <p className="response-error-detail">{iutResponseErrorDetail}</p>
          ) : null}
          <button type="button" onClick={submitResponse} disabled={!canValidateResponse}>
            Validate response
          </button>
          <JsonPane title="Response" value={uploadedResponse} />
        </section>

        <section className="panel stack wide-panel">
          <div className="panel-header">
            <h2>Validation Report</h2>
            <span className={`state-chip ${vectorResult?.status === "validated" ? "ready" : "pending"}`}>{vectorResult?.status ?? "not submitted"}</span>
          </div>
          <SummaryStrip result={vectorResult} sessionResults={sessionResults} />
          <div className="actions">
            <button type="button" onClick={() => activeReport && downloadJson(`report-${activeReport.importId}.json`, activeReport)} disabled={!activeReport}>
              Export JSON
            </button>
            <button type="button" className="secondary" onClick={() => activeReport && downloadText(`report-${activeReport.importId}.md`, activeReport.markdown)} disabled={!activeReport}>
              Export markdown
            </button>
          </div>
          <ReportPane report={activeReport} />
        </section>
      </section>
    </main>
  );
}

function CapabilityControls({
  config,
  selectedModes,
  selectedParameterSets,
  disabled,
  onToggleMode,
  onToggleParameterSet
}: {
  config: FipsVersionConfig;
  selectedModes: CapabilityMode[];
  selectedParameterSets: string[];
  disabled: boolean;
  onToggleMode: (mode: CapabilityMode) => void;
  onToggleParameterSet: (parameterSet: string) => void;
}) {
  return (
    <>
      <div className="control-group">
        <span>Modes</span>
        <div className="segmented">
          {config.modes.map((mode) => (
            <button
              type="button"
              key={mode.id}
              className={selectedModes.includes(mode.id) ? "active" : "secondary"}
              onClick={() => onToggleMode(mode.id)}
              disabled={disabled || !mode.enabled}
            >
              {mode.label}
            </button>
          ))}
        </div>
      </div>
      <div className="control-group">
        <span>Parameter sets</span>
        <div className="segmented">
          {config.parameterSets.map((parameterSet) => (
            <button
              type="button"
              key={parameterSet}
              className={selectedParameterSets.includes(parameterSet) ? "active" : "secondary"}
              onClick={() => onToggleParameterSet(parameterSet)}
              disabled={disabled}
            >
              {parameterSet}
            </button>
          ))}
        </div>
      </div>
    </>
  );
}

function MetadataGrid({ session, vector }: { session: AcvpSessionDetail | null; vector: AcvpVectorSetSummary | null }) {
  return (
    <dl className="metadata-grid">
      <div>
        <dt>session</dt>
        <dd>{session?.status ?? "none"}</dd>
      </div>
      <div>
        <dt>vector</dt>
        <dd>{vector?.status ?? "none"}</dd>
      </div>
      <div>
        <dt>mode</dt>
        <dd>{vector?.mode ?? session?.mode ?? "n/a"}</dd>
      </div>
      <div>
        <dt>cases</dt>
        <dd>{vector?.testCaseCount ?? session?.testCaseCount ?? 0}</dd>
      </div>
    </dl>
  );
}

function SummaryStrip({ result, sessionResults }: { result: AcvpVectorSetResult | null; sessionResults: AcvpSessionResults | null }) {
  const summary = result?.validationResult.summary;
  return (
    <div className="summary-strip">
      <Metric label="passed" value={summary?.passed ?? 0} tone="pass" />
      <Metric label="failed" value={summary?.failed ?? 0} tone="fail" />
      <Metric label="missing" value={summary?.missing ?? 0} tone="warn" />
      <Metric label="malformed" value={summary?.malformed ?? 0} tone="info" />
      <Metric label="session pending" value={Number(sessionResults?.summary?.pendingVectorSets ?? 0)} tone="neutral" />
    </div>
  );
}

function Metric({ label, value, tone }: { label: string; value: number; tone: string }) {
  return (
    <div className={`metric ${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function JsonPane({ title, value }: { title: string; value: unknown }) {
  return (
    <div className="json-pane">
      <h3>{title}</h3>
      {value ? <JsonViewer value={value} /> : <p className="empty-state">No JSON.</p>}
    </div>
  );
}

function ReportPane({ report }: { report: Report | null }) {
  if (!report) {
    return <p className="empty-state">No report.</p>;
  }
  return <pre className="markdown-preview">{report.markdown}</pre>;
}

function responseStatusLabel(status: IutResponseStatus): string {
  if (status === "ready") {
    return "ready";
  }
  if (status === "error") {
    return "error: Wrong response format!";
  }
  return status;
}

function validateCampaignSeed(value: string): { valid: boolean; message: string } {
  if (!value) {
    return {
      valid: true,
      message: "Leave empty to use the deterministic fallback seed, or enter 32-128 hex characters."
    };
  }
  if (/\s/.test(value)) {
    return {
      valid: false,
      message: "Campaign seed must not contain whitespace."
    };
  }
  if (!/^[0-9a-fA-F]+$/.test(value)) {
    return {
      valid: false,
      message: "Campaign seed must contain only hexadecimal characters."
    };
  }
  if (value.length % 2 !== 0) {
    return {
      valid: false,
      message: "Campaign seed must be an even-length hex string."
    };
  }
  if (value.length < 32 || value.length > 128) {
    return {
      valid: false,
      message: "Campaign seed must be between 32 and 128 hex characters."
    };
  }
  return {
    valid: true,
    message: "Valid seed. Use 32-128 hex characters."
  };
}

function buildRegistrationAlgorithms(config: FipsVersionConfig, modes: CapabilityMode[], parameterSets: string[]): JsonObject[] {
  return modes.map((mode) => {
    if (mode === "keyGen") {
      return {
        algorithm: config.algorithm,
        mode,
        revision: config.revision,
        prereqVals: [{ algorithm: "SHA", valValue: "same" }],
        parameterSets
      };
    }
    const registration: JsonObject = {
      algorithm: config.algorithm,
      mode,
      revision: config.revision,
      prereqVals: [{ algorithm: "SHA", valValue: "same" }],
      signatureInterfaces: ["internal", "external"],
      externalMu: [false, true],
      preHash: ["pure", "preHash"],
      capabilities: [
        {
          parameterSets,
          messageLength: [{ min: 8, max: 128, increment: 8 }],
          contextLength: [{ min: 0, max: 64, increment: 8 }],
          hashAlgs: config.defaultHashAlgs ?? ["SHA2-256"]
        }
      ]
    };
    if (mode === "sigGen") {
      registration.deterministic = [true, false];
    }
    return registration;
  });
}

function toggleValue<T>(values: T[], value: T): T[] {
  return values.includes(value) ? values.filter((item) => item !== value) : [...values, value];
}

async function readJsonFile(file: File): Promise<JsonValue> {
  return JSON.parse(await file.text()) as JsonValue;
}

function downloadJson(fileName: string, value: unknown) {
  downloadText(fileName, JSON.stringify(value, null, 2));
}

function downloadText(fileName: string, value: string) {
  const blob = new Blob([value], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = fileName;
  link.click();
  URL.revokeObjectURL(url);
}
