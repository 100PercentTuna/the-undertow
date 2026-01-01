"use client";

import { useEffect, useState } from "react";
import { Activity, Globe, MapPin, Search } from "lucide-react";
import Link from "next/link";

interface ZoneInfo {
  id: string;
  name: string;
  region: string;
  countries: string[];
  key_dynamics: string[];
}

interface ZoneList {
  total: number;
  zones: ZoneInfo[];
}

const REGION_COLORS: Record<string, string> = {
  Europe: "bg-blue-500",
  "Russia & Eurasia": "bg-purple-500",
  "Middle East & North Africa": "bg-amber-500",
  "Sub-Saharan Africa": "bg-green-500",
  "South Asia": "bg-orange-500",
  "East Asia": "bg-red-500",
  "Southeast Asia": "bg-teal-500",
  "Oceania & Pacific": "bg-cyan-500",
  "The Americas": "bg-indigo-500",
};

export default function ZonesPage() {
  const [zones, setZones] = useState<ZoneInfo[]>([]);
  const [regions, setRegions] = useState<string[]>([]);
  const [selectedRegion, setSelectedRegion] = useState<string>("");
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  async function fetchData() {
    try {
      const [zonesRes, regionsRes] = await Promise.all([
        fetch("/api/v1/zones"),
        fetch("/api/v1/zones/regions"),
      ]);

      if (zonesRes.ok) {
        const data: ZoneList = await zonesRes.json();
        setZones(data.zones);
      }

      if (regionsRes.ok) {
        setRegions(await regionsRes.json());
      }
    } catch (e) {
      console.error("Failed to fetch zones", e);
    } finally {
      setLoading(false);
    }
  }

  const filteredZones = zones.filter((zone) => {
    const matchesRegion = !selectedRegion || zone.region === selectedRegion;
    const matchesSearch =
      !searchQuery ||
      zone.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      zone.countries.some((c) =>
        c.toLowerCase().includes(searchQuery.toLowerCase())
      );
    return matchesRegion && matchesSearch;
  });

  const zonesByRegion = filteredZones.reduce((acc, zone) => {
    if (!acc[zone.region]) acc[zone.region] = [];
    acc[zone.region].push(zone);
    return acc;
  }, {} as Record<string, ZoneInfo[]>);

  return (
    <main className="min-h-screen">
      {/* Header */}
      <header className="border-b border-undertow-800 bg-undertow-900/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-3">
              <Link href="/" className="flex items-center gap-3">
                <div className="w-8 h-8 bg-accent-600 rounded-lg flex items-center justify-center">
                  <Activity className="w-5 h-5 text-white" />
                </div>
                <span className="text-xl font-serif font-bold tracking-tight">
                  The Undertow
                </span>
              </Link>
            </div>
            <nav className="flex items-center gap-6">
              <Link href="/" className="text-undertow-400 hover:text-undertow-100">
                Dashboard
              </Link>
              <Link href="/stories" className="text-undertow-400 hover:text-undertow-100">
                Stories
              </Link>
              <Link href="/zones" className="text-undertow-100 font-medium">
                Zones
              </Link>
            </nav>
          </div>
        </div>
      </header>

      {/* Main content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-serif font-bold">Global Coverage Zones</h1>
            <p className="text-undertow-400 mt-1">
              42 distinct analytical zones with equal seriousness
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Globe className="w-5 h-5 text-accent-400" />
            <span className="text-undertow-100 font-medium">
              {zones.length} Zones
            </span>
          </div>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap gap-4 mb-8">
          <div className="relative flex-1 min-w-64">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-undertow-400" />
            <input
              type="text"
              placeholder="Search zones or countries..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-undertow-800 border border-undertow-700 rounded-lg text-undertow-100 placeholder-undertow-400 focus:outline-none focus:border-accent-500"
            />
          </div>
          <select
            value={selectedRegion}
            onChange={(e) => setSelectedRegion(e.target.value)}
            className="px-4 py-2 bg-undertow-800 border border-undertow-700 rounded-lg text-undertow-100 focus:outline-none focus:border-accent-500"
          >
            <option value="">All Regions</option>
            {regions.map((region) => (
              <option key={region} value={region}>
                {region}
              </option>
            ))}
          </select>
        </div>

        {loading ? (
          <div className="text-center py-8 text-undertow-400">Loading...</div>
        ) : (
          <div className="space-y-8">
            {Object.entries(zonesByRegion).map(([region, regionZones]) => (
              <div key={region}>
                <h2 className="text-xl font-serif font-semibold mb-4 flex items-center gap-2">
                  <span
                    className={`w-3 h-3 rounded-full ${
                      REGION_COLORS[region] || "bg-undertow-500"
                    }`}
                  />
                  {region}
                  <span className="text-undertow-400 text-sm font-normal">
                    ({regionZones.length})
                  </span>
                </h2>
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {regionZones.map((zone) => (
                    <ZoneCard key={zone.id} zone={zone} />
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}

function ZoneCard({ zone }: { zone: ZoneInfo }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="card hover:border-undertow-600 transition-colors">
      <div
        className="cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <h3 className="font-semibold text-undertow-100 mb-2">{zone.name}</h3>
        <div className="flex flex-wrap gap-1 mb-3">
          {zone.countries.slice(0, 4).map((country) => (
            <span
              key={country}
              className="px-2 py-0.5 text-xs bg-undertow-800 text-undertow-300 rounded"
            >
              {country}
            </span>
          ))}
          {zone.countries.length > 4 && (
            <span className="px-2 py-0.5 text-xs bg-undertow-800 text-undertow-400 rounded">
              +{zone.countries.length - 4}
            </span>
          )}
        </div>
      </div>

      {expanded && (
        <div className="mt-4 pt-4 border-t border-undertow-700">
          <h4 className="text-sm font-medium text-undertow-300 mb-2">
            Key Dynamics
          </h4>
          <ul className="space-y-1">
            {zone.key_dynamics.map((dynamic, i) => (
              <li
                key={i}
                className="flex items-start gap-2 text-sm text-undertow-400"
              >
                <MapPin className="w-3 h-3 mt-1 flex-shrink-0" />
                {dynamic}
              </li>
            ))}
          </ul>
          <div className="mt-4">
            <Link
              href={`/zones/${zone.id}`}
              className="text-sm text-accent-400 hover:text-accent-300"
            >
              View stories →
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}

