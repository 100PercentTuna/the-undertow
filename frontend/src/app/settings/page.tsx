"use client";

import { useState, useEffect } from "react";

interface SystemSettings {
  // Pipeline settings
  daily_article_count: number;
  pipeline_start_hour: number;
  newsletter_publish_hour: number;
  
  // Quality thresholds
  foundation_gate: number;
  analysis_gate: number;
  adversarial_gate: number;
  output_gate: number;
  
  // Cost settings
  daily_budget: number;
  cost_per_article_target: number;
  
  // Model settings
  default_provider: "anthropic" | "openai" | "best_fit";
  frontier_model: string;
  high_model: string;
  standard_model: string;
  fast_model: string;
  
  // Notification settings
  alert_email: string;
  slack_webhook_enabled: boolean;
  webhook_url: string;
}

const defaultSettings: SystemSettings = {
  daily_article_count: 5,
  pipeline_start_hour: 4,
  newsletter_publish_hour: 10,
  
  foundation_gate: 0.75,
  analysis_gate: 0.80,
  adversarial_gate: 0.80,
  output_gate: 0.85,
  
  daily_budget: 50,
  cost_per_article_target: 2.0,
  
  default_provider: "anthropic",
  frontier_model: "claude-sonnet-4-20250514",
  high_model: "claude-sonnet-4-20250514",
  standard_model: "gpt-4o-mini",
  fast_model: "claude-3-5-haiku-20241022",
  
  alert_email: "",
  slack_webhook_enabled: false,
  webhook_url: "",
};

