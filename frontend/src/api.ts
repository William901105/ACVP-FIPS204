import type { ImportDetail, ImportSummary, JsonValue, Report, SampleInfo, ValidationResult } from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

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
    throw new Error(payload.detail ?? response.statusText);
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

