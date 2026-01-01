# Email Provider Setup Guide

The Undertow supports multiple email providers. **⚠️ App passwords for Gmail and O365 are no longer available** - use Postmark or SendGrid instead.

---

## ⚠️ Important: Gmail & O365 App Passwords Deprecated

**As of 2025, both Gmail and Microsoft O365 have deprecated app passwords** in favor of OAuth 2.0. For automated systems like The Undertow, **Postmark or SendGrid are recommended** instead.

---

## Option 1: Postmark (RECOMMENDED - Best for Production)

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

## Option 2: SendGrid (FREE TIER - Good Alternative)

**Best for**: Free tier users, testing  
**Cost**: 
- Free: 100 emails/day forever
- Paid: $19.95/month for 50,000 emails  
**Limit**: 100/day on free tier  
**Setup time**: 10 minutes

### Setup Steps

1. **Sign Up**
   - Go to [sendgrid.com](https://sendgrid.com)
   - Click "Start for Free"
   - Create account

2. **Verify Sender**
   - Settings → Sender Authentication
   - Click "Verify a Single Sender"
   - Enter your email and verify

3. **Create API Key**
   - Settings → API Keys
   - Click "Create API Key"
   - Name it "undertow"
   - Select "Full Access" or "Mail Send" permissions
   - **Copy the API key** (starts with `SG.`)

4. **Configure `.env`**
   ```bash
   EMAIL_PROVIDER=sendgrid
   SENDGRID_API_KEY=SG.your-key-here
   FROM_EMAIL=your-verified-email@domain.com
   NEWSLETTER_RECIPIENTS=you@email.com,friend@email.com
   ```

---

## Option 3: Gmail/O365 with OAuth 2.0 (ADVANCED - Not Recommended)

**Note**: This requires OAuth 2.0 setup which is complex. **Not recommended** unless you're comfortable with OAuth flows.

If you need Gmail/O365, you'll need to:
1. Register an OAuth 2.0 application
2. Implement OAuth flow to get access tokens
3. Use tokens for SMTP authentication

**Recommendation**: Use Postmark or SendGrid instead - they're simpler and more reliable for automated systems.

---

## Comparison

| Provider | Cost | Daily Limit | Setup Difficulty | Best For |
|----------|------|-------------|------------------|----------|
| **Postmark** | $15/mo | 10,000/mo | Medium | Production, scale |
| **SendGrid** | Free | 100/day | Easy | Free tier, testing |
| **Gmail/O365** | Free* | N/A | Complex | Not recommended |

*Requires OAuth 2.0 setup (complex)

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

### Postmark: "Invalid API token"
- Verify you copied the **Server API Token**, not the Account API token
- Check that your sender email is verified in Postmark

### SendGrid: "Authentication failed"
- Verify you copied the full API key (starts with `SG.`)
- Check that your sender email is verified in SendGrid
- Ensure API key has "Mail Send" permissions

### "Connection refused" (SMTP only)
- Check firewall settings
- Verify SMTP host and port are correct
- For O365, ensure your organization allows SMTP

---

## Switching Providers

To switch providers, just change `EMAIL_PROVIDER` in `.env` and update the relevant credentials. No code changes needed!

---

## Why Not Gmail/O365 App Passwords?

Both Google and Microsoft have deprecated app passwords in favor of OAuth 2.0 for security reasons:

- **Gmail**: As of March 2025, OAuth 2.0 is required for third-party apps
- **O365**: App passwords are being phased out, especially for accounts with MFA

For automated systems like The Undertow, using a transactional email service (Postmark/SendGrid) is:
- ✅ Simpler to set up
- ✅ More reliable
- ✅ Better deliverability
- ✅ Designed for automated sending
