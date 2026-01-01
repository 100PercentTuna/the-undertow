# The Undertow - Deployment Guide

## Complete Step-by-Step Instructions (No Technical Background Required)

This guide will help you deploy The Undertow on AWS. It will run automatically every day and deliver your newsletter by 4:30 AM Singapore time.

---

## What You'll Need

1. **An AWS Account** (you have this ✓)
2. **An Anthropic API Key** (for AI - costs ~$1/day)
3. **A Gmail Account** (free - for sending emails)
4. **About 30 minutes** to set everything up

---

## Part 1: Get Your API Keys

### Step 1.1: Get Anthropic API Key

1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Click "Sign Up" and create an account
3. Once logged in, click "API Keys" in the left menu
4. Click "Create Key"
5. Name it "undertow" and click Create
6. **Copy the key** (starts with `sk-ant-...`) and save it somewhere safe
7. Add $10-20 credit to your account (Settings → Billing)

### Step 1.2: Set Up Gmail for Sending Emails (FREE)

**Gmail is completely free and allows 500 emails per day** - more than enough for a daily newsletter.

1. **Enable 2-Factor Authentication** (required for App Passwords):
   - Go to [myaccount.google.com](https://myaccount.google.com)
   - Click "Security" in the left menu
   - Under "Signing in to Google", click "2-Step Verification"
   - Follow the prompts to enable it

2. **Generate an App Password**:
   - Still in Security settings, scroll down to "App passwords"
   - Click "App passwords"
   - Select "Mail" and "Other (Custom name)"
   - Type "The Undertow" and click "Generate"
   - **Copy the 16-character password** (looks like: `abcd efgh ijkl mnop`)
   - Save this password - you'll use it in the `.env` file

3. **Note your Gmail address** - this will be your `FROM_EMAIL` and `SMTP_USERNAME`

---

## Part 2: Deploy on AWS

### Step 2.1: Launch AWS Lightsail Instance

1. Log into [AWS Console](https://aws.amazon.com/console/)
2. Search for "Lightsail" in the top search bar and click it
3. Click "Create instance"
4. Choose these settings:
   - **Region**: Singapore (ap-southeast-1)
   - **Platform**: Linux/Unix
   - **Blueprint**: OS Only → Ubuntu 22.04 LTS
   - **Instance plan**: $10/month (2 GB RAM, 1 vCPU)
   - **Instance name**: undertow
5. Click "Create instance"
6. Wait 2-3 minutes for it to start

### Step 2.2: Connect to Your Server

1. In Lightsail, click on your "undertow" instance
2. Click the orange "Connect using SSH" button
3. A black terminal window will open - you're now connected!

### Step 2.3: Install The Undertow

Copy and paste these commands ONE BY ONE into the terminal (press Enter after each):

```bash
# Update the system
sudo apt update && sudo apt upgrade -y

# Install required software
sudo apt install -y python3.11 python3.11-venv python3-pip postgresql postgresql-contrib redis-server git

# Start database services
sudo systemctl start postgresql redis-server
sudo systemctl enable postgresql redis-server

# Create database
sudo -u postgres createuser undertow
sudo -u postgres createdb undertow -O undertow
sudo -u postgres psql -c "ALTER USER undertow PASSWORD 'undertow123';"

# Download The Undertow
cd ~
git clone https://github.com/YOUR_USERNAME/undertow.git
cd undertow

# Create Python environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2.4: Configure The Undertow

Create the configuration file:

```bash
nano .env
```

Paste this (replace the values in CAPS with your actual keys):

```
# AI Provider
ANTHROPIC_API_KEY=YOUR_ANTHROPIC_KEY_HERE

# Email (Gmail SMTP - FREE)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-16-char-app-password
SMTP_USE_TLS=true
FROM_EMAIL=your-email@gmail.com
NEWSLETTER_RECIPIENTS=recipient1@email.com,recipient2@email.com

# Database (don't change these)
DATABASE_URL=postgresql://undertow:undertow123@localhost:5432/undertow
REDIS_URL=redis://localhost:6379/0

# Schedule (runs at 8:30 PM UTC = 4:30 AM SGT next day)
PIPELINE_START_HOUR=20
PIPELINE_START_MINUTE=30

# Cost limit ($1/day)
DAILY_BUDGET=1.00
```

**Important**: 
- `SMTP_USERNAME` = Your Gmail address
- `SMTP_PASSWORD` = The 16-character App Password you generated (remove spaces)
- `FROM_EMAIL` = Same as `SMTP_USERNAME`

Save the file: Press `Ctrl+X`, then `Y`, then `Enter`

### Step 2.5: Initialize the Database

```bash
source venv/bin/activate
cd ~/undertow
python -m alembic upgrade head
```

### Step 2.6: Set Up Automatic Running

Create a service file:

```bash
sudo nano /etc/systemd/system/undertow.service
```

Paste this:

```ini
[Unit]
Description=The Undertow Intelligence System
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/undertow
Environment=PATH=/home/ubuntu/undertow/venv/bin
ExecStart=/home/ubuntu/undertow/venv/bin/python -m undertow.runner
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Save: `Ctrl+X`, `Y`, `Enter`

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable undertow
sudo systemctl start undertow
```

### Step 2.7: Verify It's Running

```bash
sudo systemctl status undertow
```

You should see "active (running)" in green.

---

## Part 3: Test It

### Run a Manual Test

```bash
cd ~/undertow
source venv/bin/activate
python -m undertow.cli pipeline run --test
```

This will run the pipeline once and send you a test newsletter.

---

## Daily Schedule

The system runs automatically:
- **8:30 PM UTC** (4:30 AM SGT): Pipeline starts
- **~4:00 AM SGT**: Analysis complete
- **4:30 AM SGT**: Newsletter sent to your inbox

---

## Cost Breakdown

| Item | Monthly Cost |
|------|-------------|
| AWS Lightsail | $10 |
| Anthropic API (~$1/day) | ~$30 |
| SendGrid | Free (up to 100 emails/day) |
| **Total** | **~$40/month** |

---

## Troubleshooting

### Check if it's running
```bash
sudo systemctl status undertow
```

### View recent logs
```bash
sudo journalctl -u undertow -n 100
```

### Restart the service
```bash
sudo systemctl restart undertow
```

### Check today's cost
```bash
cd ~/undertow && source venv/bin/activate
python -m undertow.cli costs summary
```

---

## Getting Help

If something goes wrong:
1. Check the logs: `sudo journalctl -u undertow -n 100`
2. The error message will tell you what's wrong
3. Common fixes:
   - "API key invalid" → Check your `.env` file
   - "Database error" → Run `sudo systemctl restart postgresql`
   - "Email failed" → Verify your SendGrid sender email

---

## Updating The Undertow

When updates are available:

```bash
cd ~/undertow
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart undertow
```

---

*That's it! Your intelligence system is now running automatically.*

