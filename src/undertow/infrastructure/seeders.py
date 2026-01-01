"""
Database seeders for initial data.

Provides initial data for zones, sources, and configuration.
"""

import structlog
from uuid import uuid4
from datetime import datetime
from typing import Any

logger = structlog.get_logger(__name__)


# ============================================================================
# Zone Data
# ============================================================================

ZONES_DATA = [
    # Europe
    {"id": "western_europe", "name": "Western Europe (Core EU)", "region": "europe", 
     "countries": ["France", "Germany", "Belgium", "Netherlands", "Luxembourg", "Austria", "Switzerland"],
     "key_dynamics": ["Franco-German axis", "EU institutional evolution", "Energy transition", "Immigration politics"]},
    {"id": "southern_europe", "name": "Southern Europe (Mediterranean EU)", "region": "europe",
     "countries": ["Italy", "Spain", "Portugal", "Greece", "Cyprus", "Malta"],
     "key_dynamics": ["Debt sustainability", "Mediterranean migration", "Eastern Med gas", "Tourism-climate"]},
    {"id": "nordic_baltic", "name": "Nordic-Baltic Region", "region": "europe",
     "countries": ["Sweden", "Norway", "Denmark", "Finland", "Iceland", "Estonia", "Latvia", "Lithuania"],
     "key_dynamics": ["NATO expansion", "Arctic defense", "Baltic vulnerability", "Nordic leadership"]},
    {"id": "british_isles", "name": "British Isles", "region": "europe",
     "countries": ["United Kingdom", "Ireland"],
     "key_dynamics": ["Post-Brexit positioning", "Northern Ireland", "Scottish independence", "AUKUS"]},
    {"id": "central_europe", "name": "Central Europe (Visegrád+)", "region": "europe",
     "countries": ["Poland", "Czech Republic", "Slovakia", "Hungary", "Slovenia"],
     "key_dynamics": ["Democratic backsliding", "Ukraine front-line", "Energy security", "Memory politics"]},
    {"id": "western_balkans", "name": "Western Balkans", "region": "europe",
     "countries": ["Serbia", "Kosovo", "Bosnia-Herzegovina", "North Macedonia", "Albania", "Montenegro"],
     "key_dynamics": ["EU accession stalled", "Serbia-Kosovo", "Chinese/Russian influence", "State capture"]},
    {"id": "eastern_europe", "name": "Eastern Europe (Non-EU)", "region": "europe",
     "countries": ["Ukraine", "Moldova", "Belarus"],
     "key_dynamics": ["Ukraine war", "Moldova EU aspirations", "Belarus-Russia integration"]},
    {"id": "south_caucasus", "name": "South Caucasus", "region": "europe",
     "countries": ["Georgia", "Armenia", "Azerbaijan"],
     "key_dynamics": ["Armenia-Azerbaijan dynamics", "Georgia EU aspirations", "Zangezur corridor"]},
    
    # Russia & Eurasia
    {"id": "russia_core", "name": "Russian Federation", "region": "russia_eurasia",
     "countries": ["Russia"],
     "key_dynamics": ["War economy", "Succession questions", "China relationship", "Regional dynamics"]},
    {"id": "central_asia_west", "name": "Central Asia (Western)", "region": "russia_eurasia",
     "countries": ["Kazakhstan", "Uzbekistan", "Turkmenistan"],
     "key_dynamics": ["Post-Karimov opening", "Kazakhstan balancing", "Water politics", "BRI debt"]},
    {"id": "central_asia_east", "name": "Central Asia (Eastern)", "region": "russia_eurasia",
     "countries": ["Kyrgyzstan", "Tajikistan"],
     "key_dynamics": ["Fragile states", "Afghanistan spillover", "Russian military presence", "Remittances"]},
    
    # Middle East & North Africa
    {"id": "levant", "name": "Levant", "region": "mena",
     "countries": ["Syria", "Lebanon", "Jordan", "Palestinian Territories"],
     "key_dynamics": ["Post-Assad Syria", "Lebanon collapse", "Jordan stability", "Palestine division"]},
    {"id": "gulf_gcc", "name": "Gulf Cooperation Council", "region": "mena",
     "countries": ["Saudi Arabia", "UAE", "Qatar", "Kuwait", "Bahrain", "Oman"],
     "key_dynamics": ["Vision 2030", "UAE power broker", "Post-oil transition", "Gulf-Iran dynamics"]},
    {"id": "iraq", "name": "Iraq", "region": "mena",
     "countries": ["Iraq", "Kurdistan Region"],
     "key_dynamics": ["Post-ISIS rebuilding", "Iran influence", "Kurdistan divisions", "Water scarcity"]},
    {"id": "iran", "name": "Iran", "region": "mena",
     "countries": ["Iran"],
     "key_dynamics": ["Succession", "Nuclear program", "Proxy network", "IRGC dominance"]},
    {"id": "turkey", "name": "Turkey", "region": "mena",
     "countries": ["Turkey"],
     "key_dynamics": ["Erdoğan longevity", "Economic crisis", "Kurdish question", "Blue Homeland"]},
    {"id": "maghreb", "name": "Maghreb", "region": "mena",
     "countries": ["Morocco", "Algeria", "Tunisia", "Libya"],
     "key_dynamics": ["Morocco-Algeria cold war", "Tunisia backsliding", "Libya fragmentation"]},
    {"id": "egypt", "name": "Egypt", "region": "mena",
     "countries": ["Egypt"],
     "key_dynamics": ["Sisi consolidation", "GERD dispute", "IMF dependency", "Military economy"]},
    
    # Sub-Saharan Africa
    {"id": "horn_of_africa", "name": "Horn of Africa", "region": "africa",
     "countries": ["Ethiopia", "Eritrea", "Djibouti", "Somalia", "Somaliland"],
     "key_dynamics": ["Post-Tigray Ethiopia", "Red Sea security", "Somaliland recognition", "Base competition"]},
    {"id": "east_africa", "name": "East Africa", "region": "africa",
     "countries": ["Kenya", "Uganda", "Tanzania", "Rwanda", "Burundi"],
     "key_dynamics": ["Kenya regional anchor", "Rwanda authoritarianism", "DRC intervention", "EAC dynamics"]},
    {"id": "great_lakes", "name": "Great Lakes & Central Africa", "region": "africa",
     "countries": ["DRC", "CAR", "Republic of Congo", "Gabon", "Cameroon", "Chad", "Equatorial Guinea"],
     "key_dynamics": ["DRC minerals", "Wagner presence", "Critical minerals", "Regional spillover"]},
    {"id": "sahel", "name": "Sahel", "region": "africa",
     "countries": ["Mali", "Niger", "Burkina Faso", "Mauritania"],
     "key_dynamics": ["Military juntas", "France expulsion", "Jihadist insurgencies", "Climate-conflict"]},
    {"id": "west_africa_coastal", "name": "West Africa (Coastal)", "region": "africa",
     "countries": ["Nigeria", "Ghana", "Côte d'Ivoire", "Senegal", "others"],
     "key_dynamics": ["Nigeria reforms", "ECOWAS strains", "Democratic exceptions", "Gulf of Guinea"]},
    {"id": "southern_africa", "name": "Southern Africa", "region": "africa",
     "countries": ["South Africa", "Zimbabwe", "Mozambique", "Zambia", "Angola", "others"],
     "key_dynamics": ["ANC decline", "Mozambique LNG", "Zambia debt restructuring", "Regional stability"]},
    
    # South Asia
    {"id": "india", "name": "India", "region": "south_asia",
     "countries": ["India"],
     "key_dynamics": ["BJP trajectory", "India-China competition", "Global South leadership", "Defense modernization"]},
    {"id": "pakistan_afghanistan", "name": "Pakistan & Afghanistan", "region": "south_asia",
     "countries": ["Pakistan", "Afghanistan"],
     "key_dynamics": ["Military-civilian dynamics", "Taliban 2.0", "TTP resurgence", "CPEC debt"]},
    {"id": "south_asian_periphery", "name": "South Asian Periphery", "region": "south_asia",
     "countries": ["Bangladesh", "Sri Lanka", "Nepal", "Bhutan", "Maldives"],
     "key_dynamics": ["Bangladesh transition", "Sri Lanka recovery", "India-China competition"]},
    
    # East Asia
    {"id": "china", "name": "China", "region": "east_asia",
     "countries": ["China", "Hong Kong", "Macau"],
     "key_dynamics": ["Xi consolidation", "Economic slowdown", "Tech sector", "Taiwan contingency"]},
    {"id": "taiwan", "name": "Taiwan", "region": "east_asia",
     "countries": ["Taiwan"],
     "key_dynamics": ["Cross-strait relations", "Semiconductor dominance", "US defense commitment"]},
    {"id": "korea", "name": "Korean Peninsula", "region": "east_asia",
     "countries": ["South Korea", "North Korea"],
     "key_dynamics": ["DPRK nuclear", "ROK polarization", "Russia military ties", "Inter-Korean frozen"]},
    {"id": "japan", "name": "Japan", "region": "east_asia",
     "countries": ["Japan"],
     "key_dynamics": ["Security transformation", "Demographic crisis", "China decoupling", "US alliance"]},
    {"id": "mongolia", "name": "Mongolia", "region": "east_asia",
     "countries": ["Mongolia"],
     "key_dynamics": ["Third neighbor balancing", "Mining dependency", "Democratic outlier"]},
    
    # Southeast Asia
    {"id": "mainland_sea", "name": "Mainland Southeast Asia", "region": "southeast_asia",
     "countries": ["Vietnam", "Thailand", "Cambodia", "Laos", "Myanmar"],
     "key_dynamics": ["Vietnam manufacturing", "Myanmar civil war", "Mekong politics", "BRI debt"]},
    {"id": "maritime_sea", "name": "Maritime Southeast Asia", "region": "southeast_asia",
     "countries": ["Indonesia", "Philippines", "Malaysia", "Singapore", "Brunei", "Timor-Leste"],
     "key_dynamics": ["South China Sea", "Indonesia nickel", "Philippines assertiveness", "Malacca Strait"]},
    
    # Oceania & Pacific
    {"id": "australia_nz", "name": "Australia & New Zealand", "region": "oceania",
     "countries": ["Australia", "New Zealand"],
     "key_dynamics": ["AUKUS", "China reset", "Critical minerals", "Pacific competition"]},
    {"id": "pacific_islands", "name": "Pacific Islands", "region": "oceania",
     "countries": ["Fiji", "Papua New Guinea", "Solomon Islands", "others"],
     "key_dynamics": ["US-China competition", "Climate existential", "Deep-sea mining", "PIF dynamics"]},
    
    # Americas
    {"id": "usa", "name": "United States", "region": "americas",
     "countries": ["United States"],
     "key_dynamics": ["Grand strategy debates", "China competition", "Alliance management", "Polarization"]},
    {"id": "canada", "name": "Canada", "region": "americas",
     "countries": ["Canada"],
     "key_dynamics": ["US relationship", "Arctic sovereignty", "China deterioration", "Immigration"]},
    {"id": "mexico_central_america", "name": "Mexico & Central America", "region": "americas",
     "countries": ["Mexico", "Guatemala", "Honduras", "El Salvador", "Nicaragua", "Costa Rica", "Panama", "Belize"],
     "key_dynamics": ["Nearshoring", "Migration drivers", "Bukele model", "Panama Canal"]},
    {"id": "caribbean", "name": "Caribbean", "region": "americas",
     "countries": ["Cuba", "Haiti", "Dominican Republic", "Jamaica", "Trinidad and Tobago", "others"],
     "key_dynamics": ["Haiti collapse", "Cuba stagnation", "Climate vulnerability", "Offshore finance"]},
    {"id": "andean", "name": "Andean Region", "region": "americas",
     "countries": ["Colombia", "Venezuela", "Ecuador", "Peru", "Bolivia"],
     "key_dynamics": ["Venezuela migration", "Colombia peace", "Ecuador security", "Lithium"]},
    {"id": "southern_cone", "name": "Southern Cone", "region": "americas",
     "countries": ["Brazil", "Argentina", "Chile", "Uruguay", "Paraguay"],
     "key_dynamics": ["Brazil BRICS", "Argentina shock therapy", "Lithium triangle", "Amazon"]},
]


