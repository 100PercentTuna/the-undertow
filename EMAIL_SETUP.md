# Email Provider Setup Guide

The Undertow supports three email providers. Choose the one that works best for you.

---

## Option 1: Gmail SMTP (FREE - Recommended)

**Best for**: Personal use, testing  
**Cost**: Free  
**Limit**: 500 emails/day  
**Setup time**: 5 minutes

### Setup Steps

1. **Enable 2-Factor Authentication**
   - Go to [myaccount.google.com](https://myaccount.google.com)
   - Security → 2-Step Verification → Enable

2. **Generate App Password**
   - Security → App passwords
   - Select "Mail" and "Other (Custom name)"
   - Type "The Undertow"
   - **Copy the 16-character password** (remove spaces)

3. **Configure `.env`**
   ```bash
   EMAIL_PROVIDER=smtp
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your-email@gmail.com
   SMTP_PASSWORD=your16charapppassword
   SMTP_USE_TLS=true
   FROM_EMAIL=your-email@gmail.com
   ```

---

## Option 2: Microsoft O365 SMTP (FREE)

**Best for**: Business/enterprise accounts  
**Cost**: Free (if you have O365 account)  
**Limit**: Unlimited (within your plan)  
**Setup time**: 5 minutes

### Setup Steps

1. **Enable 2-Factor Authentication**
   - Go to [account.microsoft.com](https://account.microsoft.com)
   - Security → Advanced security options
   - Enable 2-step verification

2. **Generate App Password**
   - Security → Advanced security → App passwords
   - Create new app password
   - Name it "The Undertow"
   - **Copy the password** (16 characters)

3. **Configure `.env`**
   ```bash
   EMAIL_PROVIDER=smtp
   SMTP_HOST=smtp.office365.com
   SMTP_PORT=587
   SMTP_USERNAME=your-email@yourdomain.com
   SMTP_PASSWORD=your-app-password
   SMTP_USE_TLS=true
   FROM_EMAIL=your-email@yourdomain.com
   ```

**Note**: Your `SMTP_USERNAME` should be your full O365 email address (e.g., `name@company.com`).

---

## Option 3: Postmark (PAID - Best for Production)

**Best for**: Production, high deliverability  
**Cost**: 
- Free: 100 emails/month
- Paid: $15/month for 10,000 emails
- $1.25 per additional 1,000 emails  
**Limit**: Based on plan  
**Setup time**: 10 minutes

### Setup Steps

1. **Sign Up**
   - Go to [postmarkapp.com](https://postmarkapp.com)
   - Click "Start Free Trial"
   - Create account

2. **Create Server**
   - Once logged in, click "Add Server"
   - Name it "The Undertow"
   - Select "Transactional" message stream
   - Click "Create Server"

3. **Get API Token**
   - Click on your server
   - Copy the **Server API Token** (starts with your server name)

4. **Verify Sender**
   - Go to "Signatures" tab
   - Click "Add Domain" or "Add Email"
   - Follow verification steps
   - Use verified email as `FROM_EMAIL`

5. **Configure `.env`**
   ```bash
   EMAIL_PROVIDER=postmark
   POSTMARK_API_KEY=your-server-token-here
   FROM_EMAIL=your-verified-email@domain.com
   NEWSLETTER_RECIPIENTS=you@email.com,friend@email.com
   ```

---

## Comparison

| Provider | Cost | Daily Limit | Setup Difficulty | Best For |
|----------|------|-------------|------------------|----------|
| **Gmail** | Free | 500/day | Easy | Personal, testing |
| **O365** | Free* | Unlimited* | Easy | Business accounts |
| **Postmark** | $15/mo | 10,000/mo | Medium | Production, scale |

*Free if you already have an O365 account

---

## Testing Your Configuration

After setting up, test with:

```bash
cd ~/undertow
source venv/bin/activate
python -m undertow.cli pipeline run --test
```

This will send a test newsletter to your recipients.

---

## Troubleshooting

### Gmail/O365: "Authentication failed"
- Make sure you're using an **App Password**, not your regular password
- Verify 2FA is enabled
- Check that `SMTP_USERNAME` matches `FROM_EMAIL`

### Postmark: "Invalid API token"
- Verify you copied the **Server API Token**, not the Account API token
- Check that your sender email is verified in Postmark

### "Connection refused"
- Check firewall settings
- Verify SMTP host and port are correct
- For O365, ensure your organization allows SMTP

---

## Switching Providers

To switch providers, just change `EMAIL_PROVIDER` in `.env` and update the relevant credentials. No code changes needed!

