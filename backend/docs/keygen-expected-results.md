# ML-DSA keyGen expectedResults generation

This backend currently supports:

- ML-DSA keyGen native oracle binaries backed by `mldsa-native`.
- `POST /api/oracle/mldsa/keygen` for a single deterministic keyGen oracle call.
- `POST /api/oracle/mldsa/keygen/expected-results` for generating keyGen `expectedResults` from an ACVP-style keyGen prompt.
- `POST /api/import/generated-keygen` for importing a prompt plus response while generating keyGen `expectedResults` server-side.

This is still a local demo service, not a formal ACVP server.

## Build native oracle

```bash
cd backend/native/mldsa_oracle
make clean
make MLDSA_NATIVE_DIR=/root/ACVP204/mldsa-native
```

The build creates:

```text
bin/mldsa44_keygen_oracle
bin/mldsa65_keygen_oracle
bin/mldsa87_keygen_oracle
```

## Test the C oracle

```bash
cd backend/native/mldsa_oracle
./bin/mldsa44_keygen_oracle 000102030405060708090A0B0C0D0E0F101112131415161718191A1B1C1D1E1F
```

The output is JSON with `pk` and `sk`.

## Start the backend

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Call the single-case keyGen endpoint

```bash
curl -X POST http://127.0.0.1:8000/api/oracle/mldsa/keygen \
  -H "Content-Type: application/json" \
  -d '{
    "parameterSet": "ML-DSA-44",
    "seed": "000102030405060708090A0B0C0D0E0F101112131415161718191A1B1C1D1E1F"
  }'
```

## Generate keyGen expectedResults

```bash
curl -X POST http://127.0.0.1:8000/api/oracle/mldsa/keygen/expected-results \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": {
      "vsId": 42,
      "algorithm": "ML-DSA",
      "mode": "keyGen",
      "revision": "FIPS204",
      "testGroups": [
        {
          "tgId": 1,
          "testType": "AFT",
          "parameterSet": "ML-DSA-44",
          "tests": [
            {
              "tcId": 1,
              "seed": "000102030405060708090A0B0C0D0E0F101112131415161718191A1B1C1D1E1F"
            }
          ]
        }
      ]
    }
  }'
```

The generated `expectedResults` preserves `vsId`, `algorithm`, `mode`, `revision`, `tgId`, and `tcId`, and includes `pk` and `sk`. It does not copy prompt `seed` values into response test cases.

## Current non-goals

The backend does not currently include:

- `/acvp/v1/testSessions`
- Database persistence
- JWT authentication
- sigGen oracle
- sigVer oracle
- Full ACVP vector set lifecycle
