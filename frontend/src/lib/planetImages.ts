export const PLANET_IMAGE_MANIFEST_URL =
  "https://storage.googleapis.com/openstars-assets/images/manifest.json";

export interface PlanetImageManifest {
  version: string;
  baseUrl: string;
  imagesByClass: Record<string, string[]>;
}

let manifestPromise: Promise<PlanetImageManifest> | null = null;

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((item) => typeof item === "string");
}

function isPlanetImageManifest(value: unknown): value is PlanetImageManifest {
  if (typeof value !== "object" || value === null) return false;

  const candidate = value as Partial<PlanetImageManifest>;
  if (typeof candidate.version !== "string" || typeof candidate.baseUrl !== "string") {
    return false;
  }

  if (typeof candidate.imagesByClass !== "object" || candidate.imagesByClass === null) {
    return false;
  }

  return Object.values(candidate.imagesByClass).every(isStringArray);
}

/**
 * Lightweight deterministic hash (FNV-1a 32-bit).
 * Stable across browser sessions and runtimes.
 */
function hashString(input: string): number {
  let hash = 0x811c9dc5;
  for (let i = 0; i < input.length; i += 1) {
    hash ^= input.charCodeAt(i);
    hash = Math.imul(hash, 0x01000193);
  }
  return hash >>> 0;
}

function joinUrl(baseUrl: string, fileName: string): string {
  const sanitizedBase = baseUrl.endsWith("/") ? baseUrl.slice(0, -1) : baseUrl;
  return `${sanitizedBase}/${fileName}`;
}

export async function fetchPlanetImageManifest(): Promise<PlanetImageManifest> {
  if (!manifestPromise) {
    manifestPromise = fetch(PLANET_IMAGE_MANIFEST_URL)
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`Planet image manifest request failed: HTTP ${response.status}`);
        }

        const json = (await response.json()) as unknown;
        if (!isPlanetImageManifest(json)) {
          throw new Error("Planet image manifest has an unexpected format");
        }
        return json;
      })
      .catch((error) => {
        manifestPromise = null;
        throw error;
      });
  }

  return manifestPromise;
}

export function getPlanetImageUrl(
  manifest: PlanetImageManifest,
  planetId: string,
): string | null {
  const classes = Object.keys(manifest.imagesByClass).sort();
  if (classes.length === 0) return null;

  const className = classes[hashString(planetId) % classes.length];
  const images = manifest.imagesByClass[className] ?? [];
  if (images.length === 0) return null;

  const imageName = images[hashString(`${planetId}:${className}`) % images.length];
  return joinUrl(manifest.baseUrl, imageName);
}
