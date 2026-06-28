import type {
  AcvpEnvelope,
  AcvpExpectedPayload,
  AcvpExpectedResults,
  AcvpGenerationProfile,
  AcvpSessionDetail,
  AcvpSessionSummary,
  AcvpStrictSessionResultItem,
  AcvpStrictVectorSetResultTest,
  AcvpStrictVectorSetResults,
  AcvpVectorSetDownload,
  AcvpVectorSetPayload,
  AcvpVectorSetResult,
  AcvpVectorSetSummary,
  AcvpWorkflowProfile,
  ImportDetail,
  ImportSummary,
  JsonObject,
  JsonValue,
  NormalizedExpectedView,
  NormalizedSessionResultsView,
  NormalizedVectorSetResultView,
  NormalizedVectorSetView,
  Report,
  SampleInfo,
  ValidationResult
} from "./types";

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

interface RequestOptions extends RequestInit {
  preserveAcvpEnvelope?: boolean;
}

export interface AcvpClientOptions {
  workflowProfile?: AcvpWorkflowProfile;
  generationProfile?: AcvpGenerationProfile;
  isSample?: boolean;
}

export class ApiError extends Error {
  readonly status: number;
  readonly code?: string;
  readonly path?: string;
  readonly payload?: unknown;

  constructor(message: string, status: number, payload?: unknown, code?: string, path?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.payload = payload;
    this.code = code;
    this.path = path;
  }
}

export function isAcvpEnvelope(payload: unknown): payload is AcvpEnvelope<unknown> {
  return (
    Array.isArray(payload) &&
    payload.length >= 2 &&
    isRecord(payload[0]) &&
    typeof payload[0].acvVersion === "string"
  );
}

export function unwrapAcvpEnvelope<T>(payload: unknown): T {
  if (isAcvpEnvelope(payload)) {
    return payload[1] as T;
  }
  return payload as T;
}

async function request<T>(path: string, options?: RequestOptions): Promise<T> {
  const payload = await requestMaybeJson<T>(path, options);
  if (payload === undefined) {
    throw new Error("Response did not include a JSON body.");
  }
  return payload;
}

export async function requestJson<T>(path: string, options?: RequestOptions): Promise<T> {
  return request<T>(path, options);
}

export async function requestMaybeJson<T>(path: string, options?: RequestOptions): Promise<T | undefined> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers ?? {})
    },
    ...options
  });

  const payload = await parseResponsePayload(response);

  if (!response.ok) {
    throw buildApiError(response, payload);
  }

  if (payload === undefined) {
    return undefined;
  }

  if (options?.preserveAcvpEnvelope) {
    return payload as T;
  }

  return unwrapAcvpEnvelope<T>(payload);
}

