# GitHub Actions Authentication Setup

> Complete guide for setting up Claude Code Action authentication in your GitHub workflows

## ACM-AI's Current Setup

**ACM-AI uses GitHub App + OAuth authentication** (the recommended approach):
- ✅ GitHub App: `Claude-Code-2`
- ✅ Secrets configured: `APP_ID`, `APP_PRIVATE_KEY`, `CLAUDE_CODE_OAUTH_TOKEN
- ✅ Max plan credits automatically applied
- ✅ No API key needed from console.anthropic.com

This guide documents our production setup and provides alternatives for different use cases.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Setup (Recommended)](#quick-setup-recommended)
- [Authentication Methods](#authentication-methods)
  - [Option 1: GitHub App + OAuth (Production Method)](#option-1-github-app--oauth-production-method)
  - [Option 2: API Key (Alternative Method)](#option-2-api-key-alternative-method)
- [Secret Configuration](#secret-configuration)
- [Cost Tracking](#cost-tracking)
- [Troubleshooting](#troubleshooting)
- [Additional Resources](#additional-resources)

## Prerequisites

Before you begin, ensure you have:

- **Repository admin access** (required to install apps and add secrets)
- **Claude Pro or Max plan** (for OAuth token generation) OR **Claude API key** (from console.anthropic.com)
- **GitHub Actions enabled** in your repository

## Quick Setup (Recommended)

The fastest way to set up Claude Code GitHub Actions is through the Claude Code CLI:

```bash
# From your terminal with Claude Code installed
claude
/install-github-app
```

This interactive command will:
1. Guide you through GitHub App installation
2. Help you add required repository secrets
3. Create example workflow files in `.github/workflows/`

> **Note:** This method is only available for direct Claude API users. If you're using AWS Bedrock or Google Vertex AI, see the [official documentation](https://code.claude.com/docs/en/github-actions#using-with-aws-bedrock--google-vertex-ai).

## Authentication Methods

**ACM-AI uses Method 1 (GitHub App + OAuth).** Choose the method that fits your needs:

| Method | Best For | Setup Time | Security | Cost Tracking |
|--------|----------|------------|----------|---------------|
| **GitHub App + OAuth** | **Production use (ACM-AI's setup)** | 10 minutes | Highest (scoped tokens, auto-rotation) | Max plan credits |
| **API Key** | Testing, simple projects | 5 minutes | Good (secret-based) | Anthropic console |

---

## Option 1: GitHub App + OAuth (Production Method)

**This is ACM-AI's current setup.** GitHub App + OAuth provides the most secure and flexible approach, with automatic token rotation and Claude Max plan integration.

### Why Use GitHub App + OAuth? (ACM-AI's Choice)

✅ **No API key needed** - OAuth token integrates GitHub App with Claude
✅ **Max plan credits** - Automatically uses your Claude Max subscription
✅ **Scoped permissions** - Tokens are repository-specific
✅ **Automatic rotation** - GitHub handles token lifecycle
✅ **Audit trail** - Track all app actions in GitHub
✅ **Team collaboration** - Share access without sharing credentials
✅ **Enterprise ready** - Production-grade security and reliability

**This is the recommended method for all production deployments.**

### Setup Steps

#### 1. Create GitHub App

Choose either the quick method or manual setup:

<details>
<summary><strong>Quick Method: Using App Manifest (Recommended)</strong></summary>

1. **Download the Quick Setup Tool**
   - Download [`create-app.html`](https://github.com/anthropics/claude-code-action/blob/main/docs/create-app.html) (Right-click → Save Link As)
   - Or use the [GitHub App Manifest JSON](https://github.com/anthropics/claude-code-action/blob/main/github-app-manifest.json)

2. **Create the App**
   - **Personal Account:** Open the HTML file and click "Create App for Personal Account"
   - **Organization:** Enter your org name and click "Create App for Organization"

   **Alternative:** Visit https://github.com/settings/apps/new and paste the manifest JSON

3. **Confirm Creation**
   - Review the auto-configured app name (customizable)
   - Click "Create GitHub App"
   - All permissions will be set automatically

</details>

<details>
<summary><strong>Manual Method: Step-by-Step</strong></summary>

1. **Navigate to GitHub Apps Settings**
   - Personal: https://github.com/settings/apps
   - Organization: `https://github.com/organizations/YOUR-ORG/settings/apps`

