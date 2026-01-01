"use client";

import { useEffect, useState } from "react";
import {
  Activity,
  DollarSign,
  TrendingUp,
  AlertTriangle,
  BarChart3,
  Clock,
} from "lucide-react";
import Link from "next/link";

interface DailyCost {
  date: string;
  total_cost_usd: number;
  total_calls: number;
  budget_used_pct: number;
}

interface CurrentCosts {
  date: string;
  total_cost_usd: number;
  total_calls: number;
  budget_usd: number;
  budget_remaining_usd: number;
  budget_used_pct: number;
  by_agent: Record<string, number>;
  by_model: Record<string, number>;
}

interface BudgetStatus {
  is_over_budget: boolean;
  budget_remaining_usd: number;
  daily_budget_usd: number;
}

export default function CostsPage() {
  const [current, setCurrent] = useState<CurrentCosts | null>(null);
  const [weekly, setWeekly] = useState<DailyCost[]>([]);
  const [budget, setBudget] = useState<BudgetStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  async function fetchData() {
    try {
      const [currentRes, weeklyRes, budgetRes] = await Promise.all([
        fetch("/api/v1/costs"),
        fetch("/api/v1/costs/weekly"),
        fetch("/api/v1/costs/budget"),
      ]);

      if (currentRes.ok) setCurrent(await currentRes.json());
      if (weeklyRes.ok) setWeekly(await weeklyRes.json());
      if (budgetRes.ok) setBudget(await budgetRes.json());
    } catch (e) {
      console.error("Failed to fetch costs", e);
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
              <Link href="/pipeline" className="text-undertow-400 hover:text-undertow-100">
                Pipeline
              </Link>
              <Link href="/costs" className="text-undertow-100 font-medium">
                Costs
              </Link>
            </nav>
          </div>
        </div>
      </header>

      {/* Main content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-3xl font-serif font-bold mb-8">Cost Tracking</h1>

        {loading ? (
          <div className="text-center py-8 text-undertow-400">Loading...</div>
        ) : (
          <>
            {/* Budget alert */}
            {budget?.is_over_budget && (
              <div className="card mb-8 border-red-800 bg-red-900/20">
                <div className="flex items-center gap-3">
                  <AlertTriangle className="w-5 h-5 text-red-400" />
                  <span className="text-red-400 font-medium">
                    Daily budget exceeded! Current spend: ${current?.total_cost_usd.toFixed(2)}
                  </span>
                </div>
              </div>
            )}

            {/* Summary cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
              <StatCard
                label="Today's Spend"
                value={`$${(current?.total_cost_usd || 0).toFixed(2)}`}
                icon={<DollarSign className="w-4 h-4" />}
              />
              <StatCard
                label="Budget Remaining"
                value={`$${(budget?.budget_remaining_usd || 0).toFixed(2)}`}
                icon={<TrendingUp className="w-4 h-4" />}
                color={
                  (budget?.budget_remaining_usd || 0) < 20
                    ? "red"
                    : (budget?.budget_remaining_usd || 0) < 50
                    ? "yellow"
                    : "green"
                }
              />
              <StatCard
                label="API Calls Today"
                value={current?.total_calls || 0}
                icon={<BarChart3 className="w-4 h-4" />}
              />
              <StatCard
                label="Budget Used"
                value={`${(current?.budget_used_pct || 0).toFixed(0)}%`}
                icon={<Clock className="w-4 h-4" />}
                color={
                  (current?.budget_used_pct || 0) > 90
                    ? "red"
                    : (current?.budget_used_pct || 0) > 70
                    ? "yellow"
                    : "default"
                }
              />
            </div>

            {/* Charts section */}
            <div className="grid md:grid-cols-2 gap-6 mb-8">
              {/* Weekly trend */}
              <div className="card">
                <h2 className="text-lg font-serif font-semibold mb-4">Weekly Trend</h2>
                <div className="space-y-2">
                  {weekly.map((day) => (
                    <div key={day.date} className="flex items-center gap-3">
                      <span className="text-undertow-400 text-sm w-24">
                        {new Date(day.date).toLocaleDateString("en-US", {
                          weekday: "short",
                          month: "short",
                          day: "numeric",
                        })}
                      </span>
                      <div className="flex-1 h-6 bg-undertow-800 rounded overflow-hidden">
                        <div
                          className={`h-full ${
                            day.budget_used_pct > 90
                              ? "bg-red-500"
                              : day.budget_used_pct > 70
                              ? "bg-yellow-500"
                              : "bg-accent-500"
                          }`}
                          style={{ width: `${Math.min(day.budget_used_pct, 100)}%` }}
                        />
                      </div>
                      <span className="text-undertow-100 text-sm w-20 text-right">
                        ${day.total_cost_usd.toFixed(2)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* By agent */}
              <div className="card">
                <h2 className="text-lg font-serif font-semibold mb-4">Cost by Agent</h2>
                {current?.by_agent && Object.keys(current.by_agent).length > 0 ? (
                  <div className="space-y-3">
                    {Object.entries(current.by_agent)
                      .sort(([, a], [, b]) => b - a)
                      .map(([agent, cost]) => {
                        const pct = (cost / current.total_cost_usd) * 100;
                        return (
                          <div key={agent}>
                            <div className="flex justify-between text-sm mb-1">
                              <span className="text-undertow-300">{agent}</span>
                              <span className="text-undertow-100">
                                ${cost.toFixed(4)} ({pct.toFixed(0)}%)
                              </span>
                            </div>
                            <div className="h-2 bg-undertow-800 rounded overflow-hidden">
                              <div
                                className="h-full bg-accent-500"
                                style={{ width: `${pct}%` }}
                              />
                            </div>
                          </div>
                        );
                      })}
                  </div>
                ) : (
                  <p className="text-undertow-400 text-center py-4">No agent costs yet</p>
                )}
              </div>
            </div>

            {/* By model */}
            <div className="card">
              <h2 className="text-lg font-serif font-semibold mb-4">Cost by Model</h2>
              {current?.by_model && Object.keys(current.by_model).length > 0 ? (
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {Object.entries(current.by_model)
                    .sort(([, a], [, b]) => b - a)
                    .map(([model, cost]) => (
                      <div
                        key={model}
                        className="p-4 bg-undertow-800/50 rounded-lg"
                      >
                        <div className="text-sm text-undertow-400 truncate mb-1">
                          {model}
                        </div>
                        <div className="text-xl font-bold text-undertow-100">
                          ${cost.toFixed(4)}
                        </div>
                      </div>
                    ))}
                </div>
              ) : (
                <p className="text-undertow-400 text-center py-4">No model costs yet</p>
              )}
            </div>
          </>
        )}
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

