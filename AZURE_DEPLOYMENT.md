# Azure Deployment Guide

Complete step-by-step instructions for deploying The Undertow on Microsoft Azure.

---

## What You'll Need

1. **An Azure Account** ([Sign up free](https://azure.microsoft.com/free/) - $200 credit for 30 days)
2. **An Anthropic API Key** (for AI - costs ~$1/day)
3. **Email Provider** (Gmail/O365/Postmark)
4. **About 30 minutes** to set everything up

---

## Part 1: Get Your API Keys

Same as AWS deployment - see [`DEPLOYMENT_GUIDE.md`](DEPLOYMENT_GUIDE.md#part-1-get-your-api-keys)

---

## Part 2: Deploy on Azure

### Step 2.1: Create Azure Virtual Machine

1. Log into [Azure Portal](https://portal.azure.com)
2. Click "Create a resource" (top left, green button)
3. Search for "Virtual Machine" and click it
4. Click "Create" → "Virtual machine"

5. Fill in the **Basics** tab:
   - **Subscription**: Your subscription (or create free one)
   - **Resource group**: Create new → Name it "undertow-rg"
   - **Virtual machine name**: undertow
   - **Region**: Southeast Asia (Singapore)
   - **Image**: Ubuntu Server 22.04 LTS
   - **Size**: Click "See all sizes" → Search "B1s" → Select "Standard_B1s" (1 vCPU, 1 GB RAM, ~$7/month)
   - **Authentication type**: SSH public key (or Password if easier)
   - **Username**: azureuser
   - **SSH public key**: Generate or paste your key (or use password)

6. Click "Next: Disks" (bottom)
   - Keep defaults (Standard SSD, 30 GB is fine)

7. Click "Next: Networking" (bottom)
   - Keep defaults (public IP, allow SSH)

8. Click "Next: Management" (bottom)
   - Keep defaults

9. Click "Review + create" (bottom)
10. Click "Create"
11. Wait 2-3 minutes for deployment

### Step 2.2: Connect to Your Server

**Option A: Azure Cloud Shell (Easiest)**

1. In Azure Portal, click the `>_` icon (top right) to open Cloud Shell
2. Select "Bash"
3. Run: `ssh azureuser@YOUR_VM_IP_ADDRESS`
   - Find IP: Virtual machines → undertow → Overview → Public IP address

**Option B: SSH from Your Computer**

1. Find your VM's IP address:
   - Virtual machines → undertow → Overview → Public IP address
2. Open terminal/command prompt
3. Run: `ssh azureuser@YOUR_VM_IP_ADDRESS`

### Step 2.3: Install The Undertow

Once connected, run these commands:

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

# Email Provider (choose: "smtp" for Gmail/O365, or "postmark")
EMAIL_PROVIDER=smtp

# For SMTP (Gmail or O365):
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true
FROM_EMAIL=your-email@gmail.com

# For Postmark (alternative):
# EMAIL_PROVIDER=postmark
# POSTMARK_API_KEY=your-server-token

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
- `SMTP_USERNAME` = Your email address
- `SMTP_PASSWORD` = The App Password you generated (remove spaces)
- `FROM_EMAIL` = Same as `SMTP_USERNAME`

Save the file: Press `Ctrl+X`, then `Y`, then `Enter`

### Step 2.5: Initialize the Database

```bash
source venv/bin/activate
cd ~/undertow
python -m alembic upgrade head
```

### Step 2.6: Set Up Automatic Running

Copy the systemd service file:

```bash
sudo cp undertow.service /etc/systemd/system/
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

Run a test pipeline:

```bash
cd ~/undertow
source venv/bin/activate
python -m undertow.cli pipeline run --test
```

This will:
1. Select test stories
2. Generate articles
3. Send a test newsletter

Check your email inbox!

---

## Part 4: Monitor & Troubleshoot

### View Logs

```bash
sudo journalctl -u undertow -f
```

### Check Status

```bash
sudo systemctl status undertow
```

### Restart Service

```bash
sudo systemctl restart undertow
```

---

## Cost Comparison: Azure vs AWS

| Provider | VM Size | Specs | Monthly Cost |
|----------|---------|-------|--------------|
| **Azure** | B1s | 1 vCPU, 1 GB RAM | ~$7-10 |
| **AWS** | Lightsail | 1 vCPU, 2 GB RAM | $10 |

**Note**: Azure B1s is cheaper but has less RAM. For better performance, use B1ms (2 vCPU, 4 GB RAM) for ~$15/month.

---

## Security Notes

### Firewall Rules

Azure automatically allows SSH (port 22). The Undertow doesn't need any open ports - it only makes outbound connections.

### Stop/Start VM to Save Costs

If you want to pause the VM (stops billing):

1. Azure Portal → Virtual machines → undertow
2. Click "Stop" (deallocate)
3. To restart: Click "Start"

**Note**: Stopping the VM means the newsletter won't run until you restart it.

---

## Troubleshooting

### Can't Connect via SSH

1. Check VM is running (Status should be "Running")
2. Check Network Security Group allows SSH (port 22)
3. Verify you're using the correct IP address

### Service Won't Start

```bash
# Check logs
sudo journalctl -u undertow -n 50

# Common issues:
# - Missing .env file → Create it
# - Wrong database password → Check DATABASE_URL
# - Missing dependencies → Run: pip install -r requirements.txt
```

### Newsletter Not Sending

1. Check email configuration in `.env`
2. Verify SMTP credentials are correct
3. Check logs: `sudo journalctl -u undertow -n 100`

---

## Next Steps

- Your newsletter will run automatically every day at 4:30 AM SGT
- Check logs regularly: `sudo journalctl -u undertow -f`
- Monitor costs in Azure Portal → Cost Management

---

**Done!** Your Undertow is now running on Azure. 🎉