export default function SettingsPage() {
  const [settings, setSettings] = useState<SystemSettings>(defaultSettings);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [activeTab, setActiveTab] = useState<"pipeline" | "quality" | "models" | "notifications">("pipeline");

  useEffect(() => {
    // Load settings from API
    loadSettings();
  }, []);

  async function loadSettings() {
    try {
      // In production, this would fetch from the API
      const stored = localStorage.getItem("undertow_settings");
      if (stored) {
        setSettings(JSON.parse(stored));
      }
    } catch (error) {
      console.error("Failed to load settings:", error);
    }
  }

  async function saveSettings() {
    setSaving(true);
    try {
      // In production, this would POST to the API
      localStorage.setItem("undertow_settings", JSON.stringify(settings));
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (error) {
      console.error("Failed to save settings:", error);
    } finally {
      setSaving(false);
    }
  }

  function updateSetting<K extends keyof SystemSettings>(key: K, value: SystemSettings[K]) {
    setSettings({ ...settings, [key]: value });
  }

  const tabs = [
    { id: "pipeline", label: "Pipeline", icon: "⚙️" },
    { id: "quality", label: "Quality Gates", icon: "🎯" },
    { id: "models", label: "AI Models", icon: "🤖" },
    { id: "notifications", label: "Notifications", icon: "🔔" },
  ] as const;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="bg-slate-900 border-b border-slate-800">
        <div className="max-w-4xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-amber-400">Settings</h1>
              <p className="text-slate-400 text-sm">
                Configure system behavior
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

      <main className="max-w-4xl mx-auto px-6 py-8">
        {/* Tabs */}
        <div className="flex gap-2 mb-8 border-b border-slate-800 pb-4">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                activeTab === tab.id
                  ? "bg-amber-600 text-white"
                  : "bg-slate-800 text-slate-400 hover:bg-slate-700"
              }`}
            >
              {tab.icon} {tab.label}
            </button>
          ))}
        </div>

        <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
          {/* Pipeline Settings */}
          {activeTab === "pipeline" && (
            <div className="space-y-6">
              <h2 className="text-lg font-semibold border-b border-slate-800 pb-2">
                Pipeline Configuration
              </h2>

              <div className="grid grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm text-slate-400 mb-2">
                    Daily Article Count
                  </label>
                  <input
                    type="number"
                    min={1}
                    max={20}
                    value={settings.daily_article_count}
                    onChange={(e) => updateSetting("daily_article_count", parseInt(e.target.value))}
                    className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2"
                  />
                  <p className="text-xs text-slate-500 mt-1">
                    Number of feature articles per day
                  </p>
                </div>

                <div>
                  <label className="block text-sm text-slate-400 mb-2">
                    Pipeline Start (UTC)
                  </label>
                  <select
                    value={settings.pipeline_start_hour}
                    onChange={(e) => updateSetting("pipeline_start_hour", parseInt(e.target.value))}
                    className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2"
                  >
                    {Array.from({ length: 24 }, (_, i) => (
                      <option key={i} value={i}>
                        {i.toString().padStart(2, "0")}:00 UTC
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm text-slate-400 mb-2">
                    Newsletter Publish (UTC)
                  </label>
                  <select
                    value={settings.newsletter_publish_hour}
                    onChange={(e) => updateSetting("newsletter_publish_hour", parseInt(e.target.value))}
                    className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2"
                  >
                    {Array.from({ length: 24 }, (_, i) => (
                      <option key={i} value={i}>
                        {i.toString().padStart(2, "0")}:00 UTC
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm text-slate-400 mb-2">
                    Daily Budget (USD)
                  </label>
                  <input
                    type="number"
                    min={1}
                    max={500}
                    value={settings.daily_budget}
                    onChange={(e) => updateSetting("daily_budget", parseInt(e.target.value))}
                    className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Quality Gates */}
          {activeTab === "quality" && (
            <div className="space-y-6">
              <h2 className="text-lg font-semibold border-b border-slate-800 pb-2">
                Quality Gate Thresholds
              </h2>
              <p className="text-sm text-slate-400">
                Minimum quality scores required to pass each gate. Articles below threshold will be escalated for human review.
              </p>

              <div className="space-y-4">
                {[
                  { key: "foundation_gate" as const, label: "Foundation Gate", desc: "Facts, timeline, actors" },
                  { key: "analysis_gate" as const, label: "Analysis Gate", desc: "Motivation, chains, subtleties" },
                  { key: "adversarial_gate" as const, label: "Adversarial Gate", desc: "Debate complete, verified" },
                  { key: "output_gate" as const, label: "Output Gate", desc: "Voice, structure, citations" },
                ].map(({ key, label, desc }) => (
                  <div key={key} className="bg-slate-800/50 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div>
                        <span className="font-medium">{label}</span>
                        <span className="text-slate-500 text-sm ml-2">({desc})</span>
                      </div>
                      <span className="text-amber-400 font-mono">
                        {(settings[key] * 100).toFixed(0)}%
                      </span>
                    </div>
                    <input
                      type="range"
                      min={50}
                      max={99}
                      value={settings[key] * 100}
                      onChange={(e) => updateSetting(key, parseInt(e.target.value) / 100)}
                      className="w-full accent-amber-500"
                    />
                    <div className="flex justify-between text-xs text-slate-500 mt-1">
                      <span>50%</span>
                      <span>99%</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* AI Models */}
          {activeTab === "models" && (
            <div className="space-y-6">
              <h2 className="text-lg font-semibold border-b border-slate-800 pb-2">
                AI Model Configuration
              </h2>

              <div>
                <label className="block text-sm text-slate-400 mb-2">
                  Default Provider
                </label>
                <select
                  value={settings.default_provider}
                  onChange={(e) => updateSetting("default_provider", e.target.value as any)}
                  className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2"
                >
                  <option value="anthropic">Anthropic (Claude)</option>
                  <option value="openai">OpenAI (GPT)</option>
                  <option value="best_fit">Best Fit (Auto-select)</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                {[
                  { key: "frontier_model" as const, label: "Frontier Tier", desc: "Motivation, debates, writing" },
                  { key: "high_model" as const, label: "High Tier", desc: "Theory, fact-checking" },
                  { key: "standard_model" as const, label: "Standard Tier", desc: "Context, verification" },
                  { key: "fast_model" as const, label: "Fast Tier", desc: "Scouts, aggregation" },
                ].map(({ key, label, desc }) => (
                  <div key={key}>
                    <label className="block text-sm text-slate-400 mb-2">
                      {label}
                      <span className="text-xs text-slate-500 block">{desc}</span>
                    </label>
                    <input
                      type="text"
                      value={settings[key]}
                      onChange={(e) => updateSetting(key, e.target.value)}
                      className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm font-mono"
                    />
                  </div>
                ))}
              </div>

              <div className="bg-slate-800/30 rounded p-4 text-sm">
                <p className="text-slate-400">
                  <strong className="text-amber-400">Cost impact:</strong> Frontier models cost ~10x more than fast tier.
                  Balance quality vs. cost by adjusting model assignments.
                </p>
              </div>
            </div>
          )}

          {/* Notifications */}
          {activeTab === "notifications" && (
            <div className="space-y-6">
              <h2 className="text-lg font-semibold border-b border-slate-800 pb-2">
                Notification Settings
              </h2>

              <div>
                <label className="block text-sm text-slate-400 mb-2">
                  Alert Email
                </label>
                <input
                  type="email"
                  value={settings.alert_email}
                  onChange={(e) => updateSetting("alert_email", e.target.value)}
                  placeholder="alerts@example.com"
                  className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2"
                />
                <p className="text-xs text-slate-500 mt-1">
                  Receives escalation and pipeline failure alerts
                </p>
              </div>

              <div className="flex items-center justify-between bg-slate-800/50 rounded-lg p-4">
                <div>
                  <span className="font-medium">Slack Notifications</span>
                  <p className="text-xs text-slate-500">
                    Send notifications to Slack channel
                  </p>
                </div>
                <button
                  onClick={() => updateSetting("slack_webhook_enabled", !settings.slack_webhook_enabled)}
                  className={`relative w-12 h-6 rounded-full transition-colors ${
                    settings.slack_webhook_enabled ? "bg-amber-500" : "bg-slate-600"
                  }`}
                >
                  <span
                    className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-transform ${
                      settings.slack_webhook_enabled ? "left-7" : "left-1"
                    }`}
                  />
                </button>
              </div>

              {settings.slack_webhook_enabled && (
                <div>
                  <label className="block text-sm text-slate-400 mb-2">
                    Slack Webhook URL
                  </label>
                  <input
                    type="url"
                    value={settings.webhook_url}
                    onChange={(e) => updateSetting("webhook_url", e.target.value)}
                    placeholder="https://hooks.slack.com/services/..."
                    className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2"
                  />
                </div>
              )}
            </div>
          )}
        </div>

        {/* Save Button */}
        <div className="flex justify-end gap-4 mt-6">
          {saved && (
            <span className="text-green-400 flex items-center gap-2">
              ✓ Settings saved
            </span>
          )}
          <button
            onClick={saveSettings}
            disabled={saving}
            className="bg-amber-600 hover:bg-amber-500 px-6 py-2 rounded font-medium transition-colors disabled:opacity-50"
          >
            {saving ? "Saving..." : "Save Settings"}
          </button>
        </div>
      </main>
    </div>
  );
}

