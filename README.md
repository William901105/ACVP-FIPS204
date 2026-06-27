# FIPS 204 / ML-DSA ACVP Web Viewer + Local JSON Validator

This is a FIPS 204 / ML-DSA ACVP JSON viewer and local validation demo.

This is not a full ACVP server.

Full ACVP server workflow is intentionally out of scope for this MVP.

## Project Purpose

This project loads ACVP-style `prompt.json`, `expectedResults.json`, and `response.json` files for ML-DSA FIPS 204 vector sets, displays the vector set in a web UI, and performs local JSON comparison between expected results and a response file.

The validator does not run ML-DSA cryptographic operations. It only compares response fields against `expectedResults.json`.

## Current Scope

- ML-DSA / keyGen / FIPS204
- ML-DSA / sigGen / FIPS204
- ML-DSA / sigVer / FIPS204
- ACVP top-level object format
- ACVP top-level array format with an `acvVersion` object followed by a vector-set object
- Local comparison by `tgId` and `tcId`
- `keyGen`: compare `pk` and `sk`
- `sigGen`: compare `signature`
- `sigVer`: compare `testPassed`
- Result states: `passed`, `failed`, `missing`, `malformed`
- JSON and Markdown report export

## Out Of Scope

- Login or JWT
- Formal `/testSessions`
- Full vectorSet lifecycle
- Vendor, module, or OE management
- Database-backed workflow
- NIST Demo ACVTS connection
- Production ACVP protocol compliance
- Cryptographic recomputation of key generation, signing, or verification

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

## Load Sample Data

1. Start the backend.
2. Start the frontend.
3. Use the Dashboard sample list.
4. Select `Pass` or `Fail` for one of the ML-DSA FIPS204 samples.

The frontend calls:

```text
GET /api/sample-data
POST /api/load-sample
```

## Upload JSON

Use the JSON Upload panel to select:

- `prompt.json`
- `expectedResults.json`
- `response.json`

After import, the UI displays vector-set metadata, test groups, test cases, and loaded JSON details.

The frontend calls:

```text
POST /api/import
```

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
```

## Roadmap

- Add an ML-DSA oracle integration point
- Add a NIST GenValAppRunner wrapper integration point
- Add a simplified session API
- Add optional persisted import sessions
- Add a full ACVP-compatible API layer as a separate future milestone
