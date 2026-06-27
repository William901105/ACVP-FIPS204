# FIPS 204 / ML-DSA ACVP Local Client + Validator

This is a local ACVP client workflow and validator for FIPS 204 / ML-DSA.

This is not a full ACVP server.

Production ACVP server behavior is intentionally out of scope for this MVP.

## Project Purpose

This project supports a local ACVP-style flow:

- capability registration
- test session and vector set creation
- prompt JSON download/import
- IUT response JSON upload
- local validation and report export

The backend can generate local ML-DSA vector sets and expected results using the
native oracle. The validator compares uploaded IUT response fields against those
expected results.

## Current Scope

- ML-DSA / keyGen / FIPS204
- ML-DSA / sigGen / FIPS204
- ML-DSA / sigVer / FIPS204
- Registry-driven frontend selection for FIPS versions
- FIPS203 is visible in the UI as `開發中` and operations are disabled
- Local `/acvp/v1/testSessions` and `/acvp/v1/vectorSets` lifecycle
- ACVP top-level object format
- ACVP top-level array format with an `acvVersion` object followed by a vector-set object
- Local comparison by `tgId` and `tcId`
- `keyGen`: compare `pk` and `sk`
- `sigGen`: compare `signature`
- `sigVer`: compare `testPassed`
- Result states: `passed`, `failed`, `missing`, `malformed`
- JSON and Markdown report export
- IUT response state labels: `waiting`, `loaded`, `ready`, and `error`
- Client-side `campaignSeed` validation matching the backend 16-64 byte hex rule

## Out Of Scope

- Login or JWT
- Vendor, module, or OE management
- NIST Demo ACVTS connection
- Production ACVP protocol compliance
- FIPS203 / ML-KEM operations

## Project Structure

```text
ACVP-FIPS204/
  backend/
    app/
      main.py
      models.py
      acvp_parser.py
      validator.py
      report.py
      sample_loader.py
    requirements.txt
  frontend/
    src/
      App.tsx
      api.ts
      registry.ts
      types.ts
      components/
        Dashboard.tsx
        JsonUpload.tsx
        VectorSetViewer.tsx
        TestGroupTable.tsx
        TestCaseDetail.tsx
        ValidationSummary.tsx
        FailureList.tsx
        ReportViewer.tsx
        JsonViewer.tsx
  sample-data/
    ML-DSA-keyGen-FIPS204/
    ML-DSA-sigGen-FIPS204/
    ML-DSA-sigVer-FIPS204/
  IUT-tests/
    mldsa-native/
      run_test.py
      run_keygen.py
      run_keygen_fail.py
      run_siggen.py
      run_siggen_fail.py
      run_sigver.py
      run_sigver_fail.py
      prompt/
      response/
```

## Install Backend

```bash
cd ACVP-FIPS204/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows PowerShell:

```powershell
cd ACVP-FIPS204/backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Start Backend

```bash
cd ACVP-FIPS204/backend
uvicorn app.main:app --reload --port 8000
```

The same command also works from the project root:

```bash
cd ACVP-FIPS204
uvicorn app.main:app --reload --port 8000
```

The backend enables CORS for `localhost:5173`, `127.0.0.1:5173`, `localhost:3000`, and `127.0.0.1:3000`.

## Install Frontend

```bash
cd ACVP-FIPS204/frontend
npm install
```

## Start Frontend

```bash
cd ACVP-FIPS204/frontend
npm run dev
```

Vite serves the frontend on port `5173` by default.

## Sample Data

The included sample data is copied from the local reference repository under:

```text
ACVP-Server/gen-val/json-files/
```

Included sample sets:

- `ML-DSA-keyGen-FIPS204`
- `ML-DSA-sigGen-FIPS204`
- `ML-DSA-sigVer-FIPS204`

Each sample directory includes:

- `prompt.json`
- `expectedResults.json`
- `response.pass.json`
- `response.fail.json`

`response.pass.json` matches `expectedResults.json`. `response.fail.json` intentionally changes the first relevant field in the first test case.

## ACVP Client Workflow

1. Start the backend.
2. Start the frontend.
3. Select `FIPS 204 / ML-DSA` in the Registry panel.
4. Select one or more modes and parameter sets.
5. Enter a valid campaign seed or leave it empty for the deterministic fallback.
6. Click `Register capabilities`.
7. Download the prompt JSON from the active vector set.
8. Generate an IUT response with `IUT-tests/mldsa-native/run_test.py`.
9. Upload the response JSON in the IUT Response panel.
10. Click `Validate response`, then export JSON or Markdown from Validation Report.

The frontend calls:

```text
GET  /acvp/v1/testSessions
POST /acvp/v1/testSessions
GET  /acvp/v1/testSessions/{sessionId}/vectorSets
GET  /acvp/v1/vectorSets/{vectorSetId}
POST /acvp/v1/vectorSets/{vectorSetId}/results
```

## IUT Response States

The IUT Response chip reports the local upload/validation state:

- `waiting`: no response JSON is loaded
- `loaded`: a response JSON file has been selected
- `ready`: validation completed and all cases passed
- `error: Wrong response format!`: the uploaded response failed schema/mode validation

The response file input is reset after each selection, so the same
`response_pass_<mode>.json` file can be uploaded repeatedly across newly created
test sessions.

## Campaign Seed Validation

For registration-generated vector sets, `campaignSeed` must be an even-length
hex string between 16 and 64 bytes. Empty input is allowed and uses the backend
deterministic fallback seed.

Valid example:

```text
00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF
```

## IUT Scripts

The IUT helpers live in `IUT-tests/mldsa-native/` and use the sibling
`../mldsa-native` checkout as the implementation under test.

```bash
cd ACVP-FIPS204/IUT-tests/mldsa-native
python3 run_test.py --prompt prompt/prompt-keygen.json
python3 run_keygen.py --prompt prompt/prompt-keygen.json
python3 run_keygen_fail.py --prompt prompt/prompt-keygen.json
```

Generated files are written to `response/response_pass_<mode>.json` and
`response/response_fail_<mode>.json`. Prompt and response JSON files in the IUT
test folders are ignored by git.

## Run Validation

Click `Validate`.

The validator:

- Aligns expected and response test cases by `tgId` and `tcId`
- Marks missing response test cases as `missing`
- Marks missing required response fields as `malformed`
- Marks mismatched values as `failed`
- Marks exact matches as `passed`

The frontend calls:

```text
POST /api/validate
```

## Export Report

Click `Report` after loading or importing a bundle. The Report Export panel can download:

- `report-<importId>.json`
- `report-<importId>.md`

The frontend calls:

```text
GET /api/report/{importId}
```

## API Summary

```text
GET  /api/health
POST /api/import
POST /api/validate
GET  /api/import/{importId}
GET  /api/report/{importId}
GET  /api/sample-data
POST /api/load-sample
GET  /acvp/v1/version
GET  /acvp/v1/algorithms
GET  /acvp/v1/testSessions
POST /acvp/v1/testSessions
GET  /acvp/v1/testSessions/{sessionId}
GET  /acvp/v1/testSessions/{sessionId}/vectorSets
GET  /acvp/v1/testSessions/{sessionId}/results
GET  /acvp/v1/vectorSets/{vectorSetId}
GET  /acvp/v1/vectorSets/{vectorSetId}/expectedResults
POST /acvp/v1/vectorSets/{vectorSetId}/results
```

## Roadmap

- Add an ML-DSA oracle integration point
- Add a NIST GenValAppRunner wrapper integration point
- Add a simplified session API
- Add optional persisted import sessions
- Add a full ACVP-compatible API layer as a separate future milestone
