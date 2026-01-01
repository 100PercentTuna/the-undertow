"""
Zone management API routes.

Provides information about the 42 global coverage zones.
"""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from undertow.models.story import Zone

router = APIRouter(prefix="/zones", tags=["Zones"])


# Zone metadata - matches THE_UNDERTOW.md
ZONE_METADATA: dict[str, dict[str, Any]] = {
    "western_europe": {
        "name": "Western Europe (Core EU)",
        "region": "Europe",
        "countries": ["France", "Germany", "Benelux", "Austria", "Switzerland"],
        "key_dynamics": [
            "Franco-German axis mechanics",
            "Industrial policy and energy transition",
            "Immigration and far-right politics",
            "EU institutional evolution",
        ],
    },
    "southern_europe": {
        "name": "Southern Europe (Mediterranean EU)",
        "region": "Europe",
        "countries": ["Italy", "Spain", "Portugal", "Greece", "Cyprus", "Malta"],
        "key_dynamics": [
            "Debt sustainability and EU fiscal politics",
            "Mediterranean migration corridor",
            "Eastern Mediterranean gas disputes",
        ],
    },
    "nordic_baltic": {
        "name": "Nordic-Baltic Region",
        "region": "Europe",
        "countries": ["Sweden", "Norway", "Denmark", "Finland", "Iceland", "Estonia", "Latvia", "Lithuania"],
        "key_dynamics": [
            "NATO's northern expansion",
            "Russian threat perception",
            "Baltic vulnerability (Suwalki Gap)",
            "Arctic governance",
        ],
    },
    "british_isles": {
        "name": "British Isles",
        "region": "Europe",
        "countries": ["United Kingdom", "Ireland"],
        "key_dynamics": [
            "Post-Brexit repositioning",
            "UK-EU relationship",
            "Scottish independence trajectory",
            "Irish unification debate",
        ],
    },
    "central_europe": {
        "name": "Central Europe (Visegrád+)",
        "region": "Europe",
        "countries": ["Poland", "Czech Republic", "Slovakia", "Hungary", "Slovenia"],
        "key_dynamics": [
            "Democratic backsliding",
            "Ukraine front-line dynamics",
            "German industrial supply chain integration",
        ],
    },
    "western_balkans": {
        "name": "Western Balkans",
        "region": "Europe",
        "countries": ["Serbia", "Kosovo", "Bosnia-Herzegovina", "North Macedonia", "Albania", "Montenegro"],
        "key_dynamics": [
            "EU accession (stalled)",
            "Serbia-Kosovo normalization",
            "Bosnia's constitutional dysfunction",
            "Chinese and Russian influence",
        ],
    },
    "eastern_europe": {
        "name": "Eastern Europe (Non-EU)",
        "region": "Europe",
        "countries": ["Ukraine", "Moldova", "Belarus"],
        "key_dynamics": [
            "Ukraine war",
            "Moldova (Transnistria, EU accession)",
            "Belarus (Russian integration)",
        ],
    },
    "south_caucasus": {
        "name": "South Caucasus",
        "region": "Europe",
        "countries": ["Georgia", "Armenia", "Azerbaijan"],
        "key_dynamics": [
            "Post-2020 Armenia-Azerbaijan dynamics",
            "Georgia's EU aspirations",
            "Zangezur corridor politics",
            "Energy transit to Europe",
        ],
    },
    "russia_core": {
        "name": "Russian Federation",
        "region": "Russia & Eurasia",
        "countries": ["Russia"],
        "key_dynamics": [
            "War economy sustainability",
            "Domestic stability and succession",
            "China relationship",
            "Regional dynamics",
        ],
    },
    "central_asia_west": {
        "name": "Central Asia (Western)",
        "region": "Russia & Eurasia",
        "countries": ["Kazakhstan", "Uzbekistan", "Turkmenistan"],
        "key_dynamics": [
            "Post-Karimov Uzbekistan opening",
            "Kazakhstan's balancing act",
            "BRI presence and debt",
            "Russian influence erosion",
        ],
    },
    "central_asia_east": {
        "name": "Central Asia (Eastern)",
        "region": "Russia & Eurasia",
        "countries": ["Kyrgyzstan", "Tajikistan"],
        "key_dynamics": [
            "Fragile state dynamics",
            "Border conflicts",
            "Afghanistan spillover",
            "Russian military presence",
        ],
    },
    "levant": {
        "name": "Levant",
        "region": "Middle East & North Africa",
        "countries": ["Syria", "Lebanon", "Jordan", "Palestinian Territories"],
        "key_dynamics": [
            "Syria fragmentation",
            "Lebanon state collapse",
            "Palestine (occupation, internal division)",
        ],
    },
    "gulf_gcc": {
        "name": "Gulf Cooperation Council",
        "region": "Middle East & North Africa",
        "countries": ["Saudi Arabia", "UAE", "Qatar", "Kuwait", "Bahrain", "Oman"],
        "key_dynamics": [
            "Saudi Vision 2030",
            "UAE as regional power broker",
            "Post-oil transition",
            "Gulf-Iran dynamics",
        ],
    },
    "iraq": {
        "name": "Iraq",
        "region": "Middle East & North Africa",
        "countries": ["Iraq", "Kurdistan Region"],
        "key_dynamics": [
            "Post-ISIS state rebuilding",
            "Iran influence",
            "Kurdistan Region internal divisions",
        ],
    },
    "iran": {
        "name": "Iran",
        "region": "Middle East & North Africa",
        "countries": ["Iran"],
        "key_dynamics": [
            "Post-Khamenei succession",
            "Nuclear program",
            "Regional proxy network",
            "Economic crisis",
        ],
    },
    "turkey": {
        "name": "Turkey",
        "region": "Middle East & North Africa",
        "countries": ["Turkey"],
        "key_dynamics": [
            "Erdoğan longevity",
            "Economic crisis",
            "Kurdish question",
            "NATO membership with independent foreign policy",
        ],
    },
    "maghreb": {
        "name": "Maghreb",
        "region": "Middle East & North Africa",
        "countries": ["Morocco", "Algeria", "Tunisia", "Libya"],
        "key_dynamics": [
            "Morocco-Algeria cold war",
            "Tunisia democratic backsliding",
            "Libya fragmentation",
            "Migration to Europe",
        ],
    },
    "egypt": {
        "name": "Egypt",
        "region": "Middle East & North Africa",
        "countries": ["Egypt"],
        "key_dynamics": [
            "Sisi consolidation",
            "Economic crisis",
            "Nile water (GERD dispute)",
            "Regional mediation role",
        ],
    },
    "horn_of_africa": {
        "name": "Horn of Africa",
        "region": "Sub-Saharan Africa",
        "countries": ["Ethiopia", "Eritrea", "Djibouti", "Somalia", "Somaliland"],
        "key_dynamics": [
            "Post-Tigray Ethiopia",
            "Somalia (Al-Shabaab, clan federalism)",
            "Somaliland de facto independence",
            "Red Sea security",
        ],
    },
    "east_africa": {
        "name": "East Africa",
        "region": "Sub-Saharan Africa",
        "countries": ["Kenya", "Uganda", "Tanzania", "Rwanda", "Burundi"],
        "key_dynamics": [
            "Kenya as regional anchor",
            "Rwanda's developmental authoritarianism",
            "DRC intervention",
        ],
    },
    "great_lakes": {
        "name": "Great Lakes & Central Africa",
        "region": "Sub-Saharan Africa",
        "countries": ["DRC", "CAR", "Republic of Congo", "Gabon", "Cameroon", "Chad", "Equatorial Guinea"],
        "key_dynamics": [
            "DRC (M23, minerals)",
            "CAR (Wagner/Russian influence)",
            "Critical minerals",
        ],
    },
    "sahel": {
        "name": "Sahel",
        "region": "Sub-Saharan Africa",
        "countries": ["Mali", "Niger", "Burkina Faso", "Mauritania"],
        "key_dynamics": [
            "Military junta belt",
            "France expulsion and Russia pivot",
            "Jihadist insurgencies",
            "Climate-conflict nexus",
        ],
    },
    "west_africa": {
        "name": "West Africa (Coastal)",
        "region": "Sub-Saharan Africa",
        "countries": ["Nigeria", "Ghana", "Côte d'Ivoire", "Senegal", "Benin", "Togo", "Guinea", "Sierra Leone", "Liberia"],
        "key_dynamics": [
            "Nigeria (Tinubu reforms, security crisis)",
            "Ghana (economic stress)",
            "ECOWAS strains",
        ],
    },
    "southern_africa": {
        "name": "Southern Africa",
        "region": "Sub-Saharan Africa",
        "countries": ["South Africa", "Zimbabwe", "Mozambique", "Zambia", "Angola", "Namibia", "Botswana"],
        "key_dynamics": [
            "South Africa (ANC decline, coalition governance)",
            "Mozambique (Cabo Delgado, LNG)",
            "Zambia debt restructuring",
        ],
    },
    "india": {
        "name": "India",
        "region": "South Asia",
        "countries": ["India"],
        "key_dynamics": [
            "Modi/BJP trajectory",
            "India-China competition",
            "Global South leadership aspirations",
        ],
    },
    "pakistan_afghanistan": {
        "name": "Pakistan & Afghanistan",
        "region": "South Asia",
        "countries": ["Pakistan", "Afghanistan"],
        "key_dynamics": [
            "Pakistan (military-civilian dynamics, TTP)",
            "Afghanistan (Taliban 2.0, ISIS-K)",
            "Nuclear arsenal",
        ],
    },
    "south_asia_periphery": {
        "name": "South Asian Periphery",
        "region": "South Asia",
        "countries": ["Bangladesh", "Sri Lanka", "Nepal", "Bhutan", "Maldives"],
        "key_dynamics": [
            "Bangladesh transition",
            "Sri Lanka post-crisis",
            "India-China competition in Indian Ocean",
        ],
    },
    "china": {
        "name": "China",
        "region": "East Asia",
        "countries": ["PRC", "Hong Kong", "Macau"],
        "key_dynamics": [
            "Xi consolidation",
            "Economic slowdown",
            "US-China competition",
            "Taiwan contingency",
        ],
    },
    "taiwan": {
        "name": "Taiwan",
        "region": "East Asia",
        "countries": ["Taiwan"],
        "key_dynamics": [
            "Cross-strait relations",
            "Semiconductor dominance",
            "US defense commitment",
        ],
    },
    "korea": {
        "name": "Korean Peninsula",
        "region": "East Asia",
        "countries": ["South Korea", "North Korea"],
        "key_dynamics": [
            "North Korea (nuclear advancement, Russia ties)",
            "South Korea (polarization, demographic crisis)",
        ],
    },
    "japan": {
        "name": "Japan",
        "region": "East Asia",
        "countries": ["Japan"],
        "key_dynamics": [
            "Post-Abe security transformation",
            "Demographic crisis",
            "US alliance deepening",
        ],
    },
    "mongolia": {
        "name": "Mongolia",
        "region": "East Asia",
        "countries": ["Mongolia"],
        "key_dynamics": [
            "Third neighbor balancing",
            "Mining-dependent economy",
            "Democratic outlier",
        ],
    },
    "mainland_sea": {
        "name": "Mainland Southeast Asia",
        "region": "Southeast Asia",
        "countries": ["Vietnam", "Thailand", "Cambodia", "Laos", "Myanmar"],
        "key_dynamics": [
            "Vietnam manufacturing rise",
            "Thailand's political triangle",
            "Myanmar civil war",
            "Mekong River politics",
        ],
    },
    "maritime_sea": {
        "name": "Maritime Southeast Asia",
        "region": "Southeast Asia",
        "countries": ["Indonesia", "Philippines", "Malaysia", "Singapore", "Brunei", "Timor-Leste"],
        "key_dynamics": [
            "Indonesia (middle power aspirations, nickel)",
            "Philippines (South China Sea)",
            "South China Sea disputes",
        ],
    },
    "australia_nz": {
        "name": "Australia & New Zealand",
        "region": "Oceania & Pacific",
        "countries": ["Australia", "New Zealand"],
        "key_dynamics": [
            "AUKUS implementation",
            "China reset attempts",
            "Pacific strategic competition",
        ],
    },
    "pacific_islands": {
        "name": "Pacific Islands",
        "region": "Oceania & Pacific",
        "countries": ["Melanesia", "Micronesia", "Polynesia"],
        "key_dynamics": [
            "US-China competition",
            "Climate as existential threat",
            "Deep-sea mining debates",
        ],
    },
    "usa": {
        "name": "United States",
        "region": "The Americas",
        "countries": ["United States"],
        "key_dynamics": [
            "Grand strategy debates",
            "Defense posture allocation",
            "China policy as organizing principle",
            "Domestic polarization as foreign policy variable",
        ],
    },
    "canada": {
        "name": "Canada",
        "region": "The Americas",
        "countries": ["Canada"],
        "key_dynamics": [
            "US relationship management",
            "Arctic sovereignty",
            "China relations deterioration",
        ],
    },
    "mexico_central_america": {
        "name": "Mexico & Central America",
        "region": "The Americas",
        "countries": ["Mexico", "Guatemala", "Honduras", "El Salvador", "Nicaragua", "Costa Rica", "Panama"],
        "key_dynamics": [
            "Mexico (nearshoring, cartels)",
            "Northern Triangle migration",
            "Panama Canal drought",
        ],
    },
    "caribbean": {
        "name": "Caribbean",
        "region": "The Americas",
        "countries": ["Cuba", "Haiti", "Dominican Republic", "Jamaica", "Trinidad & Tobago"],
        "key_dynamics": [
            "Haiti state collapse",
            "Cuba post-Castro",
            "Climate vulnerability",
        ],
    },
    "andean": {
        "name": "Andean Region",
        "region": "The Americas",
        "countries": ["Colombia", "Venezuela", "Ecuador", "Peru", "Bolivia"],
        "key_dynamics": [
            "Colombia post-peace",
            "Venezuela migration crisis",
            "Bolivia lithium",
        ],
    },
    "southern_cone": {
        "name": "Southern Cone",
        "region": "The Americas",
        "countries": ["Brazil", "Argentina", "Chile", "Uruguay", "Paraguay"],
        "key_dynamics": [
            "Brazil (regional leadership, Amazon)",
            "Argentina (Milei shock therapy)",
            "Lithium triangle",
        ],
    },
}


