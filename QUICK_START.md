# The Undertow - Quick Start

## 5-Minute Summary

**What this does**: Automatically produces a daily geopolitical intelligence newsletter.

**Cost**: ~$25/month total ($10 AWS + ~$15 AI)

**Schedule**: Newsletter arrives in your inbox by 5:30 AM Singapore time, every day.

---

## What You Need

1. ✅ AWS Account (you have this)
2. 📝 Anthropic API Key (~$10-15/month)
3. 📝 SendGrid Account (free)
4. ⏱️ 30 minutes to set up

---

## The 3 Steps

### Step 1: Get API Keys (10 min)

**Anthropic** (for AI):
1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Sign up → API Keys → Create Key
3. Add $15 credit (Settings → Billing)
4. Save the key (starts with `sk-ant-...`)

**SendGrid** (for email):
1. Go to [sendgrid.com](https://sendgrid.com)
2. Sign up (free) → Settings → API Keys → Create
3. Verify your sender email
4. Save the key (starts with `SG.`)

### Step 2: Launch Server (5 min)

1. Log into AWS → Search "Lightsail" → Create Instance
2. Choose: **Singapore**, **Ubuntu 22.04**, **$10/month**
3. Name it "undertow" → Create
4. Wait 2 minutes

### Step 3: Install & Configure (15 min)

Click "Connect" on your Lightsail instance, then paste these commands:

```bash
# One-time setup
sudo apt update && sudo apt install -y python3.11 python3.11-venv postgresql redis-server git
sudo systemctl start postgresql redis-server
sudo -u postgres createuser undertow
sudo -u postgres createdb undertow -O undertow
sudo -u postgres psql -c "ALTER USER undertow PASSWORD 'undertow123';"

# Download and install
git clone https://github.com/YOUR_USERNAME/undertow.git
cd undertow
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure (edit this file with your keys)
cp env.example .env
nano .env
# → Add your ANTHROPIC_API_KEY
# → Add your SENDGRID_API_KEY  
# → Add your FROM_EMAIL
# → Add your NEWSLETTER_RECIPIENTS
# → Save: Ctrl+X, Y, Enter

# Initialize database
python -m alembic upgrade head

# Start the service
sudo cp undertow.service /etc/systemd/system/
sudo systemctl enable undertow
sudo systemctl start undertow
```

---

## Done!

Your newsletter will arrive tomorrow at ~5:30 AM SGT.

### Check if it's running:
```bash
sudo systemctl status undertow
```

### Run a test:
```bash
cd ~/undertow && source venv/bin/activate
python -m undertow.cli pipeline run --test
```

### View logs:
```bash
sudo journalctl -u undertow -f
```

---

## Cost Breakdown

| Item | Monthly |
|------|---------|
| AWS Lightsail (Singapore) | $10 |
| Anthropic API (~$0.30/day) | ~$10 |
| SendGrid | Free |
| **Total** | **~$20/month** |

---

## Questions?

**Newsletter didn't arrive?**
- Check logs: `sudo journalctl -u undertow -n 50`
- Verify SendGrid sender email is verified
- Check spam folder

**Costs too high?**
- Check `.env` has `DAILY_BUDGET=1.50`
- The system auto-stops if budget exceeded

**Want to change the schedule?**
- Edit `.env`: `PIPELINE_START_HOUR` (UTC)
- SGT = UTC + 8 hours

