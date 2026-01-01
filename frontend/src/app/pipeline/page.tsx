"use client";

import { useEffect, useState } from "react";
import {
  Activity,
  Play,
  Clock,
  CheckCircle,
  XCircle,
  AlertTriangle,
  RefreshCw,
  DollarSign,
  Zap,
} from "lucide-react";
import Link from "next/link";

interface PipelineRun {
  id: string;
  status: string;
  started_at: string | null;
  completed_at: string | null;
  stories_processed: number;
  articles_generated: number;
  total_cost_usd: number;
  avg_quality_score: number | null;
  error_message: string | null;
  created_at: string;
}

interface PipelineStats {
  total_runs: number;
  success_rate: number;
  stories_processed: number;
  articles_generated: number;
  total_cost_usd: number;
  avg_quality_score: number;
}

export default function PipelinePage() {
  const [runs, setRuns] = useState<PipelineRun[]>([]);
  const [stats, setStats] = useState<PipelineStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState(false);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 10000); // Refresh every 10s
    return () => clearInterval(interval);
  }, []);

  async function fetchData() {
    try {
      const [runsRes, statsRes] = await Promise.all([
        fetch("/api/v1/pipeline/runs?limit=20"),
        fetch("/api/v1/pipeline/stats"),
      ]);

      if (runsRes.ok) {
        const runsData = await runsRes.json();
        setRuns(runsData.items || runsData || []);
      }

      if (statsRes.ok) {
        setStats(await statsRes.json());
      }
    } catch (e) {
      console.error("Failed to fetch pipeline data", e);
    } finally {
      setLoading(false);
    }
  }

  async function triggerPipeline() {
    setTriggering(true);
    try {
      const res = await fetch("/api/v1/pipeline/trigger", { method: "POST" });
      if (res.ok) {
        fetchData();
      }
    } catch (e) {
      console.error("Failed to trigger pipeline", e);
    } finally {
      setTriggering(false);
    }
  }

  const currentRun = runs.find((r) => r.status === "running");

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
              <Link href="/articles" className="text-undertow-400 hover:text-undertow-100">
                Articles
              </Link>
              <Link href="/pipeline" className="text-undertow-100 font-medium">
                Pipeline
              </Link>
            </nav>
          </div>
        </div>
      </header>

      {/* Main content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-serif font-bold">Pipeline</h1>
          <button
            onClick={triggerPipeline}
            disabled={triggering || !!currentRun}
            className="btn btn-primary flex items-center gap-2 disabled:opacity-50"
          >
            {triggering ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <Play className="w-4 h-4" />
            )}
            {currentRun ? "Running..." : "Run Pipeline"}
          </button>
        </div>

        {/* Current run status */}
        {currentRun && (
          <div className="card mb-8 border-yellow-800 bg-yellow-900/20">
            <div className="flex items-center gap-3 mb-4">
              <RefreshCw className="w-5 h-5 text-yellow-400 animate-spin" />
              <span className="text-yellow-400 font-medium">Pipeline Running</span>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="text-undertow-400">Started</span>
                <div className="text-undertow-100">
                  {currentRun.started_at
                    ? new Date(currentRun.started_at).toLocaleTimeString()
                    : "—"}
                </div>
              </div>
              <div>
                <span className="text-undertow-400">Stories</span>
                <div className="text-undertow-100">{currentRun.stories_processed}</div>
              </div>
              <div>
                <span className="text-undertow-400">Articles</span>
                <div className="text-undertow-100">{currentRun.articles_generated}</div>
              </div>
              <div>
                <span className="text-undertow-400">Cost</span>
                <div className="text-undertow-100">${currentRun.total_cost_usd.toFixed(2)}</div>
              </div>
            </div>
          </div>
        )}

        {/* Stats */}
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <StatCard
              label="Total Runs"
              value={stats.total_runs}
              icon={<Activity className="w-4 h-4" />}
            />
            <StatCard
              label="Success Rate"
              value={`${(stats.success_rate * 100).toFixed(0)}%`}
              icon={<CheckCircle className="w-4 h-4" />}
              color={stats.success_rate >= 0.9 ? "green" : stats.success_rate >= 0.7 ? "yellow" : "red"}
            />
            <StatCard
              label="Total Cost"
              value={`$${stats.total_cost_usd.toFixed(2)}`}
              icon={<DollarSign className="w-4 h-4" />}
            />
            <StatCard
              label="Avg Quality"
              value={`${((stats.avg_quality_score || 0) * 100).toFixed(0)}%`}
              icon={<Zap className="w-4 h-4" />}
              color={stats.avg_quality_score >= 0.85 ? "green" : "yellow"}
            />
          </div>
        )}

        {/* Run history */}
        <div className="card">
          <h2 className="text-lg font-serif font-semibold mb-4">Run History</h2>

          {loading ? (
            <div className="text-center py-8 text-undertow-400">Loading...</div>
          ) : runs.length === 0 ? (
            <div className="text-center py-8 text-undertow-400">
              No pipeline runs yet
            </div>
          ) : (
            <div className="space-y-3">
              {runs.map((run) => (
                <RunCard key={run.id} run={run} />
              ))}
            </div>
          )}
        </div>
      </div>
    </main>
  );
}

function StatCard({
  label,
  value,
  icon,
  color = "default",
}: {
  label: string;
  value: string | number;
  icon: React.ReactNode;
  color?: string;
}) {
  const colorClasses: Record<string, string> = {
    green: "text-green-400",
    yellow: "text-yellow-400",
    red: "text-red-400",
    default: "text-undertow-400",
  };

  return (
    <div className="card">
      <div className="flex items-center gap-2 text-undertow-400 mb-1">
        {icon}
        <span className="text-sm">{label}</span>
      </div>
      <div className={`text-2xl font-bold ${colorClasses[color]}`}>{value}</div>
    </div>
  );
}

function RunCard({ run }: { run: PipelineRun }) {
  const statusConfig: Record<string, { icon: React.ReactNode; color: string }> = {
    pending: { icon: <Clock className="w-4 h-4" />, color: "text-undertow-400" },
    running: { icon: <RefreshCw className="w-4 h-4 animate-spin" />, color: "text-yellow-400" },
    completed: { icon: <CheckCircle className="w-4 h-4" />, color: "text-green-400" },
    failed: { icon: <XCircle className="w-4 h-4" />, color: "text-red-400" },
    cancelled: { icon: <AlertTriangle className="w-4 h-4" />, color: "text-undertow-400" },
  };

  const config = statusConfig[run.status] || statusConfig.pending;

  return (
    <div className="flex items-center justify-between p-4 bg-undertow-800/50 rounded-lg">
      <div className="flex items-center gap-4">
        <div className={config.color}>{config.icon}</div>
        <div>
          <div className="font-medium text-undertow-100">
            {new Date(run.created_at).toLocaleString()}
          </div>
          <div className="text-sm text-undertow-400">
            {run.stories_processed} stories → {run.articles_generated} articles
          </div>
        </div>
      </div>
      <div className="flex items-center gap-6 text-sm">
        {run.avg_quality_score && (
          <div className="text-undertow-400">
            Quality: <span className="text-undertow-100">{(run.avg_quality_score * 100).toFixed(0)}%</span>
          </div>
        )}
        <div className="text-undertow-400">
          Cost: <span className="text-undertow-100">${run.total_cost_usd.toFixed(2)}</span>
        </div>
        {run.completed_at && run.started_at && (
          <div className="text-undertow-400">
            Duration:{" "}
            <span className="text-undertow-100">
              {Math.round((new Date(run.completed_at).getTime() - new Date(run.started_at).getTime()) / 1000 / 60)} min
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

