import manifestRaw from "../assets/components/manifest.json?raw";

const COMPONENT_IMAGE_BASE_URL = "https://storage.googleapis.com/openstars-assets/components";

type ComponentAssetEntry = {
  image?: string;
};

type ComponentAssetManifest = Record<string, Record<string, ComponentAssetEntry>>;

const componentImageById = flattenManifest(JSON.parse(manifestRaw) as ComponentAssetManifest);

export function getComponentImageUrl(componentId: string): string | null {
  const path = componentImageById.get(componentId);
  if (!path) return null;
  return `${COMPONENT_IMAGE_BASE_URL}/${path}`;
}

function flattenManifest(manifest: ComponentAssetManifest): Map<string, string> {
  const byId = new Map<string, string>();
  for (const group of Object.values(manifest)) {
    for (const [componentId, entry] of Object.entries(group)) {
      if (entry.image) {
        byId.set(componentId, entry.image);
      }
    }
  }
  return byId;
}