# ============================================================================
# Theme Data
# ============================================================================

THEMES_DATA = [
    {"id": "security", "name": "Security & Defense", "category": "hard_power"},
    {"id": "diplomacy", "name": "Diplomacy & Recognition", "category": "soft_power"},
    {"id": "economics", "name": "Economics & Trade", "category": "economic"},
    {"id": "energy", "name": "Energy & Resources", "category": "economic"},
    {"id": "climate", "name": "Climate & Environment", "category": "transnational"},
    {"id": "migration", "name": "Migration & Demographics", "category": "transnational"},
    {"id": "technology", "name": "Technology & Cyber", "category": "emerging"},
    {"id": "governance", "name": "Governance & Democracy", "category": "political"},
    {"id": "conflict", "name": "Conflict & Violence", "category": "security"},
    {"id": "maritime", "name": "Maritime & Naval", "category": "strategic"},
    {"id": "intelligence", "name": "Intelligence & Espionage", "category": "security"},
    {"id": "finance", "name": "Finance & Debt", "category": "economic"},
    {"id": "infrastructure", "name": "Infrastructure & Development", "category": "economic"},
    {"id": "nuclear", "name": "Nuclear & WMD", "category": "security"},
    {"id": "space", "name": "Space & Satellites", "category": "emerging"},
]


