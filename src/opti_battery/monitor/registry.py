"""
Spec registry + safety filters for the auto-discovery monitor.

SPECS defines, per "Insane Specification":
  - key            : matches core.research.RESEARCH_FUNCTIONS
  - label          : human label (with emoji) for reports/dashboard
  - metric         : the dict key holding the score in a candidate
  - lower_is_better: sort/compare direction
  - unit           : display unit
"""

SPECS = [
    {
        "key": "charging_speed",
        "label": "⚡ Charging Speed",
        "metric": "min_li_hop_angstrom",
        "lower_is_better": True,
        "unit": "Å hop",
    },
    {
        "key": "capacity",
        "label": "🔋 Capacity",
        "metric": "capacity_proxy_mAh_g",
        "lower_is_better": False,
        "unit": "mAh/g",
    },
    {
        "key": "lifespan",
        "label": "♻️ Lifespan",
        "metric": "formation_energy",
        "lower_is_better": True,   # more negative = more stable
        "unit": "eV/atom",
    },
    {
        "key": "form_factor",
        "label": "📐 Form Factor",
        "metric": "density_g_cm3",
        "lower_is_better": True,
        "unit": "g/cm³",
    },
    {
        "key": "durability",
        "label": "🛡️ Durability",
        "metric": "strength_score",
        "lower_is_better": False,
        "unit": "GPa",
    },
]

SPEC_BY_KEY = {s["key"]: s for s in SPECS}

# Elements to auto-reject: radioactive + acutely toxic heavy metals.
# A "better on one number" candidate is useless if it can't ship — the
# old champions LiThF5 (thorium, radioactive) and NbAs (arsenic) are exactly
# why this filter exists.
RADIOACTIVE = {"Tc", "Po", "At", "Rn", "Ra", "Ac", "Th", "Pa", "U",
               "Np", "Pu", "Am", "Cm", "Bk", "Cf", "Es", "Fm"}
TOXIC_HEAVY = {"As", "Pb", "Cd", "Hg", "Tl", "Be", "Sb"}

BANNED_ELEMENTS = RADIOACTIVE | TOXIC_HEAVY
