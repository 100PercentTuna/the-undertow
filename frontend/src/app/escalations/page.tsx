"use client";

import { useState, useEffect } from "react";
import { api, Escalation } from "@/lib/api";

type Priority = "critical" | "high" | "medium" | "low";
type Status = "pending" | "in_review" | "approved" | "rejected" | "revised";

interface EscalationListResponse {
  total: number;
  pending: number;
  escalations: Escalation[];
}

interface EscalationDetail {
  escalation_id: string;
  priority: Priority;
  reason: string;
  status: Status;
  story_headline: string;
  quality_score: number;
  quality_details: Record<string, number>;
  concerns: string[];
  disputed_claims: Array<{ claim: string; evidence: string }>;
  low_confidence_sections: string[];
  draft_content: string | null;
  analysis_summary: string | null;
  reviewer: string | null;
  review_notes: string | null;
  created_at: string;
  resolved_at: string | null;
}

const priorityColors: Record<Priority, string> = {
  critical: "bg-red-600",
  high: "bg-orange-500",
  medium: "bg-yellow-500",
  low: "bg-slate-500",
};

const statusColors: Record<Status, string> = {
  pending: "bg-blue-500",
  in_review: "bg-purple-500",
  approved: "bg-green-500",
  rejected: "bg-red-500",
  revised: "bg-cyan-500",
};

