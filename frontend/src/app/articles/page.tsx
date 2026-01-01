"use client";

import { useEffect, useState } from "react";
import { BookOpen, Search, ChevronRight, Check, Eye, Edit } from "lucide-react";
import Link from "next/link";

interface Article {
  id: string;
  headline: string;
  subhead: string;
  summary: string;
  status: string;
  quality_score: number;
  word_count: number;
  read_time_minutes: number;
  zones: string[];
  published_at: string | null;
  created_at: string;
}

export default function ArticlesPage() {
  const [articles, setArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");

  useEffect(() => {
    fetchArticles();
  }, [filter]);

  async function fetchArticles() {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (filter !== "all") params.set("status", filter);

      const res = await fetch(`/api/v1/articles?${params}`);
      if (res.ok) {
        const data = await res.json();
        setArticles(data.items || data || []);
      }
    } catch (e) {
      console.error("Failed to fetch articles", e);
    } finally {
      setLoading(false);
    }
  }

  async function approveArticle(id: string) {
    await fetch(`/api/v1/articles/${id}/approve`, { method: "POST" });
    fetchArticles();
  }

  async function publishArticle(id: string) {
    await fetch(`/api/v1/articles/${id}/publish`, { method: "POST" });
    fetchArticles();
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
                  <BookOpen className="w-5 h-5 text-white" />
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
              <Link href="/articles" className="text-undertow-100 font-medium">
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
          <h1 className="text-3xl font-serif font-bold">Articles</h1>
          <Link href="/newsletter" className="btn btn-primary">
            Preview Newsletter
          </Link>
        </div>

        {/* Filters */}
        <div className="flex gap-2 mb-6">
          {["all", "draft", "review", "approved", "published"].map((status) => (
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

        {/* Articles list */}
        {loading ? (
          <div className="text-center py-12 text-undertow-400">Loading...</div>
        ) : articles.length === 0 ? (
          <div className="text-center py-12">
            <BookOpen className="w-12 h-12 mx-auto mb-4 text-undertow-600" />
            <p className="text-undertow-400">No articles found</p>
          </div>
        ) : (
          <div className="space-y-4">
            {articles.map((article) => (
              <ArticleCard
                key={article.id}
                article={article}
                onApprove={() => approveArticle(article.id)}
                onPublish={() => publishArticle(article.id)}
              />
            ))}
          </div>
        )}
      </div>
    </main>
  );
}

function ArticleCard({
  article,
  onApprove,
  onPublish,
}: {
  article: Article;
  onApprove: () => void;
  onPublish: () => void;
}) {
  const statusColors: Record<string, string> = {
    draft: "badge-info",
    review: "badge-warning",
    approved: "badge-success",
    published: "badge-success",
    archived: "badge-error",
  };

  return (
    <div className="card">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2">
            <span className={`badge ${statusColors[article.status] || "badge-info"}`}>
              {article.status}
            </span>
            {article.quality_score && (
              <span className="text-xs text-undertow-400">
                Quality: {(article.quality_score * 100).toFixed(0)}%
              </span>
            )}
          </div>
          <h3 className="text-lg font-semibold text-undertow-100 mb-1">
            {article.headline}
          </h3>
          {article.subhead && (
            <p className="text-sm text-undertow-300 mb-2">{article.subhead}</p>
          )}
          {article.summary && (
            <p className="text-sm text-undertow-400 line-clamp-2 mb-3">
              {article.summary}
            </p>
          )}
          <div className="flex items-center gap-4 text-xs text-undertow-500">
            {article.word_count && <span>{article.word_count} words</span>}
            {article.read_time_minutes && (
              <span>{article.read_time_minutes} min read</span>
            )}
            {article.zones?.length > 0 && (
              <span>{article.zones.slice(0, 3).join(", ")}</span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <button className="p-2 rounded-lg bg-undertow-800 hover:bg-undertow-700 transition-colors">
            <Eye className="w-4 h-4" />
          </button>
          <button className="p-2 rounded-lg bg-undertow-800 hover:bg-undertow-700 transition-colors">
            <Edit className="w-4 h-4" />
          </button>
          {article.status === "review" && (
            <button
              onClick={onApprove}
              className="btn btn-primary text-sm py-1.5"
            >
              Approve
            </button>
          )}
          {article.status === "approved" && (
            <button
              onClick={onPublish}
              className="btn btn-primary text-sm py-1.5"
            >
              Publish
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

