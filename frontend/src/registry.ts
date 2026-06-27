import type { FipsVersionConfig } from "./types";

export const FIPS_REGISTRY: FipsVersionConfig[] = [
  {
    id: "FIPS204",
    label: "FIPS 204 / ML-DSA",
    algorithm: "ML-DSA",
    revision: "FIPS204",
    enabled: true,
    status: "available",
    modes: [
      { id: "keyGen", label: "keyGen", enabled: true },
      { id: "sigGen", label: "sigGen", enabled: true },
      { id: "sigVer", label: "sigVer", enabled: true }
    ],
    parameterSets: ["ML-DSA-44", "ML-DSA-65", "ML-DSA-87"],
    defaultParameterSets: ["ML-DSA-44"],
    defaultHashAlgs: ["SHA2-256"]
  },
  {
    id: "FIPS203",
    label: "FIPS 203 / ML-KEM",
    algorithm: "ML-KEM",
    revision: "FIPS203",
    enabled: false,
    status: "in-development",
    modes: [],
    parameterSets: [],
    defaultParameterSets: []
  }
];

export function getFipsConfig(id: string): FipsVersionConfig {
  return FIPS_REGISTRY.find((item) => item.id === id) ?? FIPS_REGISTRY[0];
}
