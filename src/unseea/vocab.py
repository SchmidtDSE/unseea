"""Controlled vocabularies.

SEEA fixes these, so they are library artifacts rather than application config
(`ARCHITECTURE.md`, the filing rule). Three of them:

* **Ecosystem types** — the ET partition of the accounting area. SEEALand uses six national
  types; a real compilation uses IUCN GET Ecosystem Functional Groups (issue #5). The alias
  table exists because the SEEALand workbook itself is inconsistent ("Urban area" in the
  condition sheets, "Urban areas" in the extent account).
* **ECT classes** — the SEEA Ecosystem Condition Typology (Table 5.1): six classes in three
  groups. Weighting is one equal vote per class *present*, so the class of a variable is
  load-bearing arithmetic, not a label (`DESIGN.md` §2.4).
* **Selected ecosystem services** — the reference list (Table 6.3), restricted here to the six
  services SEEALand supplies.
"""

from __future__ import annotations

from dataclasses import dataclass

# --------------------------------------------------------------------------------------
# Ecosystem types
# --------------------------------------------------------------------------------------

#: Canonical ET labels in SEEALand presentation order.
ECOSYSTEM_TYPES: tuple[str, ...] = (
    "Forest",
    "Lake",
    "Cropland",
    "Urban area",
    "Wetland",
    "Seagrass",
)

#: Spellings that appear in the workbook for the same ET.
ET_ALIASES: dict[str, str] = {
    "urban areas": "Urban area",
    "urban area": "Urban area",
}


def canonical_et(label: str) -> str:
    """Return the canonical ET label for one of its spellings."""
    key = " ".join(label.split()).strip()
    resolved = ET_ALIASES.get(key.lower(), key)
    if resolved not in ECOSYSTEM_TYPES:
        raise KeyError(f"unknown ecosystem type: {label!r}")
    return resolved


# --------------------------------------------------------------------------------------
# Ecosystem Condition Typology (ECT)
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class ECTClass:
    code: str
    group: str
    name: str


ECT_CLASSES: tuple[ECTClass, ...] = (
    ECTClass("A1", "Abiotic characteristics", "Physical state"),
    ECTClass("A2", "Abiotic characteristics", "Chemical state"),
    ECTClass("B1", "Biotic characteristics", "Compositional state"),
    ECTClass("B2", "Biotic characteristics", "Structural state"),
    ECTClass("B3", "Biotic characteristics", "Functional state"),
    ECTClass("C1", "Landscape/seascape characteristics", "Landscape/seascape"),
)

_ECT_BY_GROUP_CLASS = {(c.group, c.name): c for c in ECT_CLASSES}
ECT_BY_CODE = {c.code: c for c in ECT_CLASSES}

#: ECT group order, used for the sub-index rows of the condition index account.
ECT_GROUPS: tuple[str, ...] = (
    "Abiotic characteristics",
    "Biotic characteristics",
    "Landscape/seascape characteristics",
)


def ect_class(group: str, name: str | None) -> ECTClass:
    """Resolve an ECT class from its group and class name.

    The landscape/seascape group has a single class and the workbook leaves its class cell
    blank, so an empty name resolves to C1.
    """
    group = " ".join(group.split()).strip()
    name = " ".join((name or "").split()).strip()
    if group.startswith("Landscape"):
        return ECT_BY_CODE["C1"]
    try:
        return _ECT_BY_GROUP_CLASS[(group, name)]
    except KeyError:
        raise KeyError(f"unknown ECT class: {group!r} / {name!r}") from None


# --------------------------------------------------------------------------------------
# Selected ecosystem services (Table 6.3)
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Service:
    id: str
    label: str  #: reference-list name, as used in the supply-and-use tables
    section: str  #: provisioning / regulating and maintenance / cultural
    unit: str
    aliases: tuple[str, ...] = ()


SERVICES: tuple[Service, ...] = (
    Service(
        "crop_provisioning",
        "Crop provisioning services",
        "Provisioning services",
        "tonnes",
        ("crop provisioning",),
    ),
    Service(
        "wood_provisioning",
        "Wood provisioning services",
        "Provisioning services",
        "m3",
        ("wood provisioning",),
    ),
    Service(
        "wild_fish_provisioning",
        "Wild fish and other natural aquatic biomass provisioning services",
        "Provisioning services",
        "tonnes",
        ("wild fish biomass provisioning", "wild fish provisioning"),
    ),
    Service(
        "global_climate_regulation",
        "Global climate regulation services",
        "Regulating and maintenance services",
        "tonnes CO2",
        ("global climate regulation",),
    ),
    Service(
        "water_purification",
        "Water purification services",
        "Regulating and maintenance services",
        "tonnes N removed",
        ("water purification",),
    ),
    Service(
        "recreation",
        "Recreation-related services",
        "Cultural services",
        "# visits",
        ("recreation related", "recreation-related"),
    ),
)

SERVICE_BY_ID = {s.id: s for s in SERVICES}

_SERVICE_BY_NAME: dict[str, Service] = {}
for _s in SERVICES:
    _SERVICE_BY_NAME[_s.label.lower()] = _s
    _SERVICE_BY_NAME[_s.id] = _s
    for _a in _s.aliases:
        _SERVICE_BY_NAME[_a] = _s

#: Section order for supply-and-use table presentation.
SERVICE_SECTIONS: tuple[str, ...] = (
    "Provisioning services",
    "Regulating and maintenance services",
    "Cultural services",
)


def canonical_service(label: str) -> Service:
    """Resolve a service from any of the spellings used across the workbook sheets."""
    key = " ".join(label.split()).strip().lower()
    try:
        return _SERVICE_BY_NAME[key]
    except KeyError:
        raise KeyError(f"unknown ecosystem service: {label!r}") from None


# --------------------------------------------------------------------------------------
# Economic units on the use side
# --------------------------------------------------------------------------------------

#: Use-side counterparty kinds, keyed by the user labels SEEALand uses.
USER_KINDS: dict[str, str] = {
    "Agriculture": "industry",
    "Forestry": "industry",
    "Fisheries": "industry",
    "Energy & water supply": "industry",
    "Government": "government",
    "Households": "household",
}
