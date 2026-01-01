"use client";

import { useEffect, useState } from "react";
import {
  Activity,
  Server,
  Clock,
  Play,
  Pause,
  XCircle,
  CheckCircle,
  RefreshCw,
  Layers,
} from "lucide-react";
import Link from "next/link";

interface Job {
  id: string;
  name: string;
  status: string;
  worker?: string;
  started_at?: string;
  eta?: string;
  args?: string;
}

interface Worker {
  name: string;
  status: string;
  active_tasks: number;
  registered_tasks: number;
  concurrency?: number;
  uptime?: number;
}

interface ScheduledTask {
  name: string;
  task: string;
  schedule: string;
}

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [workers, setWorkers] = useState<Worker[]>([]);
  const [scheduled, setScheduled] = useState<ScheduledTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000); // Refresh every 5s
    return () => clearInterval(interval);
  }, []);

  async function fetchData() {
    try {
      const [jobsRes, workersRes, scheduledRes] = await Promise.all([
        fetch("/api/v1/jobs"),
        fetch("/api/v1/jobs/workers"),
        fetch("/api/v1/jobs/scheduled"),
      ]);

      if (jobsRes.ok) {
        const data = await jobsRes.json();
        setJobs(data.jobs || []);
        if (data.error) setError(data.error);
      }

      if (workersRes.ok) {
        const data = await workersRes.json();
        setWorkers(data.workers || []);
      }

      if (scheduledRes.ok) {
        const data = await scheduledRes.json();
        setScheduled(data.tasks || []);
      }
    } catch (e) {
      console.error("Failed to fetch jobs", e);
      setError("Failed to connect to job queue");
    } finally {
      setLoading(false);
    }
  }

  async function revokeJob(taskId: string) {
    if (!confirm("Are you sure you want to cancel this job?")) return;

    try {
      await fetch(`/api/v1/jobs/tasks/${taskId}/revoke`, { method: "POST" });
      fetchData();
    } catch (e) {
      console.error("Failed to revoke job", e);
    }
  }

  const statusConfig: Record<string, { icon: React.ReactNode; color: string }> = {
    running: { icon: <Play className="w-4 h-4" />, color: "text-green-400" },
    scheduled: { icon: <Clock className="w-4 h-4" />, color: "text-yellow-400" },
    reserved: { icon: <Pause className="w-4 h-4" />, color: "text-blue-400" },
    success: { icon: <CheckCircle className="w-4 h-4" />, color: "text-green-400" },
    failure: { icon: <XCircle className="w-4 h-4" />, color: "text-red-400" },
  };

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
              <Link href="/jobs" className="text-undertow-100 font-medium">
                Jobs
              </Link>
            </nav>
          </div>
        </div>
      </header>

      {/* Main content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-serif font-bold">Background Jobs</h1>
            <p className="text-undertow-400 mt-1">
              Monitor Celery workers and tasks
            </p>
          </div>
          <button
            onClick={fetchData}
            className="btn btn-secondary flex items-center gap-2"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>

        {error && (
          <div className="card mb-6 border-yellow-800 bg-yellow-900/20">
            <div className="flex items-center gap-2 text-yellow-400">
              <Server className="w-4 h-4" />
              <span>{error}</span>
            </div>
          </div>
        )}

        {/* Workers */}
        <div className="card mb-6">
          <h2 className="text-lg font-serif font-semibold mb-4 flex items-center gap-2">
            <Server className="w-5 h-5 text-undertow-400" />
            Workers
          </h2>

          {workers.length === 0 ? (
            <p className="text-undertow-400 text-center py-4">
              No workers online
            </p>
          ) : (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {workers.map((worker) => (
                <div
                  key={worker.name}
                  className="p-4 bg-undertow-800/50 rounded-lg"
                >
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-2 h-2 rounded-full bg-green-400" />
                    <span className="font-medium text-undertow-100 truncate">
                      {worker.name}
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div>
                      <span className="text-undertow-400">Active</span>
                      <div className="text-undertow-100">{worker.active_tasks}</div>
                    </div>
                    <div>
                      <span className="text-undertow-400">Concurrency</span>
                      <div className="text-undertow-100">{worker.concurrency || "—"}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Active jobs */}
        <div className="card mb-6">
          <h2 className="text-lg font-serif font-semibold mb-4 flex items-center gap-2">
            <Play className="w-5 h-5 text-undertow-400" />
            Active Jobs
          </h2>

          {jobs.length === 0 ? (
            <p className="text-undertow-400 text-center py-4">
              No active jobs
            </p>
          ) : (
            <div className="space-y-2">
              {jobs.map((job) => {
                const config = statusConfig[job.status] || statusConfig.reserved;
                return (
                  <div
                    key={job.id}
                    className="flex items-center justify-between p-3 bg-undertow-800/50 rounded-lg"
                  >
                    <div className="flex items-center gap-3">
                      <span className={config.color}>{config.icon}</span>
                      <div>
                        <div className="text-undertow-100 font-medium">
                          {job.name}
                        </div>
                        <div className="text-sm text-undertow-400">
                          {job.id?.slice(0, 8)}...
                          {job.worker && ` • ${job.worker}`}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`text-sm ${config.color}`}>
                        {job.status}
                      </span>
                      {job.status === "running" && (
                        <button
                          onClick={() => revokeJob(job.id)}
                          className="p-1 text-red-400 hover:text-red-300"
                          title="Cancel job"
                        >
                          <XCircle className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Scheduled tasks */}
        <div className="card">
          <h2 className="text-lg font-serif font-semibold mb-4 flex items-center gap-2">
            <Layers className="w-5 h-5 text-undertow-400" />
            Scheduled Tasks
          </h2>

          {scheduled.length === 0 ? (
            <p className="text-undertow-400 text-center py-4">
              No scheduled tasks configured
            </p>
          ) : (
            <div className="space-y-2">
              {scheduled.map((task) => (
                <div
                  key={task.name}
                  className="flex items-center justify-between p-3 bg-undertow-800/50 rounded-lg"
                >
                  <div>
                    <div className="text-undertow-100 font-medium">
                      {task.name}
                    </div>
                    <div className="text-sm text-undertow-400">
                      {task.task}
                    </div>
                  </div>
                  <div className="text-sm text-undertow-400">
                    {task.schedule}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </main>
  );
}