# ============================================================================
# Seeder Functions
# ============================================================================

async def seed_zones(session) -> int:
    """Seed zone data into database."""
    from undertow.models.zone import Zone
    
    count = 0
    for zone_data in ZONES_DATA:
        existing = await session.execute(
            f"SELECT id FROM zones WHERE id = '{zone_data['id']}'"
        )
        if not existing.scalar():
            zone = Zone(
                id=zone_data["id"],
                name=zone_data["name"],
                region=zone_data["region"],
                countries=zone_data["countries"],
                key_dynamics=zone_data["key_dynamics"],
            )
            session.add(zone)
            count += 1
    
    await session.commit()
    logger.info("zones_seeded", count=count)
    return count


async def seed_themes(session) -> int:
    """Seed theme data into database."""
    from undertow.models.theme import Theme
    
    count = 0
    for theme_data in THEMES_DATA:
        existing = await session.execute(
            f"SELECT id FROM themes WHERE id = '{theme_data['id']}'"
        )
        if not existing.scalar():
            theme = Theme(
                id=theme_data["id"],
                name=theme_data["name"],
                category=theme_data["category"],
            )
            session.add(theme)
            count += 1
    
    await session.commit()
    logger.info("themes_seeded", count=count)
    return count


async def seed_sample_sources(session) -> int:
    """Seed sample source configurations."""
    from undertow.models.source import Source
    
    sample_sources = [
        {
            "id": str(uuid4()),
            "name": "Financial Times",
            "domain": "ft.com",
            "type": "news",
            "tier": 1,
            "zones": ["western_europe", "china", "usa"],
            "feed_url": "https://www.ft.com/rss/home",
        },
        {
            "id": str(uuid4()),
            "name": "Africa Confidential",
            "domain": "africa-confidential.com",
            "type": "analysis",
            "tier": 1,
            "zones": ["horn_of_africa", "east_africa", "west_africa_coastal", "sahel", "southern_africa"],
            "feed_url": None,
        },
        {
            "id": str(uuid4()),
            "name": "Al-Monitor",
            "domain": "al-monitor.com",
            "type": "news",
            "tier": 1,
            "zones": ["levant", "gulf_gcc", "turkey", "iran", "iraq"],
            "feed_url": "https://www.al-monitor.com/rss",
        },
        {
            "id": str(uuid4()),
            "name": "Nikkei Asia",
            "domain": "asia.nikkei.com",
            "type": "news",
            "tier": 1,
            "zones": ["japan", "china", "korea", "mainland_sea", "maritime_sea"],
            "feed_url": "https://asia.nikkei.com/rss",
        },
        {
            "id": str(uuid4()),
            "name": "Crisis Group",
            "domain": "crisisgroup.org",
            "type": "analysis",
            "tier": 1,
            "zones": ["global"],
            "feed_url": "https://www.crisisgroup.org/rss.xml",
        },
    ]
    
    count = 0
    for source_data in sample_sources:
        existing = await session.execute(
            f"SELECT id FROM sources WHERE domain = '{source_data['domain']}'"
        )
        if not existing.scalar():
            source = Source(**source_data)
            session.add(source)
            count += 1
    
    await session.commit()
    logger.info("sources_seeded", count=count)
    return count


async def seed_all(session) -> dict[str, int]:
    """Run all seeders."""
    results = {
        "zones": await seed_zones(session),
        "themes": await seed_themes(session),
        "sources": await seed_sample_sources(session),
    }
    
    logger.info("seeding_complete", **results)
    return results


def get_zone_by_id(zone_id: str) -> dict[str, Any] | None:
    """Get zone data by ID without database."""
    for zone in ZONES_DATA:
        if zone["id"] == zone_id:
            return zone
    return None


def get_all_zones() -> list[dict[str, Any]]:
    """Get all zone data without database."""
    return ZONES_DATA


def get_zones_by_region(region: str) -> list[dict[str, Any]]:
    """Get zones filtered by region."""
    return [z for z in ZONES_DATA if z["region"] == region]


def get_all_themes() -> list[dict[str, Any]]:
    """Get all theme data without database."""
    return THEMES_DATA

