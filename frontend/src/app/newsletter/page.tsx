"use client";

import { useEffect, useState } from "react";
import {
  Activity,
  Mail,
  Eye,
  Send,
  Calendar,
  FileText,
  RefreshCw,
} from "lucide-react";
import Link from "next/link";

interface NewsletterPreview {
  date: string;
  subject: string;
  preview_text: string;
  article_count: number;
  html_content: string;
  text_content: string;
  estimated_read_time: number;
}

export default function NewsletterPage() {
  const [preview, setPreview] = useState<NewsletterPreview | null>(null);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [viewMode, setViewMode] = useState<"html" | "text">("html");
  const [selectedDate, setSelectedDate] = useState(
    new Date().toISOString().split("T")[0]
  );

  useEffect(() => {
    fetchPreview();
  }, [selectedDate]);

  async function fetchPreview() {
    setLoading(true);
    try {
      const res = await fetch(`/api/v1/newsletter/preview?date=${selectedDate}`);
      if (res.ok) {
        setPreview(await res.json());
      } else {
        setPreview(null);
      }
    } catch (e) {
      console.error("Failed to fetch preview", e);
      setPreview(null);
    } finally {
      setLoading(false);
    }
  }

  async function sendNewsletter() {
    if (!confirm("Are you sure you want to send this newsletter?")) return;

    setSending(true);
    try {
      const res = await fetch("/api/v1/newsletter/send", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ date: selectedDate }),
      });

      if (res.ok) {
        alert("Newsletter sent successfully!");
      } else {
        const error = await res.json();
        alert(`Failed to send: ${error.detail}`);
      }
    } catch (e) {
      console.error("Failed to send", e);
      alert("Failed to send newsletter");
    } finally {
      setSending(false);
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
              <Link href="/articles" className="text-undertow-400 hover:text-undertow-100">
                Articles
              </Link>
              <Link href="/newsletter" className="text-undertow-100 font-medium">
                Newsletter
              </Link>
            </nav>
          </div>
        </div>
      </header>

      {/* Main content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-serif font-bold">Newsletter</h1>
            <p className="text-undertow-400 mt-1">
              Preview and send the daily newsletter
            </p>
          </div>
        </div>

        {/* Controls */}
        <div className="flex flex-wrap gap-4 mb-8">
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 text-undertow-400" />
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="px-3 py-2 bg-undertow-800 border border-undertow-700 rounded-lg text-undertow-100 focus:outline-none focus:border-accent-500"
            />
          </div>

          <button
            onClick={fetchPreview}
            disabled={loading}
            className="btn btn-secondary flex items-center gap-2"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>

          <div className="flex rounded-lg overflow-hidden border border-undertow-700">
            <button
              onClick={() => setViewMode("html")}
              className={`px-4 py-2 text-sm ${
                viewMode === "html"
                  ? "bg-accent-600 text-white"
                  : "bg-undertow-800 text-undertow-400"
              }`}
            >
              HTML
            </button>
            <button
              onClick={() => setViewMode("text")}
              className={`px-4 py-2 text-sm ${
                viewMode === "text"
                  ? "bg-accent-600 text-white"
                  : "bg-undertow-800 text-undertow-400"
              }`}
            >
              Plain Text
            </button>
          </div>

          <div className="flex-1" />

          <button
            onClick={sendNewsletter}
            disabled={!preview || sending}
            className="btn btn-primary flex items-center gap-2 disabled:opacity-50"
          >
            {sending ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
            Send Newsletter
          </button>
        </div>

        {loading ? (
          <div className="text-center py-16 text-undertow-400">
            <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4" />
            Generating preview...
          </div>
        ) : !preview ? (
          <div className="card text-center py-16">
            <FileText className="w-12 h-12 text-undertow-600 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-undertow-300 mb-2">
              No newsletter for this date
            </h3>
            <p className="text-undertow-400">
              Run the pipeline to generate articles first.
            </p>
          </div>
        ) : (
          <>
            {/* Preview metadata */}
            <div className="card mb-6">
              <div className="grid md:grid-cols-4 gap-4">
                <div>
                  <span className="text-undertow-400 text-sm">Subject</span>
                  <div className="text-undertow-100 font-medium">
                    {preview.subject}
                  </div>
                </div>
                <div>
                  <span className="text-undertow-400 text-sm">Articles</span>
                  <div className="text-undertow-100 font-medium">
                    {preview.article_count}
                  </div>
                </div>
                <div>
                  <span className="text-undertow-400 text-sm">Read Time</span>
                  <div className="text-undertow-100 font-medium">
                    {preview.estimated_read_time} min
                  </div>
                </div>
                <div>
                  <span className="text-undertow-400 text-sm">Preview Text</span>
                  <div className="text-undertow-100 font-medium truncate">
                    {preview.preview_text}
                  </div>
                </div>
              </div>
            </div>

            {/* Preview content */}
            <div className="card">
              <div className="flex items-center gap-2 mb-4">
                <Eye className="w-4 h-4 text-undertow-400" />
                <span className="text-undertow-400 text-sm">
                  {viewMode === "html" ? "HTML Preview" : "Plain Text Preview"}
                </span>
              </div>

              {viewMode === "html" ? (
                <div
                  className="newsletter-preview bg-white rounded-lg p-8 text-gray-900"
                  dangerouslySetInnerHTML={{ __html: preview.html_content }}
                />
              ) : (
                <pre className="bg-undertow-800 rounded-lg p-6 text-undertow-300 overflow-x-auto whitespace-pre-wrap font-mono text-sm">
                  {preview.text_content}
                </pre>
              )}
            </div>
          </>
        )}
      </div>

      <style jsx global>{`
        .newsletter-preview h1 {
          font-size: 1.5rem;
          font-weight: bold;
          margin-bottom: 1rem;
        }
        .newsletter-preview h2 {
          font-size: 1.25rem;
          font-weight: bold;
          margin-top: 1.5rem;
          margin-bottom: 0.75rem;
        }
        .newsletter-preview p {
          margin-bottom: 1rem;
          line-height: 1.6;
        }
        .newsletter-preview a {
          color: #2563eb;
          text-decoration: underline;
        }
      `}</style>
    </main>
  );
}

