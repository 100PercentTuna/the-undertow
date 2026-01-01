"use client";

import { useEffect, useState } from "react";
import {
  Activity,
  FileText,
  Zap,
  TrendingUp,
  AlertTriangle,
  Clock,
} from "lucide-react";

interface DashboardStats {
  stories_pending: number;
  articles_published_today: number;
  pipeline_status: string;
  total_cost_today: number;
  avg_quality_score: number;
  last_pipeline_run: string;
}

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  async function fetchStats() {
    try {
      const [pipelineRes, metricsRes] = await Promise.all([
        fetch("/api/v1/pipeline/stats"),
        fetch("/api/v1/metrics"),
      ]);

      if (!pipelineRes.ok || !metricsRes.ok) {
        throw new Error("Failed to fetch stats");
      }

      const pipeline = await pipelineRes.json();
      const metrics = await metricsRes.json();

      setStats({
        stories_pending: pipeline.stories_pending || 0,
        articles_published_today: pipeline.articles_generated || 0,
        pipeline_status: pipeline.status || "unknown",
        total_cost_today: pipeline.total_cost_usd || 0,
        avg_quality_score: pipeline.avg_quality_score || 0,
        last_pipeline_run: pipeline.last_run || "Never",
      });
      setError(null);
    } catch (e) {
      setError("Failed to load dashboard data");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen">
      {/* Header */}
      <header className="border-b border-undertow-800 bg-undertow-900/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-accent-600 rounded-lg flex items-center justify-center">
                <Zap className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-serif font-bold tracking-tight">
                The Undertow
              </span>
            </div>
            <nav className="flex items-center gap-6">
              <a href="/" className="text-undertow-100 font-medium">
                Dashboard
              </a>
              <a href="/stories" className="text-undertow-400 hover:text-undertow-100">
                Stories
              </a>
              <a href="/articles" className="text-undertow-400 hover:text-undertow-100">
                Articles
              </a>
              <a href="/pipeline" className="text-undertow-400 hover:text-undertow-100">
                Pipeline
              </a>
            </nav>
          </div>
        </div>
      </header>

      {/* Main content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-3xl font-serif font-bold mb-8">Dashboard</h1>

        {error && (
          <div className="mb-6 p-4 bg-red-900/30 border border-red-800 rounded-lg flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-red-400" />
            <span className="text-red-300">{error}</span>
          </div>
        )}

        {/* Stats grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          <StatCard
            title="Stories Pending"
            value={loading ? "..." : stats?.stories_pending ?? 0}
            icon={<FileText className="w-5 h-5" />}
            color="blue"
          />
          <StatCard
            title="Articles Today"
            value={loading ? "..." : stats?.articles_published_today ?? 0}
            icon={<TrendingUp className="w-5 h-5" />}
            color="green"
          />
          <StatCard
            title="Pipeline Status"
            value={loading ? "..." : stats?.pipeline_status ?? "Unknown"}
            icon={<Activity className="w-5 h-5" />}
            color={stats?.pipeline_status === "running" ? "yellow" : "default"}
          />
          <StatCard
            title="Cost Today"
            value={loading ? "..." : `$${(stats?.total_cost_today ?? 0).toFixed(2)}`}
            icon={<Zap className="w-5 h-5" />}
            color="purple"
          />
          <StatCard
            title="Avg Quality"
            value={loading ? "..." : `${((stats?.avg_quality_score ?? 0) * 100).toFixed(0)}%`}
            icon={<TrendingUp className="w-5 h-5" />}
            color="accent"
          />
          <StatCard
            title="Last Pipeline"
            value={loading ? "..." : stats?.last_pipeline_run ?? "Never"}
            icon={<Clock className="w-5 h-5" />}
            color="default"
          />
        </div>

        {/* Quick actions */}
        <div className="card">
          <h2 className="text-lg font-serif font-semibold mb-4">Quick Actions</h2>
          <div className="flex flex-wrap gap-3">
            <button
              className="btn btn-primary"
              onClick={() => fetch("/api/v1/pipeline/trigger", { method: "POST" })}
            >
              Run Pipeline
            </button>
            <button className="btn btn-secondary">
              Refresh Sources
            </button>
            <button className="btn btn-secondary">
              Preview Newsletter
            </button>
          </div>
        </div>
      </div>
    </main>
  );
}

function StatCard({
  title,
  value,
  icon,
  color,
}: {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  color: string;
}) {
  const colorClasses: Record<string, string> = {
    blue: "bg-blue-900/30 border-blue-800 text-blue-400",
    green: "bg-green-900/30 border-green-800 text-green-400",
    yellow: "bg-yellow-900/30 border-yellow-800 text-yellow-400",
    purple: "bg-purple-900/30 border-purple-800 text-purple-400",
    accent: "bg-accent-900/30 border-accent-800 text-accent-400",
    default: "bg-undertow-800/50 border-undertow-700 text-undertow-400",
  };

  return (
    <div className={`rounded-xl border p-6 ${colorClasses[color] || colorClasses.default}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium opacity-80">{title}</span>
        {icon}
      </div>
      <div className="text-2xl font-bold text-undertow-100">{value}</div>
    </div>
  );
}

