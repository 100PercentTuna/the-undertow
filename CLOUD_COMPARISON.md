# Cloud Provider Comparison: AWS vs Azure

Quick comparison to help you choose the right cloud provider for The Undertow.

---

## Quick Comparison

| Feature | AWS Lightsail | Azure VM |
|---------|---------------|----------|
| **Easiest Setup** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Cost (Basic)** | $10/month | $7/month |
| **RAM (Basic)** | 2 GB | 1 GB |
| **RAM (Recommended)** | 2 GB | 4 GB |
| **Cost (Recommended)** | $10/month | $15/month |
| **Free Tier** | 1 month free | $200 credit (30 days) |
| **Region (Singapore)** | ✅ ap-southeast-1 | ✅ Southeast Asia |
| **SSH Access** | Browser-based | SSH client or Cloud Shell |
| **Documentation** | Extensive | Extensive |

---

## Detailed Comparison

### AWS Lightsail

**Pros:**
- ✅ Simplest interface - perfect for beginners
- ✅ Browser-based SSH (no need for SSH client)
- ✅ Predictable pricing ($10/month flat)
- ✅ 2 GB RAM included at $10/month
- ✅ Excellent documentation

**Cons:**
- ❌ Slightly more expensive than Azure basic tier
- ❌ Less flexible than full EC2

**Best For:**
- Beginners
- Users who want simplicity
- Users who prefer AWS ecosystem

**Setup Time:** ~15 minutes

---

### Azure Virtual Machine

**Pros:**
- ✅ Cheaper basic tier ($7/month)
- ✅ More RAM options (1 GB to 4 GB)
- ✅ $200 free credit for new accounts
- ✅ Good if you already use Microsoft services
- ✅ Can stop/start to save costs

**Cons:**
- ❌ Slightly more complex setup
- ❌ Need SSH client or use Cloud Shell
- ❌ Basic tier has less RAM (1 GB)

**Best For:**
- Users with Microsoft accounts
- Users who want more control
- Users who want to save a few dollars

**Setup Time:** ~20 minutes

---

## Cost Breakdown

### AWS Lightsail

| Plan | Specs | Monthly Cost |
|------|-------|--------------|
| Basic | 1 vCPU, 2 GB RAM | $10 |

### Azure VM

| Size | Specs | Monthly Cost |
|------|-------|--------------|
| B1s | 1 vCPU, 1 GB RAM | ~$7 |
| B1ms | 1 vCPU, 4 GB RAM | ~$15 |
| B2s | 2 vCPU, 4 GB RAM | ~$30 |

**Recommendation**: 
- **AWS**: Use the $10 plan (2 GB RAM is sufficient)
- **Azure**: Use B1ms ($15/month) for 4 GB RAM, or B1s ($7/month) if budget is tight

---

## Performance

Both providers offer similar performance for The Undertow's needs:

- **CPU**: Both use shared vCPUs (sufficient for daily newsletter)
- **RAM**: 2-4 GB is ideal (AWS includes 2 GB, Azure B1ms has 4 GB)
- **Storage**: Both use SSD (30 GB is plenty)
- **Network**: Both have good network connectivity

**Verdict**: Performance is essentially the same. Choose based on cost/preference.

---

## Setup Difficulty

### AWS Lightsail: ⭐⭐⭐⭐⭐ (Easiest)

1. Click "Create instance"
2. Select Ubuntu 22.04
3. Click "Create"
4. Click "Connect" (browser SSH opens)
5. Paste commands

**Total clicks**: ~10

### Azure VM: ⭐⭐⭐⭐ (Slightly More Steps)

1. Click "Create a resource"
2. Search "Virtual Machine"
3. Fill in 4 tabs (Basics, Disks, Networking, Management)
4. Review + Create
5. SSH to VM (need SSH client or Cloud Shell)

**Total clicks**: ~15-20

**Verdict**: AWS is slightly easier, but both are straightforward.

---

## Which Should You Choose?

### Choose **AWS** if:
- ✅ You're new to cloud computing
- ✅ You want the simplest setup
- ✅ You prefer browser-based SSH
- ✅ $10/month is fine

### Choose **Azure** if:
- ✅ You have a Microsoft account
- ✅ You want to save $3/month (B1s)
- ✅ You want more RAM options
- ✅ You're comfortable with SSH clients

---

## Migration Between Providers

The Undertow runs the same on both platforms. To migrate:

1. Export your `.env` file
2. Create new VM on other provider
3. Install The Undertow (same commands)
4. Copy `.env` file
5. Start service

**No code changes needed!**

---

## Free Tier Options

### AWS
- 1 month free trial of Lightsail
- 750 hours/month of t2.micro (not suitable for Undertow)

### Azure
- $200 credit for 30 days (new accounts)
- Can run B1s for ~20 days free

**Verdict**: Azure's free credit is more generous.

---

## Final Recommendation

**For most users**: **AWS Lightsail** ($10/month)
- Simplest setup
- Good documentation
- 2 GB RAM included
- Browser-based SSH

**For budget-conscious users**: **Azure B1s** ($7/month)
- Cheapest option
- Still works well
- Less RAM but sufficient

**For power users**: **Azure B1ms** ($15/month)
- 4 GB RAM for better performance
- More headroom for future features

---

## Need Help?

- **AWS Setup**: See [`DEPLOYMENT_GUIDE.md`](DEPLOYMENT_GUIDE.md)
- **Azure Setup**: See [`AZURE_DEPLOYMENT.md`](AZURE_DEPLOYMENT.md)
- **Quick Start**: See [`QUICK_START.md`](QUICK_START.md)