export async function requestNoContentAware<T>(path: string, options?: RequestOptions): Promise<T | undefined> {
  return requestMaybeJson<T>(path, options);
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

export async function clearDemoData(): Promise<{ deleted: boolean; deletedFiles: string[]; message: string }> {
  return request<{ deleted: boolean; deletedFiles: string[]; message: string }>("/api/demo/clear?confirm=true", {
    method: "DELETE"
  });
}

export async function listAcvpSessions(options: AcvpClientOptions = {}, status?: string): Promise<AcvpSessionSummary[]> {
  const payload = await request<{ testSessions: AcvpSessionSummary[] }>(
    withQuery("/acvp/v1/testSessions", {
      workflowProfile: options.workflowProfile,
      status
    })
  );
  return payload.testSessions;
}

export async function createAcvpSession(payload: JsonValue, options: AcvpClientOptions = {}): Promise<AcvpSessionDetail> {
  const body = mergeSessionOptions(payload, options);
  return request<AcvpSessionDetail>(
    withQuery("/acvp/v1/testSessions", {
      workflowProfile: options.workflowProfile
    }),
    {
      method: "POST",
      body: JSON.stringify(body)
    }
  );
}

export async function getAcvpSession(sessionId: string, options: AcvpClientOptions = {}): Promise<AcvpSessionDetail> {
  return request<AcvpSessionDetail>(
    withQuery(`/acvp/v1/testSessions/${encodeURIComponent(sessionId)}`, {
      workflowProfile: options.workflowProfile
    })
  );
}

export async function getAcvpSessionVectorSets(
  sessionId: string,
  options: AcvpClientOptions = {}
): Promise<AcvpVectorSetSummary[]> {
  const payload = await request<{ vectorSets: AcvpVectorSetSummary[] }>(
    withQuery(`/acvp/v1/testSessions/${encodeURIComponent(sessionId)}/vectorSets`, {
      workflowProfile: options.workflowProfile
    })
  );
  return payload.vectorSets;
}

export async function getAcvpVectorSetPrompt(
  sessionId: string,
  vectorSetId: string,
  options: AcvpClientOptions = {}
): Promise<NormalizedVectorSetView> {
  const payload = await requestJson<unknown>(
    withQuery(
      `/acvp/v1/testSessions/${encodeURIComponent(sessionId)}/vectorSets/${encodeURIComponent(vectorSetId)}`,
      {
        workflowProfile: options.workflowProfile
      }
    )
  );
  return normalizeVectorSetPrompt(payload, sessionId, vectorSetId);
}

export async function getAcvpExpectedResults(
  sessionId: string,
  vectorSetId: string,
  options: AcvpClientOptions = {}
): Promise<NormalizedExpectedView> {
  const payload = await requestJson<unknown>(
    withQuery(
      `/acvp/v1/testSessions/${encodeURIComponent(sessionId)}/vectorSets/${encodeURIComponent(vectorSetId)}/expected`,
      {
        workflowProfile: options.workflowProfile
      }
    )
  );
  return normalizeExpectedResults(payload);
}

export async function submitAcvpVectorSetResults(
  sessionId: string,
  vectorSetId: string,
  response: JsonValue,
  options: AcvpClientOptions = {}
): Promise<NormalizedVectorSetResultView | undefined> {
  const body = isAcvpEnvelope(response) ? response : { response };
  const payload = await requestNoContentAware<unknown>(
    withQuery(
      `/acvp/v1/testSessions/${encodeURIComponent(sessionId)}/vectorSets/${encodeURIComponent(vectorSetId)}/results`,
      {
        workflowProfile: options.workflowProfile
      }
    ),
    {
      method: "POST",
      body: JSON.stringify(body)
    }
  );

  if (payload === undefined) {
    return undefined;
  }

  return normalizeVectorSetResults(payload);
}

export async function getAcvpVectorSetResults(
  sessionId: string,
  vectorSetId: string,
  options: AcvpClientOptions = {}
): Promise<NormalizedVectorSetResultView> {
  const payload = await requestJson<unknown>(
    withQuery(
      `/acvp/v1/testSessions/${encodeURIComponent(sessionId)}/vectorSets/${encodeURIComponent(vectorSetId)}/results`,
      {
        workflowProfile: options.workflowProfile
      }
    )
  );
  return normalizeVectorSetResults(payload);
}

export async function getAcvpSessionResults(
  sessionId: string,
  options: AcvpClientOptions = {}
): Promise<NormalizedSessionResultsView> {
  const payload = await requestJson<unknown>(
    withQuery(`/acvp/v1/testSessions/${encodeURIComponent(sessionId)}/results`, {
      workflowProfile: options.workflowProfile
    })
  );
  return normalizeSessionResults(payload);
}

export function expectedDeniedView(reason: string): NormalizedExpectedView {
  return {
    available: false,
    denied: true,
    reason
  };
}

async function parseResponsePayload(response: Response): Promise<unknown | undefined> {
  if (response.status === 204) {
    return undefined;
  }
  const text = await response.text();
  if (!text) {
    return undefined;
  }
  try {
    return JSON.parse(text) as unknown;
  } catch {
    return text;
  }
}

function buildApiError(response: Response, payload: unknown): ApiError {
  const body = unwrapAcvpEnvelope<unknown>(payload);
  const detail = extractErrorDetail(body);
  return new ApiError(detail.message || response.statusText, response.status, payload, detail.code, detail.path);
}

function extractErrorDetail(payload: unknown): { message: string; code?: string; path?: string } {
  if (isRecord(payload)) {
    const error = payload.error;
    if (isRecord(error)) {
      const message = stringValue(error.message) ?? stringValue(error.detail) ?? "Request failed.";
      return {
        message,
        code: stringValue(error.code),
        path: stringValue(error.path)
      };
    }
    const detail = payload.detail;
    if (typeof detail === "string") {
      return { message: detail };
    }
    if (detail !== undefined) {
      return { message: JSON.stringify(detail) };
    }
    const message = stringValue(payload.message);
    if (message) {
      return {
        message,
        code: stringValue(payload.code),
        path: stringValue(payload.path)
      };
    }
  }
  if (typeof payload === "string") {
    return { message: payload };
  }
  return { message: "Request failed." };
}

function withQuery(path: string, params: Record<string, string | number | boolean | undefined | null>): string {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== "") {
      query.set(key, String(value));
    }
  }
  const queryString = query.toString();
  return queryString ? `${path}?${queryString}` : path;
}

