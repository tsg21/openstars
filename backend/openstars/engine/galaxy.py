"""Galaxy generation (PRD 02).

Uniform random placement with minimum separation via rejection sampling.
Seeded RNG for deterministic results.
"""

import hashlib
import struct

from openstars.engine.ids import allocate_id
from openstars.engine.models import Galaxy, GalaxyMetadata, GalaxyPlanet

# Galaxy size parameters: bits per axis
GALAXY_SIZES: dict[str, int] = {
    "small": 40,
    "medium": 42,
    "large": 44,
    "huge": 46,
}

# Default planet counts per galaxy size
DEFAULT_PLANET_COUNTS: dict[str, int] = {
    "small": 50,
    "medium": 100,
    "large": 200,
    "huge": 400,
}

# Planet names — a mix of real star names and mythological names
_PLANET_NAMES = [
    "Sol",
    "Alpha Centauri",
    "Sirius",
    "Vega",
    "Procyon",
    "Altair",
    "Rigel",
    "Betelgeuse",
    "Antares",
    "Aldebaran",
    "Polaris",
    "Deneb",
    "Canopus",
    "Arcturus",
    "Capella",
    "Fomalhaut",
    "Regulus",
    "Achernar",
    "Spica",
    "Bellatrix",
    "Castor",
    "Pollux",
    "Mira",
    "Rasalhague",
    "Albireo",
    "Mintaka",
    "Alnilam",
    "Alnitak",
    "Saiph",
    "Elnath",
    "Menkalinan",
    "Dubhe",
    "Merak",
    "Phecda",
    "Megrez",
    "Alioth",
    "Mizar",
    "Alkaid",
    "Thuban",
    "Eltanin",
    "Rastaban",
    "Kochab",
    "Pherkad",
    "Schedar",
    "Caph",
    "Ruchbah",
    "Segin",
    "Achird",
    "Almach",
    "Mirach",
    "Hamal",
    "Sheratan",
    "Mesarthim",
    "Bharani",
    "Botein",
    "Menkar",
    "Mira Ceti",
    "Cursa",
    "Rigel Kent",
    "Hadar",
    "Mimosa",
    "Gacrux",
    "Acrux",
    "Atria",
    "Peacock",
    "Alnair",
    "Ankaa",
    "Diphda",
    "Sadalmelik",
    "Sadalsuud",
    "Markab",
    "Scheat",
    "Algenib",
    "Enif",
    "Biham",
    "Sadachbia",
    "Nashira",
    "Skat",
    "Deneb Algedi",
    "Grumium",
    "Alderamin",
    "Errai",
    "Alfirk",
    "Kurhah",
    "Sadr",
    "Gienah",
    "Algorab",
    "Kraz",
    "Minkar",
    "Alchiba",
    "Cor Caroli",
    "Vindemiatrix",
    "Zaniah",
    "Porrima",
    "Auva",
    "Heze",
    "Zubenelgenubi",
    "Zubeneschamali",
    "Dschubba",
    "Acrab",
    "Yed Prior",
    "Yed Posterior",
    "Sabik",
    "Rasalgethi",
    "Kornephoros",
    "Marfik",
    "Cebalrai",
    "Unukalhai",
    "Alya",
    "Nunki",
    "Kaus Australis",
    "Kaus Media",
    "Kaus Borealis",
    "Ascella",
    "Albaldah",
    "Rukbat",
    "Dabih",
    "Algedi",
    "Giedi",
    "Sadalbaari",
    "Tarazed",
    "Alshain",
    "Tseen Ke",
    "Okab",
    "Wezen",
    "Adhara",
    "Furud",
    "Aludra",
    "Muliphein",
    "Naos",
    "Regor",
    "Suhail",
    "Markeb",
    "Avior",
    "Aspidiske",
    "Tureis",
    "Alsephina",
    "Miaplacidus",
    "Theta Carinae",
    "Eta Carinae",
    "Koo She",
    "Muscida",
    "Tania Borealis",
    "Tania Australis",
    "Talitha",
    "Alula Borealis",
    "Alula Australis",
    "Praecipua",
    "Tegmine",
    "Acubens",
    "Asellus Borealis",
    "Asellus Australis",
    "Alterf",
    "Subra",
    "Chertan",
    "Zosma",
    "Coxa",
    "Denebola",
    "Muphrid",
    "Izar",
    "Seginus",
    "Nekkar",
    "Merga",
    "Alphecca",
    "Gemma",
    "Nusakan",
    "Kitalpha",
    "Sarin",
    "Maasym",
    "Sheliak",
    "Sulafat",
    "Aladfar",
    "Rotanev",
    "Sualocin",
    "Musica",
    "Anser",
    "Sagitta",
    "Albali",
    "Sadalund",
    "Bunda",
    "Situla",
    "Sadaltager",
    "Alrescha",
    "Torcular",
    "Fumalsamakah",
    "Vernalis",
    "Revati",
    "Baten Kaitos",
    "Kaffaljidhma",
    "Azha",
    "Acamar",
    "Zaurak",
    "Rana",
    "Arneb",
    "Nihal",
    "Gomeisa",
    "Wasat",
    "Mebsuta",
    "Propus",
    "Tejat",
    "Alhena",
    "Mekbuda",
    "Alzirr",
    "Phact",
    "Wazn",
    "Ain",
    "Hyadum",
    "Chamukuy",
    "Prima Hyadum",
    "Secunda Hyadum",
    "Tianguan",
    "Nath",
    "Hassaleh",
    "Hoedus",
    "Saclateni",
]