class ZoneInfo(BaseModel):
    """Zone information response."""

    id: str
    name: str
    region: str
    countries: list[str]
    key_dynamics: list[str]


class ZoneList(BaseModel):
    """List of zones."""

    total: int
    zones: list[ZoneInfo]


@router.get("", response_model=ZoneList)
async def list_zones(region: str | None = None) -> ZoneList:
    """
    List all 42 coverage zones.

    Optionally filter by region.
    """
    zones = []

    for zone_id, metadata in ZONE_METADATA.items():
        if region and metadata["region"].lower() != region.lower():
            continue

        zones.append(
            ZoneInfo(
                id=zone_id,
                name=metadata["name"],
                region=metadata["region"],
                countries=metadata["countries"],
                key_dynamics=metadata["key_dynamics"],
            )
        )

    return ZoneList(total=len(zones), zones=zones)


@router.get("/regions", response_model=list[str])
async def list_regions() -> list[str]:
    """
    List all regions.
    """
    regions = set(m["region"] for m in ZONE_METADATA.values())
    return sorted(regions)


@router.get("/{zone_id}", response_model=ZoneInfo)
async def get_zone(zone_id: str) -> ZoneInfo:
    """
    Get information about a specific zone.
    """
    if zone_id not in ZONE_METADATA:
        raise HTTPException(status_code=404, detail=f"Zone not found: {zone_id}")

    metadata = ZONE_METADATA[zone_id]

    return ZoneInfo(
        id=zone_id,
        name=metadata["name"],
        region=metadata["region"],
        countries=metadata["countries"],
        key_dynamics=metadata["key_dynamics"],
    )


@router.get("/{zone_id}/stories")
async def get_zone_stories(zone_id: str, limit: int = 20) -> dict[str, Any]:
    """
    Get recent stories for a zone.
    """
    if zone_id not in ZONE_METADATA:
        raise HTTPException(status_code=404, detail=f"Zone not found: {zone_id}")

    # This would query the database - returning placeholder
    return {
        "zone_id": zone_id,
        "stories": [],
        "total": 0,
        "message": "Query database for actual stories",
    }

