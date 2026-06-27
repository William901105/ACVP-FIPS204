# ACVP v1 Capabilities Negotiation

Phase 3-3 adds a local ML-DSA registration/capabilities negotiation layer for the `/acvp/v1` skeleton. It is based on the NIST ACVP Protocol Specification registration/capabilities exchange model and the NIST ACVP ML-DSA JSON Specification. It is still not a production-ready ACVP server.

References:

- ACVP Protocol Specification: https://pages.nist.gov/ACVP/draft-fussell-acvp-spec.html
- ACVP ML-DSA JSON Specification: https://pages.nist.gov/ACVP/draft-celi-acvp-ml-dsa.html
- ACVP documentation landing page: https://pages.nist.gov/ACVP/
- FIPS 204: https://csrc.nist.gov/pubs/fips/204/final

Every Phase 3-3 response still includes:

```json
{
  "productionReady": false,
  "profile": "local-fips204-skeleton",
  "demoOnly": true,
  "notProductionAcvp": true
}
```

## Supported Container

The skeleton accepts a registration container with an `algorithms` array:

```json
{
  "algorithms": [
    {
      "algorithm": "ML-DSA",
      "mode": "keyGen",
      "revision": "FIPS204",
      "parameterSets": ["ML-DSA-44", "ML-DSA-65"]
    }
  ],
  "label": "phase 3-3 registration session"
}
```

Each algorithm object is validated with the existing ML-DSA registration schema before negotiation.

Supported values:

- modes: `keyGen`, `sigGen`, `sigVer`
- parameter sets: `ML-DSA-44`, `ML-DSA-65`, `ML-DSA-87`
- signature interfaces: `internal`, `external`
- signature features: `deterministic`, `externalMu`, `preHash`, `messageLength`, `contextLength`, `hashAlgs`

The current schema treats length domains as bit domains. `messageLength` must stay within the existing ML-DSA schema range and 8-bit increment rules; `contextLength` must stay within the existing 0..2040 bit range with 8-bit increment alignment.

## Negotiated Plan

`POST /acvp/v1/testSessions` now supports two local skeleton request forms:

- prompt-based Phase 3-2 sessions with `prompt`
- registration/capabilities Phase 3-3 sessions with `algorithms`

For a registration container, the server creates an in-memory session with:

```json
{
  "status": "capabilitiesAccepted",
  "vectorSetIds": [],
  "vectorSetUrls": [],
  "negotiatedCapabilities": {
    "algorithm": "ML-DSA",
    "revision": "FIPS204",
    "negotiated": [],
    "unsupported": [],
    "warnings": []
  },
  "nextAction": "Server-side vector generation from negotiated capabilities is planned for Phase 3-4."
}
```

Phase 3-3 does not create prompts or vector sets from capabilities. `GET /acvp/v1/testSessions/{sessionId}/vectorSets` returns an empty list for capabilities-only sessions. `GET /acvp/v1/testSessions/{sessionId}/results` returns `409 VECTOR_SETS_NOT_GENERATED` until Phase 3-4 vector generation exists.

## SHAKE Handling

The ML-DSA schema constants include `SHAKE-128` and `SHAKE-256`, so those names may validate in `hashAlgs`. The local expectedResults/vector generation path does not generate SHAKE preHash cases because the current API does not represent SHAKE output length behavior. Phase 3-3 therefore excludes SHAKE values from negotiated generated hash algorithms and returns a warning/unsupported entry when at least one non-SHAKE generated hash remains.

If a registration requests only unsupported generated hash capabilities, the skeleton returns:

```json
{
  "error": {
    "code": "UNSUPPORTED_CAPABILITIES",
    "message": "No supported ML-DSA capabilities were negotiated.",
    "path": "$.algorithms"
  }
}
```

## Exclusions

Phase 3-3 intentionally does not include:

- server-side vector generation from capabilities
- formal random vector generation
- DB persistence
- JWT/login/mTLS
- vendor/module/OE/dependency resources
- production ACVP certification workflow

Next phase: Phase 3-4 vector generation from negotiated capabilities.
