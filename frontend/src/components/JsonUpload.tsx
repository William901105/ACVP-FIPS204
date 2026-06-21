import { useState } from "react";
import { importBundle } from "../api";
import type { ImportSummary, JsonValue } from "../types";

interface Props {
  onImported: (summary: ImportSummary) => void;
}

type SlotName = "prompt" | "expectedResults" | "response";

export default function JsonUpload({ onImported }: Props) {
  const [files, setFiles] = useState<Partial<Record<SlotName, JsonValue>>>({});
  const [fileNames, setFileNames] = useState<Partial<Record<SlotName, string>>>({});
  const [error, setError] = useState("");

  async function readFile(slot: SlotName, file: File | null) {
    setError("");
    if (!file) {
      return;
    }
    try {
      const text = await file.text();
      setFiles((current) => ({ ...current, [slot]: JSON.parse(text) as JsonValue }));
      setFileNames((current) => ({ ...current, [slot]: file.name }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Invalid JSON");
    }
  }

  async function submit() {
    setError("");
    if (!files.prompt || !files.expectedResults || !files.response) {
      setError("prompt, expectedResults, and response are required");
      return;
    }
    try {
      const summary = await importBundle(files.prompt, files.expectedResults, files.response, "uploaded-bundle");
      onImported(summary);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Import failed");
    }
  }

  return (
    <section className="panel">
      <div className="panel-header">
        <h2>JSON Upload</h2>
      </div>

      <FileInput label="prompt.json" fileName={fileNames.prompt} onChange={(file) => readFile("prompt", file)} />
      <FileInput
        label="expectedResults.json"
        fileName={fileNames.expectedResults}
        onChange={(file) => readFile("expectedResults", file)}
      />
      <FileInput label="response.json" fileName={fileNames.response} onChange={(file) => readFile("response", file)} />

      {error ? <p className="form-error">{error}</p> : null}
      <button type="button" className="wide-button" onClick={submit}>
        Import
      </button>
    </section>
  );
}

function FileInput({
  label,
  fileName,
  onChange
}: {
  label: string;
  fileName?: string;
  onChange: (file: File | null) => void;
}) {
  return (
    <label className="file-row">
      <span>{label}</span>
      <input type="file" accept="application/json,.json" onChange={(event) => onChange(event.target.files?.[0] ?? null)} />
      <small>{fileName ?? "No file selected"}</small>
    </label>
  );
}

