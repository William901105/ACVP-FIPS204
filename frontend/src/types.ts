export type JsonValue =
  | string
  | number
  | boolean
  | null
  | JsonValue[]
  | { [key: string]: JsonValue };

export type JsonObject = Record<string, JsonValue>;

export interface ImportSummary {
  importId: string;
  label?: string | null;
  vsId?: number | string | null;
  algorithm?: string | null;
  mode?: string | null;
  revision?: string | null;
  testGroupCount: number;
  testCaseCount: number;
}

export interface SampleInfo {
  name: string;
  path: string;
  hasPassResponse: boolean;
  hasFailResponse: boolean;
  vsId?: number | string | null;
  algorithm?: string | null;
  mode?: string | null;
  revision?: string | null;
  testGroupCount?: number;
  testCaseCount?: number;
}

export interface AcvpTestCase {
  tcId: number | string;
  [key: string]: JsonValue;
}

export interface AcvpTestGroup {
  tgId: number | string;
  testType?: string;
  parameterSet?: string;
  tests: AcvpTestCase[];
  [key: string]: JsonValue | AcvpTestCase[] | undefined;
}

export interface AcvpVectorSet {
  vsId?: number | string;
  algorithm?: string;
  mode?: string;
  revision?: string;
  testGroups: AcvpTestGroup[];
  [key: string]: JsonValue | AcvpTestGroup[] | undefined;
}

export interface FailureDetail {
  tgId: number | string;
  tcId: number | string;
  field: string;
  reason: string;
  expected: JsonValue | string | null;
  provided: JsonValue | string | null;
}

export type CaseStatus = "passed" | "failed" | "missing" | "malformed";

export interface CaseResult {
  tgId: number | string;
  tcId: number | string;
  status: CaseStatus;
  prompt?: JsonObject | null;
  expected: JsonObject;
  response?: JsonObject | null;
  failures: FailureDetail[];
  group: JsonObject;
}

export interface ValidationSummaryCounts {
  total: number;
  passed: number;
  failed: number;
  missing: number;
  malformed: number;
  extra?: number;
}

export interface ValidationResult {
  metadata: {
    vsId?: number | string | null;
    algorithm?: string | null;
    mode?: string | null;
    revision?: string | null;
  };
  summary: ValidationSummaryCounts;
  failures: FailureDetail[];
  caseResults: CaseResult[];
}

export interface ImportDetail {
  importId: string;
  label?: string | null;
  summary: ImportSummary;
  prompt: AcvpVectorSet;
  expectedResults: AcvpVectorSet;
  response: AcvpVectorSet;
  validationResult?: ValidationResult | null;
}

export interface Report {
  importId: string;
  generatedAt: string;
  algorithm?: string | null;
  mode?: string | null;
  revision?: string | null;
  vsId?: number | string | null;
  totalTestCases: number;
  passedCount: number;
  failedCount: number;
  missingCount: number;
  malformedCount: number;
  failureDetails: FailureDetail[];
  markdown: string;
}

export type FipsVersionId = "FIPS203" | "FIPS204";
export type CapabilityMode = "keyGen" | "sigGen" | "sigVer";

export interface CapabilityModeConfig {
  id: CapabilityMode;
  label: string;
  enabled: boolean;
}

export interface FipsVersionConfig {
  id: FipsVersionId;
  label: string;
  algorithm: string;
  revision: string;
  enabled: boolean;
  status: "available" | "in-development";
  modes: CapabilityModeConfig[];
  parameterSets: string[];
  defaultParameterSets: string[];
  defaultHashAlgs?: string[];
}

export interface AcvpSessionSummary {
  testSessionId: string;
  status: string;
  label?: string | null;
  vectorSetIds: string[];
  vectorSetUrls: string[];
  vectorSetCount: number;
  mode?: string | null;
  algorithm?: string | null;
  revision?: string | null;
  testGroupCount?: number;
  testCaseCount?: number;
  productionReady: boolean;
  profile: string;
  demoOnly: boolean;
  notProductionAcvp: boolean;
  [key: string]: unknown;
}

export interface AcvpSessionDetail extends AcvpSessionSummary {
  vectorSets?: AcvpVectorSetSummary[];
  stateHistory?: JsonValue[];
  negotiatedCapabilities?: JsonValue;
  vectorGeneration?: JsonValue;
}

export interface AcvpVectorSetSummary {
  vectorSetId: string;
  testSessionId: string;
  status: string;
  url: string;
  mode?: string | null;
  vsId?: number | string | null;
  algorithm?: string | null;
  revision?: string | null;
  testGroupCount?: number;
  testCaseCount?: number;
  downloadedAt?: string | null;
  submittedAt?: string | null;
  validatedAt?: string | null;
  productionReady: boolean;
  profile: string;
  demoOnly: boolean;
  notProductionAcvp: boolean;
  [key: string]: unknown;
}

export interface AcvpVectorSetDownload {
  vectorSetId: string;
  testSessionId: string;
  status: string;
  prompt: AcvpVectorSet;
  stateHistory?: JsonValue[];
  productionReady: boolean;
  profile: string;
  demoOnly: boolean;
  notProductionAcvp: boolean;
  [key: string]: unknown;
}

export interface AcvpExpectedResults {
  vectorSetId: string;
  testSessionId: string;
  expectedResults: AcvpVectorSet;
  status: string;
  productionReady: boolean;
  profile: string;
  demoOnly: boolean;
  notProductionAcvp: boolean;
}

export interface AcvpVectorSetResult {
  vectorSetId: string;
  testSessionId: string;
  status: string;
  validationResult: ValidationResult;
  report: Report;
  stateHistory?: JsonValue[];
  productionReady: boolean;
  profile: string;
  demoOnly: boolean;
  notProductionAcvp: boolean;
}

export interface AcvpSessionResults {
  testSessionId: string;
  status: string;
  summary: JsonObject;
  vectorSetResults: AcvpVectorSetResult[];
  productionReady: boolean;
  profile: string;
  demoOnly: boolean;
  notProductionAcvp: boolean;
}
