# The Undertow - Quick Start

## 5-Minute Summary

**What this does**: Automatically produces a daily geopolitical intelligence newsletter.

**Cost**: ~$25/month total ($10 AWS + ~$15 AI)

**Schedule**: Newsletter arrives in your inbox by 5:30 AM Singapore time, every day.

---

## What You Need

1. ✅ AWS Account (you have this)
2. 📝 Anthropic API Key (~$10-15/month)
3. 📝 Gmail Account (free - for sending emails)
4. ⏱️ 30 minutes to set up

---

## The 3 Steps

### Step 1: Get API Keys (10 min)

**Anthropic** (for AI):
1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Sign up → API Keys → Create Key
3. Add $15 credit (Settings → Billing)
4. Save the key (starts with `sk-ant-...`)

**Email Provider** (choose one):

**Gmail** (FREE - recommended):
1. [myaccount.google.com](https://myaccount.google.com) → Security → 2-Step Verification
2. App passwords → Mail → "The Undertow"
3. Save 16-character password

**O365** (FREE if you have account):
1. [account.microsoft.com](https://account.microsoft.com) → Security
2. App passwords → Create → "The Undertow"
3. Save password

**Postmark** (PAID - $15/month):
1. [postmarkapp.com](https://postmarkapp.com) → Sign up
2. Create server → Copy Server API Token

See [`EMAIL_SETUP.md`](EMAIL_SETUP.md) for details.

### Step 2: Launch Server (5 min)

**Choose AWS or Azure:**

**AWS** (Recommended):
1. Log into AWS → Search "Lightsail" → Create Instance
2. Choose: **Singapore**, **Ubuntu 22.04**, **$10/month**
3. Name it "undertow" → Create
4. Wait 2 minutes

**Azure** (Alternative):
1. Log into Azure Portal → Create resource → Virtual Machine
2. Choose: **Southeast Asia**, **Ubuntu 22.04**, **B1s ($7/mo)** or **B1ms ($15/mo)**
3. Name it "undertow" → Create
4. Wait 2 minutes

See [`AZURE_DEPLOYMENT.md`](AZURE_DEPLOYMENT.md) for detailed Azure instructions.

### Step 3: Install & Configure (15 min)

**For AWS**: Click "Connect" on your Lightsail instance  
**For Azure**: SSH to your VM (see [`AZURE_DEPLOYMENT.md`](AZURE_DEPLOYMENT.md))

Then paste these commands:

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
# → Set EMAIL_PROVIDER (smtp or postmark)
# → If SMTP: Add SMTP_USERNAME, SMTP_PASSWORD, FROM_EMAIL
# → If Postmark: Add POSTMARK_API_KEY
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
| Cloud Server (AWS/Azure) | $7-15 |
| Anthropic API (~$0.30/day) | ~$10 |
| Email (Gmail/O365/Postmark) | Free - $15/mo |
| **Total** | **~$17-40/month** |

**AWS**: $10/month (2 GB RAM)  
**Azure**: $7-15/month (1-4 GB RAM)

---

## Questions?

**Newsletter didn't arrive?**
- Check logs: `sudo journalctl -u undertow -n 50`
- Verify Gmail App Password is correct (no spaces)
- Check spam folder
- Verify SMTP_USERNAME matches FROM_EMAIL

**Costs too high?**
- Check `.env` has `DAILY_BUDGET=1.50`
- The system auto-stops if budget exceeded

**Want to change the schedule?**
- Edit `.env`: `PIPELINE_START_HOUR` (UTC)
- SGT = UTC + 8 hours

