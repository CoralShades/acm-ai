# GitHub Actions Verification Checklist

Complete verification procedures for ACM-AI GitHub Actions workflows.

## Pre-Deployment Checks

### 1. YAML Syntax Validation
```bash
# Install yamllint
pip install yamllint

# Validate all workflows
yamllint .github/workflows/*.yml

# Expected: No errors
```

### 2. File Existence
```bash
# Verify all 6 workflow files exist
ls -la .github/workflows/{claude,claude-code-review,ci,test-generation,sprint-automation,security}.yml
```

### 3. Permissions Audit
Review each workflow's permissions section:
- `contents: write` only where needed (sprint-automation, test-generation)
- `pull-requests: write` for PR comments
- `issues: write` for issue creation
- `security-events: write` for CodeQL

## Secret Configuration

### Required Secrets (All Workflows)
| Secret | Purpose | How to Verify |
|--------|---------|---------------|
| `APP_ID` | GitHub App ID | `gh secret list \| grep APP_ID` |
| `APP_PRIVATE_KEY` | GitHub App private key | `gh secret list \| grep APP_PRIVATE_KEY` |
| `CLAUDE_CODE_OAUTH_TOKEN` | Claude OAuth token | `gh secret list \| grep CLAUDE_CODE_OAUTH_TOKEN` |

### Validation Steps
```bash
# List all secrets
gh secret list

# Expected output:
# APP_ID
# APP_PRIVATE_KEY
# CLAUDE_CODE_OAUTH_TOKEN
```

## Workflow-Specific Testing

### 1. claude.yml (Interactive Assistant)
```bash
# Create test issue
gh issue create --title "Test @claude" --body "@claude List BMAD workflows"

# Check workflow run
gh run list --workflow=claude.yml --limit 1

# Expected: Status = completed, Conclusion = success
```

### 2. claude-code-review.yml (Automated Review)
```bash
# Create test PR
git checkout -b test-review
echo "# Test" > test-review.md
git add test-review.md
git commit -m "test: automated review"
git push origin test-review
gh pr create --title "Test review" --body "Testing"

# Check workflow
gh run list --workflow=claude-code-review.yml --limit 1
```

### 3. ci.yml (CI Pipeline)
```bash
# Trigger on push to main
git checkout main
git push

# Check all 3 jobs complete
gh run view --log | grep -E "(backend|frontend|type-sync)"
```

### 4. sprint-automation.yml (Sprint Tracking)
```bash
# Create PR with story ID
git checkout -b test-sprint
echo "test" > test.md
git add test.md
git commit -m "test: sprint automation"
git push origin test-sprint
gh pr create --title "[E99-S99] Test" --body "Test"
gh pr merge --squash

# Verify sprint-status.yaml updated
git pull
grep "e99-s99" docs/sprint-artifacts/sprint-status.yaml
```

### 5. test-generation.yml (AI Test Generation)
```bash
# Manual trigger
gh workflow run test-generation.yml \
  --field target_path="open_notebook/extractors/" \
  --field coverage_threshold="80"

# Wait for completion
gh run watch

# Check for generated PR
gh pr list --author "github-actions[bot]" | grep "Add test coverage"
```

### 6. security.yml (Security Scanning)
```bash
# Manual trigger
gh workflow run security.yml

# Check all jobs complete
gh run watch
gh run view --log | grep -E "(python-security|npm-security|secret-scan|codeql|security-report)"
```

## Success Criteria

- [ ] All workflows have valid YAML syntax
- [ ] All required secrets configured
- [ ] GitHub App installed on repository
- [ ] All test workflows complete successfully
- [ ] No authentication errors in logs
- [ ] Sprint automation updates sprint-status.yaml
- [ ] Code review posts comments on PRs
- [ ] CI pipeline runs on every PR
- [ ] Security scans produce reports
- [ ] Test generation creates valid PRs

## Troubleshooting

See [GitHub Actions Setup Guide](./github-actions-setup.md#troubleshooting) for detailed troubleshooting steps.

## Rollback Procedures

### Emergency Full Rollback
```bash
# Disable all workflows
for workflow in claude claude-code-review ci test-generation sprint-automation security; do
  gh workflow disable $workflow.yml
done

# Delete workflow files
git rm .github/workflows/{ci,test-generation,sprint-automation,security}.yml
git commit -m "rollback: remove GitHub Actions workflows"
git push
```

### Selective Disable
```bash
# Disable single workflow
gh workflow disable test-generation.yml

# Or edit workflow file to add condition:
# if: false  # Temporarily disabled
```

## Post-Deployment Monitoring

### Week 1
- [ ] Monitor API costs daily
- [ ] Review all workflow runs for errors
- [ ] Check PR review quality
- [ ] Verify sprint automation accuracy

### Weeks 2-4
- [ ] Review cost trends weekly
- [ ] Optimize prompts if needed
- [ ] Adjust allowed_tools if security concerns
- [ ] Fine-tune test generation quality

### Monthly
- [ ] Review total API costs vs budget
- [ ] Audit workflow permissions
- [ ] Update documentation
- [ ] Rotate GitHub App keys

---

**Last Updated:** 2026-02-15
**Status:** Production-ready pending user testing