export default function EscalationsPage() {
  const [escalations, setEscalations] = useState<Escalation[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<EscalationDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [resolving, setResolving] = useState(false);
  const [filter, setFilter] = useState<{ status?: string; priority?: string }>({});
  const [reviewNotes, setReviewNotes] = useState("");
  const [reviewer, setReviewer] = useState("");
  const [stats, setStats] = useState<{
    total: number;
    by_status: Record<string, number>;
    by_priority: Record<string, number>;
    by_reason: Record<string, number>;
  } | null>(null);

  useEffect(() => {
    loadEscalations();
    loadStats();
  }, [filter]);

  async function loadEscalations() {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filter.status) params.append("status", filter.status);
      if (filter.priority) params.append("priority", filter.priority);

      const response = await fetch(`${api.baseUrl}/escalations?${params}`);
      const data: EscalationListResponse = await response.json();
      setEscalations(data.escalations);
    } catch (error) {
      console.error("Failed to load escalations:", error);
    } finally {
      setLoading(false);
    }
  }

  async function loadStats() {
    try {
      const response = await fetch(`${api.baseUrl}/escalations/stats/summary`);
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error("Failed to load stats:", error);
    }
  }

  async function loadDetail(id: string) {
    try {
      const response = await fetch(`${api.baseUrl}/escalations/${id}`);
      const data: EscalationDetail = await response.json();
      setDetail(data);
      setSelectedId(id);
    } catch (error) {
      console.error("Failed to load escalation detail:", error);
    }
  }

  async function resolveEscalation(status: "approved" | "rejected" | "revised") {
    if (!selectedId || !reviewer || !reviewNotes) {
      alert("Please fill in reviewer name and notes");
      return;
    }

    setResolving(true);
    try {
      await fetch(`${api.baseUrl}/escalations/${selectedId}/resolve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status, reviewer, notes: reviewNotes }),
      });
      
      setSelectedId(null);
      setDetail(null);
      setReviewNotes("");
      loadEscalations();
      loadStats();
    } catch (error) {
      console.error("Failed to resolve escalation:", error);
    } finally {
      setResolving(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="bg-slate-900 border-b border-slate-800">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-amber-400">Human Escalations</h1>
              <p className="text-slate-400 text-sm">
                Content requiring human review
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

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Stats Overview */}
        {stats && (
          <div className="grid grid-cols-5 gap-4 mb-8">
            <div className="bg-slate-900 rounded-lg p-4 border border-slate-800">
              <div className="text-3xl font-bold text-amber-400">{stats.total}</div>
              <div className="text-slate-400 text-sm">Total</div>
            </div>
            {Object.entries(stats.by_priority).map(([priority, count]) => (
              <div key={priority} className="bg-slate-900 rounded-lg p-4 border border-slate-800">
                <div className="flex items-center gap-2">
                  <span className={`w-3 h-3 rounded-full ${priorityColors[priority as Priority]}`} />
                  <span className="text-2xl font-bold">{count}</span>
                </div>
                <div className="text-slate-400 text-sm capitalize">{priority}</div>
              </div>
            ))}
          </div>
        )}

        {/* Filters */}
        <div className="flex gap-4 mb-6">
          <select
            value={filter.priority || ""}
            onChange={(e) => setFilter({ ...filter, priority: e.target.value || undefined })}
            className="bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm"
          >
            <option value="">All Priorities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
          <select
            value={filter.status || ""}
            onChange={(e) => setFilter({ ...filter, status: e.target.value || undefined })}
            className="bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm"
          >
            <option value="">All Statuses</option>
            <option value="pending">Pending</option>
            <option value="in_review">In Review</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
          </select>
          <button
            onClick={loadEscalations}
            className="bg-amber-600 hover:bg-amber-500 px-4 py-2 rounded text-sm font-medium transition-colors"
          >
            Refresh
          </button>
        </div>

        <div className="grid grid-cols-2 gap-6">
          {/* Escalation List */}
          <div className="bg-slate-900 rounded-xl border border-slate-800">
            <div className="p-4 border-b border-slate-800">
              <h2 className="font-semibold">Escalation Queue</h2>
            </div>
            <div className="divide-y divide-slate-800 max-h-[600px] overflow-y-auto">
              {loading ? (
                <div className="p-8 text-center text-slate-500">Loading...</div>
              ) : escalations.length === 0 ? (
                <div className="p-8 text-center text-slate-500">
                  No escalations found
                </div>
              ) : (
                escalations.map((esc) => (
                  <div
                    key={esc.escalation_id}
                    onClick={() => loadDetail(esc.escalation_id)}
                    className={`p-4 cursor-pointer hover:bg-slate-800/50 transition-colors ${
                      selectedId === esc.escalation_id ? "bg-slate-800" : ""
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span
                          className={`px-2 py-0.5 rounded text-xs font-medium ${
                            priorityColors[esc.priority as Priority]
                          }`}
                        >
                          {esc.priority}
                        </span>
                        <span
                          className={`px-2 py-0.5 rounded text-xs font-medium ${
                            statusColors[esc.status as Status]
                          }`}
                        >
                          {esc.status}
                        </span>
                      </div>
                      <span className="text-slate-500 text-xs">
                        {new Date(esc.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    <h3 className="font-medium text-sm mb-1 line-clamp-2">
                      {esc.story_headline}
                    </h3>
                    <div className="flex items-center justify-between text-xs text-slate-400">
                      <span>{esc.reason}</span>
                      <span>Quality: {(esc.quality_score * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Detail View */}
          <div className="bg-slate-900 rounded-xl border border-slate-800">
            {detail ? (
              <div className="h-full flex flex-col">
                <div className="p-4 border-b border-slate-800">
                  <div className="flex items-center gap-2 mb-2">
                    <span
                      className={`px-2 py-0.5 rounded text-xs font-medium ${
                        priorityColors[detail.priority]
                      }`}
                    >
                      {detail.priority}
                    </span>
                    <span
                      className={`px-2 py-0.5 rounded text-xs font-medium ${
                        statusColors[detail.status]
                      }`}
                    >
                      {detail.status}
                    </span>
                  </div>
                  <h2 className="font-semibold">{detail.story_headline}</h2>
                  <p className="text-sm text-slate-400 mt-1">
                    Reason: {detail.reason} • Quality: {(detail.quality_score * 100).toFixed(0)}%
                  </p>
                </div>

                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                  {/* Quality Details */}
                  <div>
                    <h3 className="font-medium text-amber-400 mb-2">Quality Breakdown</h3>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      {Object.entries(detail.quality_details).map(([key, value]) => (
                        <div key={key} className="flex justify-between bg-slate-800/50 rounded px-2 py-1">
                          <span className="text-slate-400 capitalize">{key}</span>
                          <span>{((value as number) * 100).toFixed(0)}%</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Concerns */}
                  {detail.concerns.length > 0 && (
                    <div>
                      <h3 className="font-medium text-red-400 mb-2">Concerns</h3>
                      <ul className="text-sm space-y-1">
                        {detail.concerns.map((concern, i) => (
                          <li key={i} className="text-slate-300">• {concern}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Disputed Claims */}
                  {detail.disputed_claims.length > 0 && (
                    <div>
                      <h3 className="font-medium text-yellow-400 mb-2">Disputed Claims</h3>
                      <div className="space-y-2">
                        {detail.disputed_claims.map((dc, i) => (
                          <div key={i} className="bg-slate-800/50 rounded p-2 text-sm">
                            <p className="text-slate-200">{dc.claim}</p>
                            <p className="text-slate-400 text-xs mt-1">{dc.evidence}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Analysis Summary */}
                  {detail.analysis_summary && (
                    <div>
                      <h3 className="font-medium text-slate-300 mb-2">Analysis Summary</h3>
                      <p className="text-sm text-slate-400">{detail.analysis_summary}</p>
                    </div>
                  )}

                  {/* Draft Content Preview */}
                  {detail.draft_content && (
                    <div>
                      <h3 className="font-medium text-slate-300 mb-2">Draft Preview</h3>
                      <div className="bg-slate-800/50 rounded p-3 text-sm text-slate-300 max-h-40 overflow-y-auto">
                        {detail.draft_content.substring(0, 500)}...
                      </div>
                    </div>
                  )}
                </div>

                {/* Resolution Form */}
                {detail.status === "pending" && (
                  <div className="p-4 border-t border-slate-800 space-y-3">
                    <input
                      type="text"
                      placeholder="Reviewer name"
                      value={reviewer}
                      onChange={(e) => setReviewer(e.target.value)}
                      className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm"
                    />
                    <textarea
                      placeholder="Review notes (required)"
                      value={reviewNotes}
                      onChange={(e) => setReviewNotes(e.target.value)}
                      className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm resize-none h-20"
                    />
                    <div className="flex gap-2">
                      <button
                        onClick={() => resolveEscalation("approved")}
                        disabled={resolving}
                        className="flex-1 bg-green-600 hover:bg-green-500 px-4 py-2 rounded text-sm font-medium transition-colors disabled:opacity-50"
                      >
                        Approve
                      </button>
                      <button
                        onClick={() => resolveEscalation("revised")}
                        disabled={resolving}
                        className="flex-1 bg-cyan-600 hover:bg-cyan-500 px-4 py-2 rounded text-sm font-medium transition-colors disabled:opacity-50"
                      >
                        Revised
                      </button>
                      <button
                        onClick={() => resolveEscalation("rejected")}
                        disabled={resolving}
                        className="flex-1 bg-red-600 hover:bg-red-500 px-4 py-2 rounded text-sm font-medium transition-colors disabled:opacity-50"
                      >
                        Reject
                      </button>
                    </div>
                  </div>
                )}

                {/* Previous Resolution */}
                {detail.reviewer && (
                  <div className="p-4 border-t border-slate-800 bg-slate-800/30">
                    <p className="text-sm">
                      <span className="text-slate-400">Resolved by </span>
                      <span className="text-amber-400">{detail.reviewer}</span>
                      <span className="text-slate-400"> on </span>
                      {detail.resolved_at && new Date(detail.resolved_at).toLocaleString()}
                    </p>
                    {detail.review_notes && (
                      <p className="text-sm text-slate-300 mt-2">{detail.review_notes}</p>
                    )}
                  </div>
                )}
              </div>
            ) : (
              <div className="h-full flex items-center justify-center text-slate-500">
                Select an escalation to view details
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

