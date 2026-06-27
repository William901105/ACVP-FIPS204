import type {
  AcvpExpectedResults,
  AcvpSessionDetail,
  AcvpSessionResults,
  AcvpSessionSummary,
  AcvpVectorSetDownload,
  AcvpVectorSetSummary,
  AcvpVectorSetResult,
  ImportDetail,
  ImportSummary,
  JsonValue,
  Report,
  SampleInfo,
  ValidationResult
} from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers ?? {})
    },
    ...options
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: response.statusText }));
    const detail = payload.detail ?? payload.error?.message ?? payload.error ?? response.statusText;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return response.json() as Promise<T>;
}

export async function listSamples(): Promise<SampleInfo[]> {
  const payload = await request<{ samples: SampleInfo[] }>("/api/sample-data");
  return payload.samples;
}

export async function loadSample(sampleName: string, responseVariant: "pass" | "fail"): Promise<ImportSummary> {
  return request<ImportSummary>("/api/load-sample", {
    method: "POST",
    body: JSON.stringify({ sampleName, responseVariant })
  });
}

export async function importBundle(
  prompt: JsonValue,
  expectedResults: JsonValue,
  response: JsonValue,
  label?: string
): Promise<ImportSummary> {
  return request<ImportSummary>("/api/import", {
    method: "POST",
    body: JSON.stringify({ prompt, expectedResults, response, label })
  });
}

export async function getImport(importId: string): Promise<ImportDetail> {
  return request<ImportDetail>(`/api/import/${importId}`);
}

export async function validateImport(importId: string): Promise<ValidationResult> {
  return request<ValidationResult>("/api/validate", {
    method: "POST",
    body: JSON.stringify({ importId })
  });
}

export async function getReport(importId: string): Promise<Report> {
  return request<Report>(`/api/report/${importId}`);
}

export async function listAcvpSessions(status?: string): Promise<AcvpSessionSummary[]> {
  const query = status ? `?status=${encodeURIComponent(status)}` : "";
  const payload = await request<{ testSessions: AcvpSessionSummary[] }>(`/acvp/v1/testSessions${query}`);
  return payload.testSessions;
}

export async function createAcvpSession(payload: JsonValue): Promise<AcvpSessionDetail> {
  return request<AcvpSessionDetail>("/acvp/v1/testSessions", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function getAcvpSession(sessionId: string): Promise<AcvpSessionDetail> {
  return request<AcvpSessionDetail>(`/acvp/v1/testSessions/${sessionId}`);
}

export async function getAcvpSessionVectorSets(sessionId: string): Promise<AcvpVectorSetSummary[]> {
  const payload = await request<{ vectorSets: AcvpVectorSetSummary[] }>(`/acvp/v1/testSessions/${sessionId}/vectorSets`);
  return payload.vectorSets;
}

export async function getAcvpVectorSet(vectorSetId: string): Promise<AcvpVectorSetDownload> {
  return request<AcvpVectorSetDownload>(`/acvp/v1/vectorSets/${vectorSetId}`);
}

export async function getAcvpExpectedResults(vectorSetId: string): Promise<AcvpExpectedResults> {
  return request<AcvpExpectedResults>(`/acvp/v1/vectorSets/${vectorSetId}/expectedResults`);
}

export async function submitAcvpVectorSetResults(vectorSetId: string, response: JsonValue): Promise<AcvpVectorSetResult> {
  return request<AcvpVectorSetResult>(`/acvp/v1/vectorSets/${vectorSetId}/results`, {
    method: "POST",
    body: JSON.stringify({ response })
  });
}

export async function getAcvpVectorSetResults(vectorSetId: string): Promise<AcvpVectorSetResult> {
  return request<AcvpVectorSetResult>(`/acvp/v1/vectorSets/${vectorSetId}/results`);
}

export async function getAcvpSessionResults(sessionId: string): Promise<AcvpSessionResults> {
  return request<AcvpSessionResults>(`/acvp/v1/testSessions/${sessionId}/results`);
}