function mergeSessionOptions(payload: JsonValue, options: AcvpClientOptions): JsonValue {
  if (!isRecord(payload) || Array.isArray(payload)) {
    return payload;
  }
  const body: Record<string, JsonValue> = { ...(payload as JsonObject) };
  if (options.generationProfile !== undefined) {
    body.generationProfile = options.generationProfile;
  }
  if (options.isSample !== undefined) {
    body.isSample = options.isSample;
  }
  return body;
}

function normalizeVectorSetPrompt(payload: unknown, sessionId: string, vectorSetId: string): NormalizedVectorSetView {
  const body = unwrapAcvpEnvelope<unknown>(payload);
  if (isRecord(body) && isVectorSetPayload(body.prompt)) {
    return {
      vectorSetId: stringValue(body.vectorSetId) ?? vectorSetId,
      sessionId: stringValue(body.testSessionId) ?? sessionId,
      status: stringValue(body.status),
      prompt: body.prompt,
      raw: payload,
      sourceShape: "local-wrapper"
    };
  }
  if (isVectorSetPayload(body)) {
    return {
      vectorSetId,
      sessionId,
      status: stringValue(isRecord(body) ? body.status : undefined),
      prompt: body,
      raw: payload,
      sourceShape: "strict-payload"
    };
  }
  throw new Error("Vector set response did not contain an ACVP prompt payload.");
}

function normalizeExpectedResults(payload: unknown): NormalizedExpectedView {
  const body = unwrapAcvpEnvelope<unknown>(payload);
  if (isRecord(body) && isVectorSetPayload(body.expectedResults)) {
    return {
      available: true,
      denied: false,
      expectedResults: body.expectedResults,
      raw: payload,
      sourceShape: "local-wrapper"
    };
  }
  if (isVectorSetPayload(body)) {
    return {
      available: true,
      denied: false,
      expectedResults: body,
      raw: payload,
      sourceShape: "strict-payload"
    };
  }
  return {
    available: false,
    denied: false,
    reason: "Expected results response did not contain a vector set payload.",
    raw: payload
  };
}

function normalizeVectorSetResults(payload: unknown): NormalizedVectorSetResultView {
  const body = unwrapAcvpEnvelope<unknown>(payload);
  const strictResults = extractStrictVectorSetResults(body);
  if (strictResults) {
    return {
      disposition: strictResults.results.disposition,
      tests: strictResults.results.tests,
      raw: payload,
      acvpResults: strictResults,
      sourceShape: isRecord(body) && ("validationResult" in body || "report" in body) ? "local-wrapper" : "strict-payload",
      status: isRecord(body) ? stringValue(body.status) : undefined,
      validationResult: isRecord(body) && isValidationResult(body.validationResult) ? body.validationResult : undefined,
      report: isRecord(body) && isReport(body.report) ? body.report : undefined
    };
  }

  if (isRecord(body) && isValidationResult(body.validationResult)) {
    const summary = body.validationResult.summary;
    const disposition = summary.failed === 0 && summary.missing === 0 && summary.malformed === 0 ? "passed" : "fail";
    return {
      disposition,
      tests: [],
      raw: payload,
      sourceShape: "local-wrapper",
      status: stringValue(body.status),
      validationResult: body.validationResult,
      report: isReport(body.report) ? body.report : undefined
    };
  }

  throw new Error("Vector set results response did not contain a recognizable result body.");
}

