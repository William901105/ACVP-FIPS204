# mldsa-native IUT Scripts

These scripts generate local ML-DSA ACVP response JSON from a `prompt.json` file.
They reuse the backend ML-DSA expected-results path, which is backed by the local
native oracle binaries under `backend/native/mldsa_oracle`.

```bash
python3 run_test.py --prompt prompt.json
python3 run_keygen.py --prompt prompt.json
python3 run_keygen_fail.py --prompt prompt.json
```

Outputs are written to `response/response_pass.json` and
`response/response_fail.json`. Unsupported prompt modes or missing native oracle
binaries fail with a non-zero exit status instead of fabricating crypto output.
