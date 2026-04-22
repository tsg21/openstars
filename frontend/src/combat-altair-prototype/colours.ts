const OWNER_COLOURS: Record<string, string> = {
  alice: "hsl(213 91% 67%)",
  bob: "hsl(0 91% 71%)",
  charlie: "hsl(158 64% 52%)",
  dave: "hsl(43 96% 56%)",
};

const HSL_PATTERN =
  /^hsl\(\s*(-?\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)%\s+(\d+(?:\.\d+)?)%\s*\)$/i;

export function ownerColour(owner: string): string {
  if (owner in OWNER_COLOURS) return OWNER_COLOURS[owner];

  let hash = 0;
  for (let i = 0; i < owner.length; i++) {
    hash = owner.charCodeAt(i) + ((hash << 5) - hash);
  }

  const hue = ((hash % 360) + 360) % 360;
  return `hsl(${hue} 70% 60%)`;
}

export function brightenColour(colour: string, lightnessBoost = 18): string {
  const match = HSL_PATTERN.exec(colour);
  if (!match) return colour;

  const [, hue, saturation, lightness] = match;
  const brighterLightness = Math.min(Number(lightness) + lightnessBoost, 92);
  return `hsl(${hue} ${saturation}% ${brighterLightness}%)`;
}

export function intensifyColour(
  colour: string,
  saturationBoost = 18,
  lightnessBoost = 8,
): string {
  const match = HSL_PATTERN.exec(colour);
  if (!match) return colour;

  const [, hue, saturation, lightness] = match;
  const strongerSaturation = Math.min(Number(saturation) + saturationBoost, 100);
  const strongerLightness = Math.min(Number(lightness) + lightnessBoost, 78);
  return `hsl(${hue} ${strongerSaturation}% ${strongerLightness}%)`;
}

export function ownerBeamColour(owner: string): string {
  return intensifyColour(ownerColour(owner));
}
