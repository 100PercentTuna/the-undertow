"use client";

import { useEffect, useState } from "react";
import { FileText, Search, Filter, ChevronRight, Globe } from "lucide-react";
import Link from "next/link";

interface Story {
  id: string;
  headline: string;
  summary: string;
  source_name: string;
  primary_zone: string;
  status: string;
  relevance_score: number;
  created_at: string;
}

export default function StoriesPage() {
  const [stories, setStories] = useState<Story[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");
  const [search, setSearch] = useState("");

  useEffect(() => {
    fetchStories();
  }, [filter]);

  async function fetchStories() {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (filter !== "all") params.set("status", filter);

      const res = await fetch(`/api/v1/stories?${params}`);
      if (res.ok) {
        const data = await res.json();
        setStories(data.items || data || []);
      }
    } catch (e) {
      console.error("Failed to fetch stories", e);
    } finally {
      setLoading(false);
    }
  }

  const filteredStories = stories.filter(
    (s) =>
      s.headline.toLowerCase().includes(search.toLowerCase()) ||
      s.summary?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <main className="min-h-screen">
      {/* Header */}
      <header className="border-b border-undertow-800 bg-undertow-900/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-3">
              <Link href="/" className="flex items-center gap-3">
                <div className="w-8 h-8 bg-accent-600 rounded-lg flex items-center justify-center">
                  <FileText className="w-5 h-5 text-white" />
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
              <Link href="/stories" className="text-undertow-100 font-medium">
                Stories
              </Link>
              <Link href="/articles" className="text-undertow-400 hover:text-undertow-100">
                Articles
              </Link>
              <Link href="/pipeline" className="text-undertow-400 hover:text-undertow-100">
                Pipeline
              </Link>
            </nav>
          </div>
        </div>
      </header>

      {/* Main content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-serif font-bold">Stories</h1>
          <button className="btn btn-primary">Import Sources</button>
        </div>

        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-4 mb-6">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-undertow-500" />
            <input
              type="text"
              placeholder="Search stories..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="input w-full pl-10"
            />
          </div>
          <div className="flex gap-2">
            {["all", "pending", "analyzing", "analyzed", "published"].map((status) => (
              <button
                key={status}
                onClick={() => setFilter(status)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  filter === status
                    ? "bg-accent-600 text-white"
                    : "bg-undertow-800 text-undertow-300 hover:bg-undertow-700"
                }`}
              >
                {status.charAt(0).toUpperCase() + status.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {/* Stories list */}
        {loading ? (
          <div className="text-center py-12 text-undertow-400">Loading...</div>
        ) : filteredStories.length === 0 ? (
          <div className="text-center py-12">
            <FileText className="w-12 h-12 mx-auto mb-4 text-undertow-600" />
            <p className="text-undertow-400">No stories found</p>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredStories.map((story) => (
              <StoryCard key={story.id} story={story} />
            ))}
          </div>
        )}
      </div>
    </main>
  );
}

function StoryCard({ story }: { story: Story }) {
  const statusColors: Record<string, string> = {
    pending: "badge-info",
    analyzing: "badge-warning",
    analyzed: "badge-success",
    published: "badge-success",
    rejected: "badge-error",
  };

  return (
    <div className="card hover:border-undertow-600 transition-colors cursor-pointer group">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2">
            <span className={`badge ${statusColors[story.status] || "badge-info"}`}>
              {story.status}
            </span>
            {story.primary_zone && (
              <span className="flex items-center gap-1 text-xs text-undertow-400">
                <Globe className="w-3 h-3" />
                {story.primary_zone}
              </span>
            )}
          </div>
          <h3 className="text-lg font-semibold text-undertow-100 mb-2 line-clamp-2">
            {story.headline}
          </h3>
          {story.summary && (
            <p className="text-sm text-undertow-400 line-clamp-2 mb-3">
              {story.summary}
            </p>
          )}
          <div className="flex items-center gap-4 text-xs text-undertow-500">
            {story.source_name && <span>{story.source_name}</span>}
            {story.relevance_score && (
              <span>Relevance: {(story.relevance_score * 100).toFixed(0)}%</span>
            )}
            <span>{new Date(story.created_at).toLocaleDateString()}</span>
          </div>
        </div>
        <ChevronRight className="w-5 h-5 text-undertow-600 group-hover:text-undertow-400 transition-colors flex-shrink-0" />
      </div>
    </div>
  );
}

