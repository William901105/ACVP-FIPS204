# mldsa-native IUT Scripts

These scripts generate local ML-DSA ACVP response JSON from a `prompt.json` file.
They run the sibling `mldsa-native/test/acvp/acvp_client.py` client first, so
pass responses are produced by the IUT. The backend native oracle is only a
fallback when the IUT client cannot run.

```bash
python3 run_test.py --prompt prompt.json
python3 run_keygen.py --prompt prompt.json
python3 run_keygen_fail.py --prompt prompt.json
```

Outputs are written to mode-specific files:

- `response/response_pass_keyGen.json`
- `response/response_fail_keyGen.json`
- `response/response_pass_sigGen.json`
- `response/response_fail_sigGen.json`
- `response/response_pass_sigVer.json`
- `response/response_fail_sigVer.json`

Unsupported prompt modes or missing IUT/native oracle binaries fail with a
non-zero exit status instead of fabricating crypto output. Prompt JSON files
downloaded from the UI can be kept locally under `prompt/`; generated prompt and
response JSON files are ignored by git.
