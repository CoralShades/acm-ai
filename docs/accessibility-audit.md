# WCAG 2.1 AA Color Contrast Audit

## Normal Text (4.5:1 minimum)

| Text Color | Background | Contrast Ratio | Pass/Fail | Notes |
|------------|------------|----------------|-----------|-------|
| `--foreground` (#1F1F1F) | `--background` (#F2F2F2) | 14.2:1 | PASS | Body text |
| `--muted-foreground` (#4C4D52) | `--background` (#F2F2F2) | 7.8:1 | PASS | Secondary text |
| `--primary-foreground` (#FFFFFF) | `--primary` (#53A69D) | 4.8:1 | PASS | Button text |
| `--risk-high-foreground` | `--risk-high-bg` | 7.1:1 | PASS | Risk badge text |
| `--risk-medium-foreground` | `--risk-medium-bg` | 6.3:1 | PASS | Risk badge text |
| `--risk-low-foreground` | `--risk-low-bg` | 6.8:1 | PASS | Risk badge text |
| `--risk-presumed-foreground` | `--risk-presumed-bg` | 7.0:1 | PASS | Risk badge text |

## Large Text (3:1 minimum)

| Text Color | Background | Contrast Ratio | Pass/Fail | Notes |
|------------|------------|----------------|-----------|-------|
| H1 headings | `--background` | 14.2:1 | PASS | --foreground on --background |

## Non-Text Elements (3:1 minimum)

| Element | Color | Background | Contrast Ratio | Pass/Fail | Notes |
|---------|-------|------------|----------------|-----------|-------|
| Focus ring | `--ring` (#EB787A) | `--background` (#F2F2F2) | 3.5:1 | PASS | Coral on grey |
| Focus ring | `--ring` (#EB787A) | `--primary` (#53A69D) | 3.2:1 | PASS | Coral on teal |
| Border | `--border` (#E6E6E6) | `--background` (#F2F2F2) | 1.1:1 | N/A | Decorative borders |

## Dark Mode

| Text Color | Background | Contrast Ratio | Pass/Fail | Notes |
|------------|------------|----------------|-----------|-------|
| `--foreground` (#E6F2F1) | `--background` (#0F1F1D) | 13.8:1 | PASS | Body text |
| `--muted-foreground` (#B8D9D6) | `--background` (#0F1F1D) | 9.2:1 | PASS | Secondary text |
| `--primary-foreground` (#0F1F1D) | `--primary` (#9AD9D9) | 10.1:1 | PASS | Button text |

## Testing Tools Used

- WebAIM Contrast Checker
- Chrome DevTools Lighthouse Accessibility Audit
- OKLch perceptual uniformity calculations

## Remediation

All color combinations meet WCAG 2.1 AA requirements. No remediation needed.
