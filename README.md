# The Undertow

**Intelligence for Serious People**

An AI-powered geopolitical intelligence system that produces a daily newsletter analyzing global events across 42 distinct zones. The Undertow traces causal chains far enough to reveal what game is actually being played.

---

## 🎯 What This Does

Every day at **4:30 AM Singapore Time**, The Undertow:

1. **Selects** 5 significant geopolitical stories
2. **Analyzes** each with 4-layer motivation analysis, chain mapping, and subtlety decoding
3. **Writes** complete analytical articles (1500-2000 words each)
4. **Delivers** a newsletter to your inbox by 5:30 AM SGT

**No human intervention required.** Fully automated.

---

## 💰 Cost

| Item | Monthly |
|------|---------|
| Cloud Server (AWS/Azure) | $7-15 |
| Anthropic API (~$0.30/day) | ~$10 |
| Email (Postmark/SendGrid) | Free - $15/mo |
| **Total** | **~$17-40/month** |

**AWS**: $10/month (2 GB RAM) | **Azure**: $7-15/month (1-4 GB RAM)

---

## 🚀 Quick Start

### Prerequisites

- Cloud Account: AWS or Azure
- Anthropic API Key ([get one here](https://console.anthropic.com))
- Email Provider: Postmark ($15/mo) or SendGrid (free - 100/day)

### 5-Minute Setup

1. **Get API Keys** (10 min)
   - Anthropic: Sign up → API Keys → Create → Add $15 credit
   - SendGrid: Sign up → API Keys → Create → Verify sender email

2. **Launch Cloud Server** (5 min)
   - **AWS**: Lightsail → Create Instance → Singapore, Ubuntu 22.04, $10/month
   - **Azure**: Virtual Machine → Southeast Asia, Ubuntu 22.04, B1s ($7/mo)
   - Name: "undertow"

3. **Install & Configure** (15 min)
   - Click "Connect" on your instance
   - Follow commands in [`DEPLOYMENT_GUIDE.md`](DEPLOYMENT_GUIDE.md)

**Full instructions**: 
- AWS: [`DEPLOYMENT_GUIDE.md`](DEPLOYMENT_GUIDE.md)
- Azure: [`AZURE_DEPLOYMENT.md`](AZURE_DEPLOYMENT.md)
- Quick: [`QUICK_START.md`](QUICK_START.md)
- **Which cloud?** See [`CLOUD_COMPARISON.md`](CLOUD_COMPARISON.md)

**Setting up GitHub?** See [`GITHUB_SETUP.md`](GITHUB_SETUP.md)

---

## 📁 Project Structure

```
undertow/
├── src/undertow/          # Main application code
│   ├── runner.py          # Automated daily runner
│   ├── config.py          # Configuration management
│   ├── core/              # Core pipeline logic
│   ├── llm/               # LLM provider integration
│   └── services/          # Newsletter, etc.
├── tests/                 # Test suite
├── requirements.txt      # Python dependencies
├── env.example            # Configuration template
├── alembic/               # Database migrations
├── DEPLOYMENT_GUIDE.md    # Step-by-step deployment
├── QUICK_START.md         # 5-minute overview
└── README.md              # This file
```

---

## 🏗️ Architecture

**Simplified for low cost (~$1/day):**

- **Single server** (AWS Lightsail)
- **Claude 3.5 Haiku** for analysis ($0.25/$1.25 per million tokens)
- **No caching** (not needed for daily content)
- **No human review** (fully automated)
- **No observability stack** (logs only)

See [`SOLUTION_ARCHITECTURE_SIMPLE.md`](SOLUTION_ARCHITECTURE_SIMPLE.md) for details.

---

## 📊 Daily Schedule

| Time (SGT) | Activity |
|------------|----------|
| 4:30 AM | Pipeline starts |
| 4:35 AM | Story selection complete |
| 5:15 AM | Articles generated |
| 5:20 AM | **Newsletter delivered** |

---

## 🔧 Configuration

Copy `env.example` to `.env` and fill in:

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Email Provider (choose one)
EMAIL_PROVIDER=postmark  # or "sendgrid"

# For Postmark (recommended):
POSTMARK_API_KEY=your-server-token
FROM_EMAIL=your-verified-email@domain.com

# For SendGrid (free tier):
# EMAIL_PROVIDER=sendgrid
# SENDGRID_API_KEY=SG.your-key-here
# FROM_EMAIL=your-verified-email@domain.com

NEWSLETTER_RECIPIENTS=you@email.com,friend@email.com

# Optional
DAILY_BUDGET=1.50
PIPELINE_START_HOUR=20  # 8:30 PM UTC = 4:30 AM SGT
```

**See [`EMAIL_SETUP.md`](EMAIL_SETUP.md) for detailed email provider setup.**

---

## 🧪 Testing

Run a test pipeline:

```bash
python -m undertow.cli pipeline run --test
```

Check status:

```bash
sudo systemctl status undertow
```

View logs:

```bash
sudo journalctl -u undertow -f
```

---

## 📚 Documentation

- [`QUICK_START.md`](QUICK_START.md) - 5-minute overview
- [`DEPLOYMENT_GUIDE.md`](DEPLOYMENT_GUIDE.md) - Complete step-by-step guide
- [`SOLUTION_ARCHITECTURE_SIMPLE.md`](SOLUTION_ARCHITECTURE_SIMPLE.md) - Technical architecture
- [`THE_UNDERTOW.md`](THE_UNDERTOW.md) - Project philosophy and methodology

---

## 🛠️ Development

### Setup Local Environment

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/undertow.git
cd undertow

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure
cp env.example .env
# Edit .env with your keys

# Initialize database
python -m alembic upgrade head
```

### Run Locally

```bash
# Run the daily pipeline manually
python -m undertow.runner

# Or use CLI
python -m undertow.cli pipeline run --test
```

---

## 📝 License

[Add your license here]

---

## 🤝 Contributing

[Add contribution guidelines if open source]

---

## 📧 Support

For issues or questions:
- Check [`DEPLOYMENT_GUIDE.md`](DEPLOYMENT_GUIDE.md) troubleshooting section
- Review logs: `sudo journalctl -u undertow -n 100`

---

## 🙏 Acknowledgments

Built for people who want to understand how the world actually works—and who know that understanding requires tracing the chains far enough to see what game is really being played.

---

**The Undertow: Intelligence for serious people.**