function normalizeSessionResults(payload: unknown): NormalizedSessionResultsView {
  const body = unwrapAcvpEnvelope<unknown>(payload);
  if (isStrictSessionResults(body)) {
    return {
      passed: body.passed,
      results: body.results,
      raw: payload,
      sourceShape: "strict-payload"
    };
  }

  if (isRecord(body)) {
    return {
      passed: booleanValue(body.summary && isRecord(body.summary) ? body.summary.passed : undefined),
      results: localVectorSetResultsToSessionItems(body.vectorSetResults),
      raw: payload,
      sourceShape: "local-wrapper",
      status: stringValue(body.status),
      summary: isJsonObject(body.summary) ? body.summary : undefined,
      vectorSetResults: Array.isArray(body.vectorSetResults) ? (body.vectorSetResults as AcvpVectorSetResult[]) : undefined
    };
  }

  throw new Error("Test session results response did not contain a recognizable result body.");
}

function extractStrictVectorSetResults(payload: unknown): AcvpStrictVectorSetResults | undefined {
  if (!isRecord(payload)) {
    return undefined;
  }
  if (isStrictVectorSetResults(payload)) {
    return payload;
  }
  if (isStrictVectorSetResults(payload.acvpResults)) {
    return payload.acvpResults;
  }
  return undefined;
}

function localVectorSetResultsToSessionItems(value: unknown): AcvpStrictSessionResultItem[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value
    .filter(isRecord)
    .map((item) => ({
      vectorSetUrl: stringValue(item.vectorSetId) ?? "",
      status: stringValue(item.status) ?? "unknown",
      disposition: statusToDisposition(stringValue(item.status))
    }));
}

function statusToDisposition(status: string | undefined): string {
  if (status === "validated") {
    return "passed";
  }
  if (status === "failed") {
    return "fail";
  }
  return status ?? "unreceived";
}

function isVectorSetPayload(value: unknown): value is AcvpVectorSetPayload {
  return isRecord(value) && Array.isArray(value.testGroups);
}

function isStrictVectorSetResults(value: unknown): value is AcvpStrictVectorSetResults {
  return (
    isRecord(value) &&
    isRecord(value.results) &&
    typeof value.results.disposition === "string" &&
    Array.isArray(value.results.tests)
  );
}

function isStrictSessionResults(value: unknown): value is { passed: boolean; results: AcvpStrictSessionResultItem[] } {
  return isRecord(value) && typeof value.passed === "boolean" && Array.isArray(value.results);
}

function isValidationResult(value: unknown): value is ValidationResult {
  return isRecord(value) && isRecord(value.summary) && typeof value.summary.total === "number";
}

function isReport(value: unknown): value is Report {
  return isRecord(value) && typeof value.markdown === "string";
}

function isJsonObject(value: unknown): value is JsonObject {
  if (!isRecord(value)) {
    return false;
  }
  return Object.values(value).every(isJsonValue);
}

function isJsonValue(value: unknown): value is JsonValue {
  if (
    value === null ||
    typeof value === "string" ||
    typeof value === "number" ||
    typeof value === "boolean"
  ) {
    return true;
  }
  if (Array.isArray(value)) {
    return value.every(isJsonValue);
  }
  return isJsonObject(value);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function stringValue(value: unknown): string | undefined {
  return typeof value === "string" ? value : undefined;
}

function booleanValue(value: unknown): boolean | undefined {
  return typeof value === "boolean" ? value : undefined;
}