class _SeededRNG:
    """Simple seeded PRNG using SHA-256 as a counter-mode generator.

    Deterministic and platform-independent.
    """

    def __init__(self, seed: int) -> None:
        self._seed = seed
        self._counter = 0

    def next_int(self, upper: int) -> int:
        """Return a random integer in [0, upper)."""
        while True:
            data = struct.pack(">QQ", self._seed, self._counter)
            digest = hashlib.sha256(data).digest()
            self._counter += 1
            val = struct.unpack(">Q", digest[:8])[0]
            # Rejection sampling to avoid modulo bias
            limit = (2**64 // upper) * upper
            if val < limit:
                return val % upper

    def shuffle(self, lst: list) -> None:
        """Fisher-Yates shuffle in-place."""
        for i in range(len(lst) - 1, 0, -1):
            j = self.next_int(i + 1)
            lst[i], lst[j] = lst[j], lst[i]


def _isqrt(n: int) -> int:
    """Integer square root — largest r such that r² ≤ n."""
    if n < 0:
        raise ValueError("isqrt requires non-negative input")
    if n == 0:
        return 0
    x = n
    y = (x + 1) // 2
    while y < x:
        x = y
        y = (x + n // x) // 2
    return x


def generate_galaxy(
    name: str,
    size: str,
    seed: int,
    num_planets: int | None = None,
) -> Galaxy:
    """Generate a galaxy with seeded deterministic placement.

    Args:
        name: Galaxy display name.
        size: One of "small", "medium", "large", "huge".
        seed: Galaxy seed for deterministic generation.
        num_planets: Number of planets (defaults per size if None).

    Returns:
        Galaxy model with metadata and planet list.
    """
    if size not in GALAXY_SIZES:
        raise ValueError(f"Invalid galaxy size: {size!r}")

    bits = GALAXY_SIZES[size]
    max_coord = (1 << bits) - 1
    if num_planets is None:
        num_planets = DEFAULT_PLANET_COUNTS[size]

    rng = _SeededRNG(seed)

    # Placement region: middle 50% of the coordinate space
    region_min = max_coord // 4
    region_max = max_coord * 3 // 4
    region_size = region_max - region_min

    # Minimum separation: ~0.5% of axis range in coordinate units
    # PRD 02 suggests this produces reasonable spacing
    min_sep = max_coord // 200
    min_sep_sq = min_sep * min_sep

    # Generate planet names — shuffle a copy of the name list
    names = list(_PLANET_NAMES[: max(num_planets, len(_PLANET_NAMES))])
    rng.shuffle(names)
    # If we need more names than the list, generate numbered ones
    while len(names) < num_planets:
        names.append(f"Planet-{len(names) + 1}")

    # Place planets via rejection sampling
    placed: list[tuple[int, int]] = []
    next_id = 0
    planets: list[GalaxyPlanet] = []
    max_attempts = num_planets * 1000  # Safety valve
    attempts = 0

    while len(placed) < num_planets and attempts < max_attempts:
        x = region_min + rng.next_int(region_size)
        y = region_min + rng.next_int(region_size)
        attempts += 1

        # Check minimum separation from all placed planets
        too_close = False
        for px, py in placed:
            dx = x - px
            dy = y - py
            if dx * dx + dy * dy < min_sep_sq:
                too_close = True
                break

        if too_close:
            continue

        # Accept this planet
        planet_id, next_id = allocate_id(next_id, seed, "PL")
        planet_name = names[len(placed)]
        planets.append(GalaxyPlanet(id=planet_id, name=planet_name, x=x, y=y))
        placed.append((x, y))

    if len(placed) < num_planets:
        raise RuntimeError(
            f"Could only place {len(placed)}/{num_planets} planets after {max_attempts} attempts"
        )

    return Galaxy(
        galaxy=GalaxyMetadata(name=name, size=size, seed=seed),
        planets=planets,
    )