2. **Click "New GitHub App"**

3. **Configure Basic Information**
   - **Name:** Choose a unique name (e.g., "ACM-AI Claude Assistant" or "Claude-Code-2")
   - **Homepage URL:** Your repository or organization URL
   - **Webhook:** Uncheck "Active" (not needed)

4. **Set Repository Permissions**

   These are the **minimum required permissions**:

   | Permission | Access | Purpose |
   |------------|--------|---------|
   | **Contents** | Read & Write | Modify repository files, create commits |
   | **Issues** | Read & Write | Respond to issues, create comments |
   | **Pull Requests** | Read & Write | Create PRs, push changes, add reviews |

5. **Account Permissions**
   - Leave as "None required"

6. **Installation Options**
   - Set "Where can this GitHub App be installed?" based on your needs
   - Choose "Only on this account" for security

7. **Click "Create GitHub App"**

</details>

#### 2. Generate Private Key

After creating the app:

1. Scroll to **"Private keys"** section
2. Click **"Generate a private key"**
3. Download the `.pem` file
4. **⚠️ KEEP THIS FILE SECURE** - Never commit it to version control

![Screenshot: Private Key Generation](https://github.com/anthropics/claude-code-action/blob/main/docs/images/github-app-private-key.png)

#### 3. Install App on Repository

1. From your app's settings page, click **"Install App"** (left sidebar)
2. Select your account or organization
3. Choose **"Only select repositories"**
4. Select the specific repository (e.g., `acm-ai`)
5. Click **"Install"**

![Screenshot: App Installation](https://github.com/anthropics/claude-code-action/blob/main/docs/images/github-app-install.png)

#### 4. Add Secrets to Repository

Navigate to: **Repository Settings → Secrets and variables → Actions**

Add the following secrets:

| Secret Name | Value | Where to Find |
|-------------|-------|---------------|
| `APP_ID` | Your GitHub App's ID | App settings page (top) |
| `APP_PRIVATE_KEY` | Contents of the `.pem` file | Downloaded file from step 2 |
| `CLAUDE_CODE_OAUTH_TOKEN` | OAuth token | Run `claude setup-token` locally* |

\* **OAuth Token Setup (Claude Pro/Max users):**

The OAuth token connects your GitHub App to your Claude account, enabling:
- Automatic billing through your Claude Max plan (no separate API costs)
- Unified usage tracking in Claude console
- Higher rate limits and priority access

**To generate:**
```bash
# In your terminal with Claude Code installed
claude setup-token
```

This token is **different from an API key** - it's specifically for GitHub App ↔ Claude integration and is ACM-AI's production authentication method.

#### 5. Update Workflow File

Use the GitHub App token in your workflows:

```yaml
name: Claude Code
on:
  issue_comment:
    types: [created]
  pull_request_review_comment:
    types: [created]
  issues:
    types: [opened, assigned]

jobs:
  claude:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: read
      issues: read
      id-token: write

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 1

      # Generate token from your custom GitHub App
      - name: Generate GitHub App token
        id: app-token
        uses: actions/create-github-app-token@v1
        with:
          app-id: ${{ secrets.APP_ID }}
          private-key: ${{ secrets.APP_PRIVATE_KEY }}

      # Use Claude with GitHub App authentication
      - name: Run Claude Code
        uses: anthropics/claude-code-action@v1
        with:
          github_token: ${{ steps.app-token.outputs.token }}
          anthropic_api_key: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
          model: "claude-4-0-sonnet-20250805"
```

✅ **Setup Complete!** Test by mentioning `@claude` in an issue or PR comment.

---

## Option 2: API Key (Alternative Method)

**Note:** ACM-AI does not use this method. API key authentication is provided as an alternative for testing or simpler projects that don't need GitHub App integration.

### Why Use API Key?

✅ **Simple setup** - Just one secret to configure
✅ **Direct billing** - Costs tracked in Anthropic console
✅ **Quick testing** - Get started in minutes
✅ **No GitHub App needed** - Simpler for personal projects

⚠️ **Limitations compared to GitHub App + OAuth:**
- ❌ No Max plan credit integration
- ❌ API keys don't auto-rotate
- ❌ Harder to track per-repository usage
- ❌ Requires managing API key lifecycle
- ❌ Not recommended for production use

**Use this method only if:**
- Testing Claude Code Actions for the first time
- Working on a personal project without team collaboration
- Don't have Claude Pro/Max plan

### Setup Steps

#### 1. Get Your API Key

1. Visit [console.anthropic.com](https://console.anthropic.com)
2. Navigate to **Settings → API Keys**
3. Click **"Create Key"**
4. Copy the key (starts with `sk-ant-`)
5. **⚠️ SAVE IT SECURELY** - You won't be able to see it again

![Screenshot: API Key Creation](https://github.com/anthropics/claude-code-action/blob/main/docs/images/api-key-creation.png)

#### 2. Install Claude GitHub App

Even with API key authentication, you still need the Claude GitHub App for repository permissions:

1. Visit https://github.com/apps/claude
2. Click **"Install"** or **"Configure"**
3. Select your account/organization
4. Choose repositories to grant access
5. Click **"Install"**

#### 3. Add API Key to Repository Secrets

Navigate to: **Repository Settings → Secrets and variables → Actions**

Click **"New repository secret"** and add:

| Secret Name | Value |
|-------------|-------|
| `ANTHROPIC_API_KEY` | Your API key (starts with `sk-ant-`) |

#### 4. Create Workflow File

Create `.github/workflows/claude.yml`:

```yaml
name: Claude Code
on:
  issue_comment:
    types: [created]
  pull_request_review_comment:
    types: [created]
  issues:
    types: [opened, assigned]

jobs:
  claude:
    if: |
      (github.event_name == 'issue_comment' && contains(github.event.comment.body, '@claude')) ||
      (github.event_name == 'pull_request_review_comment' && contains(github.event.comment.body, '@claude')) ||
      (github.event_name == 'issues' && contains(github.event.issue.body, '@claude'))
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: read
      issues: read
      id-token: write

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 1

      - name: Run Claude Code
        uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          model: "claude-4-0-sonnet-20250805"
```

✅ **Setup Complete!** Test by mentioning `@claude` in an issue or PR comment.

---

## Secret Configuration

### Adding Secrets to GitHub

1. **Navigate to Repository Settings**
   - Go to your repository on GitHub
   - Click **"Settings"** (requires admin access)

2. **Access Secrets Page**
   - Left sidebar → **"Secrets and variables"** → **"Actions"**

3. **Add Each Secret**
   - Click **"New repository secret"**
   - Enter **Name** (exact match required)
   - Paste **Value**
   - Click **"Add secret"**

### Required Secrets by Method

**GitHub App + OAuth Method (ACM-AI's Setup):**
```
✅ APP_ID                   # GitHub App ID
✅ APP_PRIVATE_KEY          # GitHub App private key (.pem file)
✅ CLAUDE_CODE_OAUTH_TOKEN  # Claude OAuth token (from `claude setup-token`)
```

**API Key Method (Alternative):**
```
✅ ANTHROPIC_API_KEY  # API key from console.anthropic.com
```

**Important:** Do NOT mix methods. ACM-AI uses OAuth tokens, not API keys.

### Security Best Practices

🔒 **Critical Security Rules:**

✅ **DO:**
- Use `${{ secrets.ANTHROPIC_API_KEY }}` or `${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}` in workflows
- Regularly rotate API keys and tokens
- Use environment secrets for org-wide access
- Limit app permissions to minimum required
- Review Claude's suggestions before merging

❌ **DON'T:**
- Commit API keys or OAuth tokens to version control (even in private repos)
- Share credentials in PR comments or issues
- Log workflow variables containing secrets
- Hardcode credentials in workflow files

**Example - Correct Usage:**
```yaml
# ✅ CORRECT - Uses GitHub secrets
anthropic_api_key: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
```

**Example - WRONG Usage:**
```yaml
# ❌ WRONG - Exposes your credentials
anthropic_api_key: "token-abc123..."
```

---

## Cost Tracking

Understanding costs helps you optimize your Claude Code usage.

### GitHub Actions Costs

**GitHub-hosted runners consume Actions minutes:**

| Plan | Included Minutes/Month | Overage Cost |
|------|------------------------|--------------|
| Free | 2,000 minutes | $0.008/minute |
| Pro | 3,000 minutes | $0.008/minute |
| Team | 3,000 minutes/user | $0.008/minute |
| Enterprise | 50,000 minutes | $0.008/minute |

**ACM-AI Workflow Estimates:**
- `claude.yml` (interactive): ~2-5 minutes per invocation
- `claude-code-review.yml`: ~3-4 minutes per PR
- `test-generation.yml`: ~5-10 minutes per run
- `sprint-automation.yml`: ~1-2 minutes per PR merge

See [GitHub's billing documentation](https://docs.github.com/en/billing/managing-billing-for-your-products/managing-billing-for-github-actions/about-billing-for-github-actions) for details.

### API Costs (Anthropic)

**For OAuth Token Users (ACM-AI):**

✅ **Included in Claude Max plan** - No separate API billing
✅ **Higher rate limits** - Priority access
✅ **Unified tracking** - Monitor usage in Claude console

**For API Key Users:**

Token usage varies by task complexity:

| Model | Input | Output | Typical PR Review Cost |
|-------|-------|--------|------------------------|
| Claude Sonnet 4 | $3/MTok | $15/MTok | ~$0.10-0.15 |
| Claude Opus 4.6 | $15/MTok | $75/MTok | ~$0.50-0.75 |

**ACM-AI uses Sonnet 4 for 80% cost savings compared to Opus.**

**Monthly estimates for full automation suite (API key users):**
- Code reviews (5-10 PRs/week): ~$4-8/month
- Test generation (weekly): ~$3-4/month
- Sprint automation (10 PRs/week): ~$2-3/month
- Security scanning (daily): ~$3-5/month
- **Total estimated monthly cost:** ~$12-20/month

See [Claude's pricing page](https://www.anthropic.com/pricing) for current rates.

### Cost Optimization Tips

💰 **Save money without sacrificing quality:**

1. **Use Sonnet 4 instead of Opus** (80% savings)
   ```yaml
   model: "claude-4-0-sonnet-20250805"  # ✅ Cost-effective
   # vs
   model: "claude-opus-4-6"              # ❌ Expensive
   ```

2. **Set appropriate max turns**
   ```yaml
   claude_args: "--max-turns 5"  # Prevent runaway iterations
   ```

3. **Use specific triggers**
   ```yaml
   # Only run on non-draft PRs from external contributors
   if: |
     github.event.pull_request.draft == false &&
     github.event.pull_request.author_association != 'MEMBER'
   ```

4. **Configure concurrency limits**
   ```yaml
   concurrency:
     group: claude-${{ github.workflow }}-${{ github.ref }}
     cancel-in-progress: true  # Cancel old runs
   ```

5. **Use workflow dispatch for expensive operations**
   ```yaml
   on:
     workflow_dispatch:  # Manual trigger only
     # Instead of schedule (automatic)
   ```

### Tracking for Claude Max Users (ACM-AI)

If you're using Claude Max plan with OAuth tokens (like ACM-AI):

1. **Usage appears in your Max plan quota**
   - Max plan includes higher API limits
   - OAuth token usage tracked separately from API keys

2. **Generate OAuth token:**
   ```bash
   claude setup-token
   ```

3. **Monitor usage:**
   - Visit https://console.anthropic.com
   - Check **"Usage"** dashboard
   - Filter by OAuth token

4. **Cost benefits:**
   - Max plan often more cost-effective for heavy usage
   - No separate API billing for OAuth token usage
   - Included in monthly Max subscription

---

## Troubleshooting

### Common Issues and Solutions

<details>
<summary><strong>🚨 Claude not responding to @claude mentions</strong></summary>

**Symptoms:** No response when mentioning `@claude` in issues or PRs

**Solutions:**

1. **Verify GitHub App is installed**
   - Go to https://github.com/apps/claude/installations (or your custom app's page)
   - Check if app is installed on your repository
   - Re-install if necessary

2. **Check workflow is enabled**
   - Go to **Actions** tab in your repository
   - Ensure workflows aren't disabled

3. **Verify secrets are configured**
   - Settings → Secrets and variables → Actions
   - For ACM-AI setup, check: `APP_ID`, `APP_PRIVATE_KEY`, `CLAUDE_CODE_OAUTH_TOKEN`
   - Re-add if showing as expired

4. **Confirm trigger phrase**
   - Default is `@claude` (not `/claude`)
   - Check workflow file for `trigger_phrase` parameter
   - Ensure mention is in comment body (not title only)

5. **Review workflow run logs**
   - Actions tab → Latest workflow run
   - Check for authentication or permission errors

</details>

<details>
<summary><strong>🔑 Authentication errors (401/403)</strong></summary>

**Symptoms:** Workflow fails with "Invalid API key" or "Unauthorized"

**Solutions:**

1. **OAuth Token Issues (ACM-AI Setup):**
   - Regenerate token: `claude setup-token`
   - Verify you're on Claude Pro or Max plan
   - Check token hasn't expired (regenerate if old)
   - Ensure secret name is exactly `CLAUDE_CODE_OAUTH_TOKEN`

2. **API Key Issues (Alternative Method):**
   - Verify key starts with `sk-ant-`
   - Regenerate key at console.anthropic.com if expired
   - Ensure key has sufficient permissions
   - Check for typos when adding to secrets

3. **GitHub App Issues:**
   - Verify `APP_ID` matches your app's ID
   - Check `APP_PRIVATE_KEY` contains full `.pem` file contents
   - Ensure no extra whitespace in private key
   - Confirm app is installed on the repository

4. **Permissions:**
   - Workflow file must include:
     ```yaml
     permissions:
       contents: read
       pull-requests: read
       issues: read
       id-token: write
     ```

</details>

<details>
<summary><strong>⚠️ Workflow not triggering on Claude's commits</strong></summary>

**Symptoms:** CI doesn't run when Claude creates commits/PRs

**Solution:**

Use GitHub App authentication instead of default `GITHUB_TOKEN`:

```yaml
# ✅ CORRECT - Triggers CI (ACM-AI's approach)
- name: Generate GitHub App token
  id: app-token
  uses: actions/create-github-app-token@v1
  with:
    app-id: ${{ secrets.APP_ID }}
    private-key: ${{ secrets.APP_PRIVATE_KEY }}

- uses: anthropics/claude-code-action@v1
  with:
    github_token: ${{ steps.app-token.outputs.token }}
```

Why: Default `GITHUB_TOKEN` has restrictions to prevent recursive workflow triggers. GitHub App tokens don't have this limitation.

</details>

<details>
<summary><strong>💸 Unexpected high costs</strong></summary>

**Symptoms:** Higher than expected API or Actions bills

**Solutions:**

1. **For OAuth Users (ACM-AI):**
   - Check Claude console usage dashboard
   - Verify Max plan quota hasn't been exceeded
   - No separate API billing - usage counts against plan limits

2. **For API Key Users:**
   - Review Anthropic console for token usage
   - Identify high-cost workflows
   - Check for failed runs that retry

3. **Implement cost controls:**
   ```yaml
   # Add timeouts
   timeout-minutes: 15

   # Limit max turns
   claude_args: "--max-turns 5"

   # Use concurrency limits
   concurrency:
     group: claude-${{ github.workflow }}-${{ github.ref }}
     cancel-in-progress: true
   ```

4. **Use Sonnet instead of Opus**
   ```yaml
   model: "claude-4-0-sonnet-20250805"  # 80% cheaper
   ```

5. **Add conditional triggers**
   ```yaml
   if: |
     github.event.pull_request.draft == false &&
     !contains(github.event.pull_request.title, '[skip-review]')
   ```

</details>

<details>
<summary><strong>🔧 Workflow YAML syntax errors</strong></summary>

**Symptoms:** Workflow file fails to parse or save

**Solutions:**

1. **Validate YAML syntax**
   - Use online YAML validator
   - Check indentation (spaces, not tabs)
   - Ensure proper quoting for special characters

2. **Common YAML mistakes:**
   ```yaml
   # ❌ WRONG - Missing quotes
   model: claude-4-0-sonnet-20250805

   # ✅ CORRECT - Quoted string
   model: "claude-4-0-sonnet-20250805"
   ```

3. **Use workflow schema validation**
   - VS Code: Install GitHub Actions extension
   - Shows syntax errors in real-time

</details>

<details>
<summary><strong>📦 "Resource not accessible by integration" error</strong></summary>

**Symptoms:** Workflow fails with permissions error

**Solution:**

Add proper permissions to workflow file:

```yaml
jobs:
  claude:
    runs-on: ubuntu-latest
    permissions:
      contents: write      # Required for commits
      pull-requests: write # Required for PR creation
      issues: write        # Required for issue comments
      id-token: write      # Required for OIDC
```

Ensure GitHub App has matching permissions in app settings.

</details>

### Getting Help

If you're still stuck:

1. **Check GitHub Actions logs**
   - Actions tab → Failed workflow run
   - Expand each step to see detailed errors

2. **Review official documentation**
   - [Claude Code GitHub Actions docs](https://code.claude.com/docs/en/github-actions)
   - [Claude Code Action repository](https://github.com/anthropics/claude-code-action)

3. **Community support**
   - [GitHub Discussions](https://github.com/anthropics/claude-code-action/discussions)
   - [Discord Community](https://discord.gg/anthropic)

4. **Contact support**
   - Email: support@anthropic.com
   - Include workflow logs and error messages

---

## Additional Resources

### Official Documentation

- 📖 [Claude Code GitHub Actions](https://code.claude.com/docs/en/github-actions) - Complete feature documentation
- 🔐 [Security Best Practices](https://github.com/anthropics/claude-code-action/blob/main/docs/security.md) - Security and permissions guide
- ⚙️ [Setup Guide](https://github.com/anthropics/claude-code-action/blob/main/docs/setup.md) - Detailed setup instructions
- 🌐 [Claude Code Action Repository](https://github.com/anthropics/claude-code-action) - Source code and examples

### GitHub Documentation

- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions)
- [GitHub Actions Billing](https://docs.github.com/en/billing/managing-billing-for-your-products/managing-billing-for-github-actions/about-billing-for-github-actions)
- [Creating GitHub Apps](https://docs.github.com/en/apps/creating-github-apps/about-creating-github-apps/about-creating-github-apps)

### ACM-AI Specific

- [CLAUDE.md](/CLAUDE.md) - Project-specific Claude configuration
- [Workflow Examples](/.github/workflows/) - ACM-AI's production workflows
- [Contributing Guide](/docs/development/contributing.md) - Development workflow

### External Resources

- [Claude Pricing](https://www.anthropic.com/pricing) - Current API pricing
- [Anthropic Console](https://console.anthropic.com) - API key and usage management
- [GitHub Apps Marketplace](https://github.com/marketplace?type=apps) - Browse other GitHub Apps

---

**Last Updated:** 2026-02-15
**Maintained By:** ACM-AI Team
**ACM-AI Setup:** GitHub App `Claude-Code-2` with OAuth token

_Found an issue or have a suggestion? [Open an issue](https://github.com/your-org/acm-ai/issues) or contribute directly!_
