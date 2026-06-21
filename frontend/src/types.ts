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

