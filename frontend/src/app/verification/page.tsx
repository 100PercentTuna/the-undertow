"use client";

import { useState } from "react";
import { apiExtensions, ExtractedClaim, VerificationResult } from "@/lib/api";

export default function VerificationPage() {
  const [text, setText] = useState("");
  const [extractedClaims, setExtractedClaims] = useState<ExtractedClaim[]>([]);
  const [verifiedClaims, setVerifiedClaims] = useState<VerificationResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState<"input" | "extracted" | "verified">("input");
  const [zones, setZones] = useState<string[]>([]);

  const allZones = [
    "western_europe", "southern_europe", "nordic_baltic", "british_isles",
    "central_europe", "western_balkans", "eastern_europe", "south_caucasus",
    "russia_core", "central_asia_west", "central_asia_east", "levant",
    "gulf_gcc", "iraq", "iran", "turkey", "maghreb", "egypt", "horn_of_africa",
    "east_africa", "great_lakes", "sahel", "west_africa_coastal", "southern_africa",
    "india", "pakistan_afghanistan", "south_asian_periphery", "china",
    "taiwan", "korea", "japan", "mongolia", "mainland_sea", "maritime_sea",
    "australia_nz", "pacific_islands", "usa", "canada", "mexico_central_america",
    "caribbean", "andean", "southern_cone"
  ];

  async function handleExtract() {
    if (!text.trim()) return;
    
    setLoading(true);
    try {
      const result = await apiExtensions.extractClaims(text);
      setExtractedClaims(result.claims);
      setStep("extracted");
    } catch (error) {
      console.error("Extraction failed:", error);
    } finally {
      setLoading(false);
    }
  }

  async function handleVerify() {
    if (!extractedClaims.length) return;
    
    setLoading(true);
    try {
      const result = await apiExtensions.verifyClaims(extractedClaims, zones);
      setVerifiedClaims(result.verified_claims);
      setStep("verified");
    } catch (error) {
      console.error("Verification failed:", error);
    } finally {
      setLoading(false);
    }
  }

  function reset() {
    setText("");
    setExtractedClaims([]);
    setVerifiedClaims([]);
    setStep("input");
    setZones([]);
  }

  const claimTypeColors: Record<string, string> = {
    factual: "bg-blue-500",
    analytical: "bg-purple-500",
    predictive: "bg-orange-500",
    attributive: "bg-cyan-500",
  };

  const statusColors: Record<string, string> = {
    verified: "bg-green-500",
    supported: "bg-emerald-400",
    disputed: "bg-yellow-500",
    refuted: "bg-red-500",
    unverifiable: "bg-slate-500",
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="bg-slate-900 border-b border-slate-800">
        <div className="max-w-5xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-amber-400">Claim Verification</h1>
              <p className="text-slate-400 text-sm">
                Extract and verify claims against sources
              </p>
            </div>
            <a
              href="/"
              className="text-slate-400 hover:text-amber-400 transition-colors"
            >
              ← Dashboard
            </a>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-8">
        {/* Progress Steps */}
        <div className="flex items-center justify-center gap-4 mb-8">
          {["Input Text", "Review Claims", "Verification"].map((label, i) => {
            const stepName = ["input", "extracted", "verified"][i];
            const isActive = step === stepName;
            const isPast = 
              (step === "extracted" && i === 0) ||
              (step === "verified" && i <= 1);
            
            return (
              <div key={label} className="flex items-center gap-2">
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                    isActive
                      ? "bg-amber-500 text-slate-900"
                      : isPast
                      ? "bg-green-600"
                      : "bg-slate-700"
                  }`}
                >
                  {isPast ? "✓" : i + 1}
                </div>
                <span className={isActive ? "text-amber-400" : "text-slate-500"}>
                  {label}
                </span>
                {i < 2 && <div className="w-12 h-0.5 bg-slate-700" />}
              </div>
            );
          })}
        </div>

        {/* Step 1: Input */}
        {step === "input" && (
          <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
            <h2 className="font-semibold mb-4">Paste text to analyze</h2>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Enter geopolitical analysis text here..."
              className="w-full h-64 bg-slate-800 border border-slate-700 rounded-lg p-4 text-sm resize-none focus:outline-none focus:border-amber-500"
            />
            <div className="mt-4 flex justify-between items-center">
              <span className="text-slate-500 text-sm">
                {text.length} characters
              </span>
              <button
                onClick={handleExtract}
                disabled={loading || !text.trim()}
                className="bg-amber-600 hover:bg-amber-500 px-6 py-2 rounded font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? "Extracting..." : "Extract Claims →"}
              </button>
            </div>
          </div>
        )}

        {/* Step 2: Review Claims */}
        {step === "extracted" && (
          <div className="space-y-6">
            <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-semibold">
                  Extracted Claims ({extractedClaims.length})
                </h2>
                <button
                  onClick={reset}
                  className="text-slate-400 hover:text-amber-400 text-sm"
                >
                  Start Over
                </button>
              </div>

              <div className="space-y-3">
                {extractedClaims.map((claim) => (
                  <div
                    key={claim.claim_id}
                    className="bg-slate-800/50 rounded-lg p-4"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <p className="text-sm text-slate-200">{claim.text}</p>
                        <p className="text-xs text-slate-500 mt-2">
                          Source: "{claim.source_sentence}"
                        </p>
                      </div>
                      <div className="flex flex-col items-end gap-2">
                        <span
                          className={`px-2 py-0.5 rounded text-xs font-medium ${
                            claimTypeColors[claim.claim_type]
                          }`}
                        >
                          {claim.claim_type}
                        </span>
                        <span className="text-xs text-slate-400">
                          {(claim.confidence * 100).toFixed(0)}% conf.
                        </span>
                        {claim.requires_verification && (
                          <span className="text-xs text-amber-400">
                            Needs verification
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Zone Selection */}
            <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
              <h3 className="font-semibold mb-4">Filter by zones (optional)</h3>
              <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto">
                {allZones.map((zone) => (
                  <button
                    key={zone}
                    onClick={() => {
                      setZones(
                        zones.includes(zone)
                          ? zones.filter((z) => z !== zone)
                          : [...zones, zone]
                      );
                    }}
                    className={`px-2 py-1 rounded text-xs transition-colors ${
                      zones.includes(zone)
                        ? "bg-amber-600 text-white"
                        : "bg-slate-800 text-slate-400 hover:bg-slate-700"
                    }`}
                  >
                    {zone.replace(/_/g, " ")}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex justify-end">
              <button
                onClick={handleVerify}
                disabled={loading || extractedClaims.length === 0}
                className="bg-amber-600 hover:bg-amber-500 px-6 py-2 rounded font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? "Verifying..." : "Verify Claims →"}
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Verification Results */}
        {step === "verified" && (
          <div className="space-y-6">
            {/* Summary */}
            <div className="grid grid-cols-5 gap-4">
              {["verified", "supported", "disputed", "refuted", "unverifiable"].map(
                (status) => {
                  const count = verifiedClaims.filter(
                    (c) => c.status === status
                  ).length;
                  return (
                    <div
                      key={status}
                      className="bg-slate-900 rounded-lg p-4 border border-slate-800 text-center"
                    >
                      <div className="text-2xl font-bold">{count}</div>
                      <div className="text-xs text-slate-400 capitalize">
                        {status}
                      </div>
                    </div>
                  );
                }
              )}
            </div>

            {/* Results */}
            <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-semibold">Verification Results</h2>
                <button
                  onClick={reset}
                  className="bg-amber-600 hover:bg-amber-500 px-4 py-2 rounded text-sm font-medium transition-colors"
                >
                  Start New Verification
                </button>
              </div>

              <div className="space-y-3">
                {verifiedClaims.map((result) => (
                  <div
                    key={result.claim_id}
                    className="bg-slate-800/50 rounded-lg p-4"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <p className="text-sm text-slate-200">
                          {result.claim_text}
                        </p>
                        <div className="flex items-center gap-4 mt-2 text-xs text-slate-400">
                          <span>
                            Score: {(result.verification_score * 100).toFixed(0)}%
                          </span>
                          <span>
                            {result.independent_sources} independent source(s)
                          </span>
                          <span>{result.evidence_count} evidence items</span>
                        </div>
                      </div>
                      <span
                        className={`px-3 py-1 rounded text-xs font-medium ${
                          statusColors[result.status]
                        }`}
                      >
                        {result.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

