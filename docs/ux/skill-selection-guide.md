# Skill Selection Guide — When to Use What

> Quick-reference decision tree for ACM-AI frontend/UI work.
> **Updated:** 2026-03-11 — All skills verified installed.

---

## Decision Tree

```
What are you doing?
│
├─ DESIGNING a new component/page?
│  ├─ Want to avoid AI-looking UI?     → /uncodixfy (always load first)
│  ├─ Need specific aesthetic?          → /frontend-design
│  ├─ Need design engineering?          → /taste-skill
│  ├─ Building with Tailwind/Radix?     → /baseline-ui
│  ├─ Need design intelligence data?    → /ui-ux-pro-max (50 styles, 97 palettes)
│  ├─ Building a design system?         → /design-system-creation
│  ├─ Need compliance check?            → /web-design-guidelines
│  └─ Single-file React prototype?      → /web-artifacts-builder
│
├─ BUILDING React/Next.js code?
│  ├─ React performance patterns?       → /react-best-practices (57 rules)
│  ├─ Next.js App Router patterns?      → /next-best-practices (18 sections)
│  ├─ Accessibility compliance?         → /fixing-accessibility (WCAG 2.1)
│  ├─ SEO/social metadata?             → /fixing-metadata
│  └─ Animation performance?            → /fixing-motion-performance
│
├─ BUILDING AI-powered UIs?
│  ├─ AI copilot / chatbot in React?    → /copilotkit
│  ├─ Agent-to-Agent communication?     → /a2a-protocol (v0.3.0)
│  └─ SSE streaming / real-time push?   → /sse-streaming
│
├─ TESTING the UI?
│  ├─ Quick smoke test?                 → /webapp-testing
│  ├─ Custom browser script?            → /playwright-skill
│  ├─ Full E2E with self-healing?       → /e2e-test
│  ├─ Exploratory QA / bug hunting?     → /dogfood
│  ├─ Desktop Electron app?             → /electron
│  └─ Design guideline audit?           → /web-design-guidelines
│
├─ PLANNING multi-agent work?
│  ├─ Architecture patterns?            → /multi-agent-patterns
│  ├─ Task-based subagent dispatch?     → /subagent-driven-development
│  └─ Persistent task tracking?         → /planning-with-files
│
└─ NEED more? (not yet installed)
   ├─ Additional A2A patterns?          → npx skills add vanman2024/ai-dev-marketplace@a2a-patterns
   ├─ Real-time sync?                   → npx skills add ancoleman/ai-design-components@implementing-realtime-sync
   ├─ LLM streaming patterns?           → npx skills add yonatangross/orchestkit@llm-streaming
   └─ Material Design reference?        → npx skills add copyleftdev/sk1llz@google-material-design
```

---

## Recommended Skill Combos

### Full Design Pipeline
```
/uncodixfy → /taste-skill → /frontend-design → /baseline-ui → /ui-ux-pro-max
```

### Design System Pipeline
```
/design-system-creation → /ui-ux-pro-max → /uncodixfy → /baseline-ui
```

### Full Quality Pipeline
```
/fixing-accessibility → /fixing-metadata → /fixing-motion-performance → /web-design-guidelines
```

### Full Test Pipeline
```
/webapp-testing → /playwright-skill → /e2e-test → /dogfood
```

### AI-Powered UI Pipeline
```
/copilotkit → /sse-streaming → /a2a-protocol → /react-best-practices
```

### Sprint Story Pipeline
```
/planning-with-files → /subagent-driven-development → /e2e-test → /dogfood
```

### Single-File Prototype Pipeline
```
/web-artifacts-builder → /uncodixfy → /frontend-design
```

---

## Token Budget Reference

| Skill | Approx Tokens | Load Impact | Category |
|-------|---------------|-------------|----------|
| uncodixfy | ~2,500 | Medium | Design Foundation |
| baseline-ui | ~1,200 | Light | Design Constraints |
| taste-skill | ~3,000 | Heavy | Design Engineering |
| frontend-design | ~800 | Light | Aesthetic Direction |
| ui-ux-pro-max | ~1,500 | Medium | Design Intelligence (plugin) |
| web-artifacts-builder | ~1,200 | Light | Prototyping |
| design-system-creation | ~800 | Light | Design Systems |
| react-best-practices | ~2,000 | Medium | Framework |
| next-best-practices | ~2,500 | Medium | Framework |
| fixing-accessibility | ~1,000 | Light | Quality Gate |
| fixing-metadata | ~800 | Light | Quality Gate |
| fixing-motion-performance | ~1,200 | Light | Quality Gate |
| copilotkit | ~2,500 | Medium | AI/Agent UI |
| a2a-protocol | ~2,000 | Medium | Agent Protocol |
| sse-streaming | ~1,000 | Light | Streaming |
| webapp-testing | ~600 | Light | Testing |
| playwright-skill | ~1,500 | Medium | Testing |
| e2e-test | ~2,000 | Medium | Testing |
| dogfood | ~1,200 | Light | Testing |
| web-design-guidelines | ~400 | Minimal | Compliance |
| electron | ~1,000 | Light | Desktop Testing |

---

## Installation Status Summary

| # | Skill | Status | Location |
|---|-------|--------|----------|
| 1 | uncodixfy | INSTALLED | `.agents/skills/` (symlinked) |
| 2 | baseline-ui | INSTALLED | `.claude/skills/` |
| 3 | taste-skill | INSTALLED | `.claude/skills/` |
| 4 | frontend-design | INSTALLED | `.claude/skills/` |
| 5 | ui-ux-pro-max | INSTALLED | Plugin (v2.0.1) |
| 6 | web-artifacts-builder | INSTALLED | `~/.agents/skills/` (user-level) |
| 7 | design-system-creation | INSTALLED | `~/.agents/skills/` (user-level) |
| 8 | react-best-practices | INSTALLED | `.claude/skills/` |
| 9 | next-best-practices | INSTALLED | `.claude/skills/` |
| 10 | fixing-accessibility | INSTALLED | `.claude/skills/` |
| 11 | fixing-metadata | INSTALLED | `.claude/skills/` |
| 12 | fixing-motion-performance | INSTALLED | `.claude/skills/` |
| 13 | copilotkit | INSTALLED | `~/.agents/skills/` (user-level) |
| 14 | a2a-protocol | INSTALLED | `~/.agents/skills/` (user-level) |
| 15 | sse-streaming | INSTALLED | `~/.agents/skills/` (user-level) |
| 16 | webapp-testing | INSTALLED | `.claude/skills/` |
| 17 | playwright-skill | INSTALLED | `.claude/skills/` |
| 18 | e2e-test | INSTALLED | `.claude/skills/` |
| 19 | dogfood | INSTALLED | `.claude/skills/` |
| 20 | web-design-guidelines | INSTALLED | `.claude/skills/` |
| 21 | electron | INSTALLED | `.claude/skills/` |
