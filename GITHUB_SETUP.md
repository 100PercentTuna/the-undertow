# GitHub Setup Instructions

## Step 1: Create GitHub Repository

1. Go to [github.com](https://github.com) and log in
2. Click the **"+"** icon in the top right → **"New repository"**
3. Fill in:
   - **Repository name**: `undertow` (or `the-undertow`)
   - **Description**: "AI-powered geopolitical intelligence system"
   - **Visibility**: Choose Public or Private
   - **DO NOT** initialize with README, .gitignore, or license (we already have these)
4. Click **"Create repository"**

## Step 2: Connect Local Repository to GitHub

After creating the repository, GitHub will show you commands. Use these:

```bash
# Add the remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/undertow.git

# Rename branch to main (if needed)
git branch -M main

# If the remote has an initial commit (README, etc.), force push:
git push -u origin main --force

# Otherwise, regular push:
git push -u origin main
```

**Note**: If you see "rejected" errors, it means the remote has content. Use `--force` to overwrite it with your local code.

## Step 3: Verify

1. Go to your repository on GitHub
2. You should see all files uploaded
3. The README.md should display on the main page

## Alternative: Using SSH

If you prefer SSH (requires SSH key setup):

```bash
git remote add origin git@github.com:YOUR_USERNAME/undertow.git
git branch -M main
git push -u origin main
```

## Future Updates

After making changes:

```bash
# Stage changes
git add .

# Commit
git commit -m "Description of changes"

# Push
git push
```

## Repository Settings (Optional)

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Add secrets for CI/CD if needed:
   - `ANTHROPIC_API_KEY`
   - `SENDGRID_API_KEY`

3. Go to **Settings** → **Pages** (if you want GitHub Pages)
4. Go to **Settings** → **Topics** and add:
   - `ai`
   - `geopolitics`
   - `newsletter`
   - `python`
   - `aws`

## Making Repository Public

If you want to make it public later:

1. Go to **Settings** → **General** → Scroll to **"Danger Zone"**
2. Click **"Change visibility"**
3. Select **"Make public"**

---

**That's it! Your repository is now on GitHub.**

