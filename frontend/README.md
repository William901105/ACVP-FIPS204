# ACVP FIPS 204 Frontend

React/Vite client for the local ACVP FIPS 204 server demo. The UI supports both the local skeleton workflow and the stricter ACVP-like workflow profile.

This is not a production ACVP client. Auth/JWT/mTLS, `/large` submission, async validation, and production ACVP resource workflows are not implemented.

## Start The Backend

```bash
cd /root/ACVP204/ACVP-FIPS204/backend/native/mldsa_oracle
make clean
make MLDSA_NATIVE_DIR=/root/ACVP204/mldsa-native

cd /root/ACVP204/ACVP-FIPS204/backend
source .venv/bin/activate
ACVP_DB_PATH=/tmp/acvp_ui_demo.sqlite3 uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

## Start The Frontend

```bash
cd /root/ACVP204/ACVP-FIPS204/frontend
npm install
npm run dev
```

Open:

```text
http://127.0.0.1:5173
```

Build check:

```bash
npm run build
```

## API Base URL

The default backend URL is:

```text
http://127.0.0.1:8000
```

Override it with Vite:

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000 npm run dev
```

Do not commit `frontend/.env.local`.

## Workflow Profile

`workflowProfile` controls route behavior and response shape.

| Profile | Behavior |
| --- | --- |
| `strict` | Uses canonical nested routes, direct ACVP payloads, sample-only expected results, 204 response submission, and GET results for disposition. |
| `local` | Preserves local skeleton wrappers, downloadable expected results, and immediate validation response bodies for demo/debug. |

Strict routes use:

```text
/acvp/v1/testSessions/{sessionId}/vectorSets/{vectorSetId}
/acvp/v1/testSessions/{sessionId}/vectorSets/{vectorSetId}/expected
/acvp/v1/testSessions/{sessionId}/vectorSets/{vectorSetId}/results
/acvp/v1/testSessions/{sessionId}/results
```

Strict mode does not use flat vectorSet aliases.

## Generation Profile

`generationProfile` is separate from `workflowProfile`.

| Profile | Purpose |
| --- | --- |
| `local-debug` | Small vector sets for quick UI/debug runs. |
| `nist-conformance` | NIST-oriented vector counts and KAT coverage. |

`generationProfile` controls generated vector count and KAT coverage only. It does not control response envelopes or route shape.

## Sample Policy

`isSample=true` allows expected results to be downloaded.

`isSample=false` with `workflowProfile=strict` hides expected results from the client. The server still keeps hidden expected results for server-side validation.

The UI does not auto-download expected results for strict non-sample sessions.

## Result Submission

Strict result submission returns:

```text
204 No Content
```

HTTP 204 only means the response was accepted. The UI then calls:

```text
GET /acvp/v1/testSessions/{sessionId}/vectorSets/{vectorSetId}/results?workflowProfile=strict
```

to display `passed`, `fail`, `unreceived`, or another disposition.

## FIPS203 Status

FIPS203 / ML-KEM remains visible but disabled because the backend is not merged yet. The UI does not submit ML-KEM registration payloads and does not include a fake FIPS203 provider.
