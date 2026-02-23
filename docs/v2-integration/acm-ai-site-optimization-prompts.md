# ACM-AI Marketing Site — Optimization Prompt Collection
# Use in Claude Code, in order per section, or in parallel terminals where marked PARALLEL

---

## PRE-FLIGHT: READ ALL SKILLS FIRST
## PASTE THIS IN EVERY NEW TERMINAL BEFORE ANY OTHER PROMPT

```
Before doing anything else, read these skill files completely:
1. cat /mnt/skills/public/frontend-design/SKILL.md
2. cat /mnt/skills/examples/theme-factory/SKILL.md
3. cat /mnt/skills/examples/canvas-design/SKILL.md
4. cat /mnt/skills/examples/web-artifacts-builder/SKILL.md

Internalize the design philosophy from frontend-design/SKILL.md:
- Commit to a BOLD aesthetic direction before writing any code
- Avoid: Inter font, purple gradients, generic AI aesthetics, centered-everything layouts
- Use: DM Serif Display + DM Sans, OKLCH colours, VAEA teal/coral/navy
- Motion: one well-orchestrated reveal is better than scattered micro-interactions
- Never converge on common choices

The site lives at: /home/claude/acm-ai-site/
All output goes to: /mnt/user-data/outputs/acm-ai-site/

Report which skills you read and your chosen aesthetic approach before writing any code.
```

---

## PROMPT OPT-01: HERO SECTION — CINEMATIC ENTRANCE
## Terminal A | Priority: P0

```
Read /mnt/skills/public/frontend-design/SKILL.md first.

You are optimising the hero section at src/app/page.tsx and src/components/landing/Hero.tsx
in the ACM-AI marketing site at /home/claude/acm-ai-site/

Read the current Hero.tsx file first, then implement ALL of the following:

DESIGN DIRECTION: "Blueprint Authority" — a dark navy canvas with animated technical grid 
lines, like an engineering blueprint that comes alive. Government precision meets AI energy.

1. ANIMATED GRID BACKGROUND:
Replace any static background with this CSS pattern:
```css
background-color: #2a2f45;
background-image: 
  linear-gradient(rgba(58, 143, 138, 0.08) 1px, transparent 1px),
  linear-gradient(90deg, rgba(58, 143, 138, 0.08) 1px, transparent 1px);
background-size: 40px 40px;
animation: gridDrift 20s linear infinite;

@keyframes gridDrift {
  0% { background-position: 0 0; }
  100% { background-position: 40px 40px; }
}
```
Add this as inline styles or a CSS module (not Tailwind for this one).

2. HEADLINE ANIMATION:
Wrap the headline in Framer Motion with word-by-word stagger:
- Each word: initial { opacity: 0, y: 20 }, animate { opacity: 1, y: 0 }
- Stagger: 0.06s between words
- Duration: 0.5s per word
- Headline text: "Asbestos Compliance,\nReinvented with AI"
- Use DM Serif Display, 72px desktop / 40px mobile
- Colour: white for "Asbestos Compliance," — teal (#3a8f8a) for "Reinvented with AI"

3. SUBHEADLINE TYPEWRITER:
After headline completes (delay 1.2s), typewriter-reveal the subheadline:
"ACM-AI converts Victorian Government SAMP/BAR PDF registers into 
submission-ready spreadsheets using a 7-stage AI extraction pipeline."
Use the useTypewriter hook from src/hooks/useTypewriter.ts
Speed: 30ms per character, cursor blinks with CSS animation

4. CTA BUTTONS — MAGNETIC HOVER:
Add a magnetic hover effect to both CTA buttons using onMouseMove:
```tsx
const handleMouseMove = (e: React.MouseEvent<HTMLButtonElement>) => {
  const rect = e.currentTarget.getBoundingClientRect()
  const x = e.clientX - rect.left - rect.width / 2
  const y = e.clientY - rect.top - rect.height / 2
  e.currentTarget.style.transform = `translate(${x * 0.15}px, ${y * 0.15}px)`
}
const handleMouseLeave = (e: React.MouseEvent<HTMLButtonElement>) => {
  e.currentTarget.style.transform = 'translate(0, 0)'
}
```
Add transition: transform 0.2s ease to the button style.

5. ANIMATED STAT COUNTER ROW:
Below the buttons, 4 counters animate from 0 using IntersectionObserver:
- 87 → label: "Extraction Accuracy" → suffix: "%"
- 47 → label: "BAR Columns" → suffix: ""
- 122 → label: "Stories Shipped" → suffix: ""  
- 18 → label: "Seconds Per PDF" → suffix: "s"

Each counter: large number in teal (DM Serif, 56px), label in gray-400 (DM Sans, 13px)
Animate: count from 0 to target over 2 seconds using requestAnimationFrame easing
Delay each counter by 150ms after the previous one completes.

6. SCROLL INDICATOR:
At the bottom of the hero, a subtle animated scroll arrow:
- A chevron-down icon that bounces gently (CSS keyframe, translate Y 0→8px→0, 1.5s loop)
- Opacity 0.4 in default, 0.8 on hover
- Clicking it smooth-scrolls to the "How It Works" section

After implementing, run:
cd /home/claude/acm-ai-site && npm run lint && npm run build

Copy final files: cp -r /home/claude/acm-ai-site/src /mnt/user-data/outputs/acm-ai-site/src
Report: what changed, build status, any issues.
```

---

## PROMPT OPT-02: LIVE GITHUB STATUS — REAL COMMIT COUNT
## Terminal A (after OPT-01) | Priority: P0

```
Read /mnt/skills/public/frontend-design/SKILL.md first.

You are implementing the Live GitHub Status widget in the ACM-AI marketing site.
Site location: /home/claude/acm-ai-site/

Read the current LiveStatusStrip.tsx and src/app/api/github/stats/route.ts first.

TASK: Replace the current stub with a working GitHub API integration that shows 
REAL commit count from the actual GitHub repository.

1. UPDATE src/app/api/github/stats/route.ts:

The endpoint must:
a) Use the GITHUB_TOKEN environment variable (from .env.local)
b) Fetch ACTUAL commit count using GitHub's statistics endpoint:
   GET https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contributors
   Sum commit counts across all contributors for total.
   
   FALLBACK method (if contributors is slow): use:
   GET https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/commits?per_page=1
   Read the Link header to get total page count = total commits

c) Also fetch:
   - Last commit: GET /repos/{owner}/{repo}/commits?per_page=1
     → commit.commit.message (first 60 chars), commit.commit.author.date
   - Last commit author: commit.commit.author.name
   - Open PRs: GET /repos/{owner}/{repo}/pulls?state=open&per_page=1 
     → read X-Total-Count header or count results
   - Last workflow run: GET /repos/{owner}/{repo}/actions/runs?per_page=1
     → conclusion (success/failure/null), created_at
   - Branch: GET /repos/{owner}/{repo}/branches/main → commit.sha (first 7 chars)
   - Stars: GET /repos/{owner}/{repo} → stargazers_count

d) Return JSON:
```json
{
  "commits": 281,
  "lastCommitMessage": "feat: add qwen2.5:32b model support",
  "lastCommitTime": "2026-02-22T14:30:00Z",
  "lastCommitAuthor": "Demi",
  "openPRs": 2,
  "ciStatus": "success",
  "branch": "main",
  "sha": "a3f7b9c",
  "stars": 12,
  "repoUrl": "https://github.com/your-org/acm-ai"
}
```

e) Cache with: next: { revalidate: 120 } — re-fetch every 2 minutes

f) GRACEFUL FALLBACK: If GITHUB_TOKEN is not set or API fails, return static fallback:
```json
{
  "commits": 281, "lastCommitMessage": "demo mode — connect GitHub for live data",
  "ciStatus": "unknown", "branch": "main", "stars": 0, "_fallback": true
}
```

2. UPDATE src/components/landing/LiveStatusStrip.tsx:

Design: a dark, condensed strip (navy bg, 56px height, horizontal flex)
showing three sections: [GitHub] [Vercel] [Railway]

GitHub section display:
- Green/yellow/red dot based on ciStatus
- "⬢ {commits} commits" — teal colour
- "↑ {lastCommitMessage truncated to 40 chars}" — gray-300, monospace font
- "by {lastCommitAuthor} · {timeAgo(lastCommitTime)}" — gray-500, 11px
- On hover: expand to show SHA and open PR count
- Link: clicking opens GitHub repo in new tab

Use the timeAgo() utility:
```ts
function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return `${Math.floor(hrs / 24)}d ago`
}
```

3. Add a PULSING DOT animation for the CI status indicator:
```css
@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(1.3); }
}
```
- ciStatus "success" → green dot, pulses slowly (2s)
- ciStatus null (in progress) → yellow dot, pulses fast (0.8s)
- ciStatus "failure" → red dot, no pulse

4. Add .env.local.example update:
```
GITHUB_TOKEN=ghp_your_token_here
GITHUB_OWNER=your-github-org
GITHUB_REPO=acm-ai
```

After implementing, run:
npm run lint && npm run build

Report: actual commit count fetched (if token available), fallback mode status,
build result.
```

---

## PROMPT OPT-03: ANIMATION SYSTEM OVERHAUL
## Terminal B (PARALLEL with OPT-02) | Priority: P1

```
Read /mnt/skills/public/frontend-design/SKILL.md first.
Pay special attention to the Motion section: "one well-orchestrated page load with 
staggered reveals creates more delight than scattered micro-interactions."

You are overhauling the animation system in /home/claude/acm-ai-site/

Read src/lib/animations.ts and all component files that currently use Framer Motion.

TASK: Replace inconsistent ad-hoc animations with a cohesive, intentional system.

1. REWRITE src/lib/animations.ts as the single source of truth:

```ts
import { Variants } from 'framer-motion'

// Entrance animations — use these for ALL section reveals
export const pageEnter: Variants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.08, delayChildren: 0.1 } }
}

export const fadeUp: Variants = {
  hidden: { opacity: 0, y: 32 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: [0.22, 1, 0.36, 1] } }
}

export const fadeLeft: Variants = {
  hidden: { opacity: 0, x: -24 },
  visible: { opacity: 1, x: 0, transition: { duration: 0.5, ease: [0.22, 1, 0.36, 1] } }
}

export const scaleIn: Variants = {
  hidden: { opacity: 0, scale: 0.92 },
  visible: { opacity: 1, scale: 1, transition: { duration: 0.4, ease: [0.22, 1, 0.36, 1] } }
}

// Card hover — use for ALL cards (stat cards, stage cards, feature cards)
export const cardHover = {
  rest: { y: 0, boxShadow: '0 1px 3px rgba(0,0,0,0.1)' },
  hover: { y: -4, boxShadow: '0 12px 32px rgba(58,143,138,0.15)', transition: { duration: 0.2 } }
}

// Number counter — use for ALL animated numbers
export function useCountUp(target: number, duration = 1800, startOnMount = false) {
  // implementation using requestAnimationFrame
}

// Pipeline stage reveal — staggered with colour shift
export const stageReveal: Variants = {
  hidden: { opacity: 0, x: -16, filter: 'brightness(0.7)' },
  visible: (i: number) => ({
    opacity: 1, x: 0, filter: 'brightness(1)',
    transition: { delay: i * 0.12, duration: 0.45, ease: 'easeOut' }
  })
}

// Terminal log line — for pipeline log simulation
export const logLine: Variants = {
  hidden: { opacity: 0, x: -8 },
  visible: { opacity: 1, x: 0, transition: { duration: 0.25 } }
}
```

2. APPLY to these components (read each one first, then update):

src/components/landing/HowItWorks.tsx:
- Wrap the 3 cards in motion.div with pageEnter parent + fadeUp children
- Add cardHover to each card
- Trigger: IntersectionObserver (only animate when entering viewport)

src/components/landing/PipelinePreview.tsx:
- Each stage pill uses stageReveal with custom={index} prop
- Add a "connector line" between pills that draws itself using:
  motion.div with scaleX from 0→1 after the previous pill completes

src/demo/PipelineSection.tsx (the demo page):
- Enhance the terminal log with logLine variants
- Add a scanline CSS overlay to the terminal:
  ```css
  .terminal::after {
    content: '';
    position: absolute;
    inset: 0;
    background: repeating-linear-gradient(
      0deg,
      transparent,
      transparent 2px,
      rgba(0,255,0,0.015) 2px,
      rgba(0,255,0,0.015) 4px
    );
    pointer-events: none;
  }
  ```

src/components/landing/StatsCounter.tsx:
- Replace any CSS counter with useCountUp hook
- Easing: ease-out cubic (fast start, slow end)
- Only start when element is 20% in viewport

3. ADD a global page transition in src/app/layout.tsx:
```tsx
<motion.div
  initial={{ opacity: 0, y: 8 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ duration: 0.4, ease: 'easeOut' }}
>
  {children}
</motion.div>
```

After implementing: npm run lint && npm run build
Report: which files changed, animation patterns applied, build status.
```

---

## PROMPT OPT-04: PIPELINE SECTION — INTERACTIVE EXCALIDRAW + ENHANCED TERMINAL
## Terminal A (after OPT-02) | Priority: P1

```
Read /mnt/skills/public/frontend-design/SKILL.md first.

You are enhancing the Pipeline section in:
- src/app/demo/page.tsx (or src/components/demo/PipelineSection.tsx)
in the ACM-AI marketing site at /home/claude/acm-ai-site/

Read the current PipelineSection implementation first.

TASK: Make this section the most impressive part of the demo.

1. EXCALIDRAW SYSTEM DIAGRAM:
Create src/components/ExcalidrawDiagram.tsx with a pre-built pipeline diagram.

The diagram should visually represent:
PDF → [MinerU/Docling] → [ACM Parser] → [SurrealDB] → [AG Grid] → [BAR Export]

Build the Excalidraw elements array manually using the element schema:
```ts
const elements = [
  // Box for PDF:
  { id: 'pdf', type: 'rectangle', x: 20, y: 150, width: 120, height: 60,
    strokeColor: '#3a8f8a', backgroundColor: '#3a8f8a22', roundness: { type: 3 },
    label: { text: '📄 PDF Upload', fontSize: 14 } },
  // Arrow:
  { id: 'arr1', type: 'arrow', x: 140, y: 180, points: [[0,0],[80,0]],
    strokeColor: '#3a8f8a', endArrowhead: 'arrow' },
  // MinerU box:
  { id: 'mineru', type: 'rectangle', x: 220, y: 150, width: 140, height: 60,
    strokeColor: '#d4614a', backgroundColor: '#d4614a22', roundness: { type: 3 },
    label: { text: '🔍 MinerU\n/Docling', fontSize: 12 } },
  // Continue for all 6 stages...
]
```

Add labels below each box showing the stage name and key tool.
Use VAEA colours: teal for data boxes, coral for AI stages, navy for storage.

Render in a dark-themed container:
```tsx
<div style={{ height: 280, borderRadius: 12, overflow: 'hidden', 
              border: '1px solid #3a8f8a33' }}>
  <Excalidraw 
    initialData={{ elements, appState: { 
      viewBackgroundColor: '#1a2035',
      theme: 'dark',
      zoom: { value: 0.9 }
    }}}
    viewModeEnabled={true}
    zenModeEnabled={true}
  />
</div>
```

Use dynamic import (SSR=false):
```tsx
const Excalidraw = dynamic(
  () => import('@excalidraw/excalidraw').then(m => m.Excalidraw),
  { ssr: false, loading: () => <div className="h-64 animate-pulse bg-navy/50 rounded-xl" /> }
)
```

2. ENHANCED TERMINAL LOG SIMULATION:
When "Run Demo" is clicked:

a) Show a fake "Uploading PDF..." progress bar first (500ms, CSS width animation 0→100%)
b) Then the terminal opens with a slide-down animation (Framer Motion height: 0 → auto)
c) Log lines appear one by one with realistic timing:
   - Stage -1 logs: fast (every 200ms) — these are structural
   - Stage 1-2 logs: slower (every 600ms) — AI is working
   - Stage 2.5 logs: pulse the teal border while validating
   - Final "✅ Complete" line: bold green, scale up from 0.8→1.0 using Framer Motion

d) After completion, show 3 RESULT BADGES that pop in:
   [44 Records ✓] [96% Confidence ✓] [0 Validation Errors ✓]
   Each badge: scaleIn animation, 150ms stagger

e) Add a REPLAY button that resets and re-runs the simulation

3. STAGE PILL IMPROVEMENTS:
Each of the 7 stage pills should:
- Have a number badge in the top-right corner (Stage -1, 0, 0.5, 1, 2, 2.5, 3)
- When active (during demo): add a pulsing teal border animation
  `animation: activePulse 1s ease-in-out infinite`
  `@keyframes activePulse { 0%,100% { border-color: #3a8f8a } 50% { border-color: #3a8f8aaa } }`
- When completed: show a small checkmark icon in the top-right (replacing the number)
- Tooltip on hover: show the "Tools:" line from the stage data

After implementing: npm run lint && npm run build
Report changes and build status.
```

---

## PROMPT OPT-05: SPREADSHEET SECTION — ANIMATED AG GRID MOCKUP
## Terminal B (after OPT-03) | Priority: P1

```
Read /mnt/skills/public/frontend-design/SKILL.md first.

You are enhancing the Spreadsheet section in the demo page.
Site: /home/claude/acm-ai-site/
Read the current SpreadsheetSection.tsx first.

TASK: Make the AG Grid mockup feel real and interactive.

1. ROW REVEAL ANIMATION:
When the user first scrolls to this section (IntersectionObserver):
- The column header groups slide down from above (translateY -20px → 0)
- Then each data row reveals from left to right with Framer Motion, 80ms stagger
- Risk colour appears with a brief 300ms flash (brightness 1.5 → 1.0)

2. RISK COLOUR SYSTEM — make it more dramatic:
HIGH risk rows:
- Left border: 4px solid #ef4444
- Background: linear-gradient(90deg, #ef444408 0%, transparent 100%)
- Text: bold font weight
- On mount: brief red pulse (1 cycle of box-shadow 0→12px→0)

MEDIUM risk rows:
- Left border: 4px solid #f97316
- Background: linear-gradient(90deg, #f9731608 0%, transparent 100%)

LOW risk rows:
- Left border: 4px solid #22c55e
- Background: linear-gradient(90deg, #22c55e08 0%, transparent 100%)

3. INTERACTIVE ROW CLICK → CITATION PANEL:
When a row is clicked:
a) The row highlights with a teal left border pulse
b) A side panel slides in from the RIGHT with Framer Motion:
   - initial: { x: 320, opacity: 0 }
   - animate: { x: 0, opacity: 1, transition: { type: 'spring', stiffness: 300, damping: 30 } }

The citation panel shows:
```
┌─────────────────────────────────────────┐
│ 📄 Source Document                       │
│ Rathdowne_ACM_Register.pdf               │
│                                          │
│ 📍 Location in PDF                       │
│ Page {row.page} · Table {row.table}      │
│ Row {row.row}                            │
│                                          │
│ [████████████] ← grey PDF page mockup   │
│ [████ highlighted yellow block ████]     │
│ [████████████]                           │
│                                          │
│ 🔗 Citation Reference                    │
│ [acm:acm_record:abc123:risk_status]      │
│                                          │
│ ℹ {field name}: {cell value}            │
│                                          │
│                              [✕ Close]  │
└─────────────────────────────────────────┘
```

The "PDF page mockup" is:
- A div 200x260px, background #e8e8e8, border-radius 4px
- Inside: several lines of grey bars (div, h:8px, bg:#ccc, varying widths)
- One "highlight" block: yellow bg (#fef08a), positioned at y:40% of the mockup height

4. COLUMN PRESET BUTTONS — with icon + active state:
[📋 Essential View] [📊 Full BAR View] [🎯 Assessment Focus] [🗑️ Removal Tracking]

When clicked:
- Active button: teal fill, white text
- The visible columns in the mockup table update to show only relevant column groups
- Animate: a brief opacity 0.3 → 1.0 transition on the table body

5. SEARCH BAR — live filtering:
The search input at the top of the toolbar should actually filter the mock rows:
- onChange: filter gridRows array by checking if any cell value includes the search string
- Show "N results" in gray below the toolbar while filtering
- Empty state: "No records match your search" with a subtle icon

After implementing: npm run lint && npm run build
Report changes and build status.
```

---

## PROMPT OPT-06: PROGRESS DASHBOARD — LIVE CHARTS + GITHUB COMMITS
## Terminal A (after OPT-04) | Priority: P1

```
Read /mnt/skills/public/frontend-design/SKILL.md and 
/mnt/skills/examples/theme-factory/SKILL.md first.

You are enhancing the Progress section in the demo page.
Site: /home/claude/acm-ai-site/
Read the current ProgressSection.tsx (or equivalent) first.

The Theme Factory skill says to apply consistent theme. Apply "Tech Innovation" 
theme (bold and modern) to this section's chart palette.

TASK: Make the Progress section a genuine project delivery dashboard.

1. HERO METRICS — animated ring charts:
Replace the flat stat cards with animated SVG ring/donut charts:

For each metric, create an SVG circle that draws itself:
```tsx
function RingMetric({ value, max, label, color }: {...}) {
  const circumference = 2 * Math.PI * 40  // radius 40
  const progress = (value / max) * circumference
  return (
    <div className="flex flex-col items-center">
      <svg width="96" height="96" viewBox="0 0 96 96">
        {/* Background track */}
        <circle cx="48" cy="48" r="40" fill="none" stroke="#2a2f4533" strokeWidth="8" />
        {/* Progress arc */}
        <motion.circle
          cx="48" cy="48" r="40" fill="none"
          stroke={color} strokeWidth="8" strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: circumference - progress }}
          transition={{ duration: 1.5, ease: 'easeOut', delay: 0.3 }}
          style={{ transformOrigin: '50% 50%', transform: 'rotate(-90deg)' }}
        />
        {/* Center text */}
        <text x="48" y="52" textAnchor="middle" fill={color} 
              fontSize="18" fontWeight="bold" fontFamily="DM Serif Display">
          {value}
        </text>
      </svg>
      <span className="text-xs text-gray-400 mt-2 text-center">{label}</span>
    </div>
  )
}
```

Metrics to show:
- 87/122 stories → ring 71% full → teal → "Stories Complete"
- 16/17 epics → ring 94% full → coral → "Epics Done"
- 87% E2E accuracy → ring 87% full → success green → "Extraction Accuracy"
- 281 commits → no ring, just large counter → navy → "Git Commits"

2. GITHUB INTEGRATION — real commit data in the chart:
Fetch from /api/github/stats (from OPT-02) using useSWR.
Show the real commit count in the "Git Commits" card.

3. RECHARTS — UPGRADE ALL CHARTS:

Epic stories BarChart:
- Change from solid teal bar → gradient fill:
  Define a LinearGradient defs element, gradient from teal to coral (top to bottom)
- Add custom tooltip with rounded corners + shadow:
```tsx
const CustomTooltip = ({ active, payload }: any) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-navy text-white text-xs px-3 py-2 rounded-lg shadow-lg border border-teal/20">
      <p className="font-semibold">{payload[0].payload.epic}</p>
      <p className="text-teal">{payload[0].value} stories</p>
    </div>
  )
}
```
- X-axis labels: rotate -35deg, fontSize 11px
- Add ReferenceLine at y=8 (average velocity line) with a label "Avg velocity"

Sprint velocity LineChart:
- Change from Line to AreaChart with gradient fill
- Area fill: teal gradient (opacity 0.3 → 0)
- Add animated dot that pulses on the last data point (current sprint)
- Add a second line "Target" in coral dashed

Radar chart (NEW — add this):
```tsx
import { RadarChart, Radar, PolarGrid, PolarAngleAxis } from 'recharts'

const radarData = [
  { subject: 'Pipeline', completion: 97 },
  { subject: 'Grid/UX', completion: 83 },
  { subject: 'Export', completion: 50 },
  { subject: 'Chat', completion: 100 },
  { subject: 'Infrastructure', completion: 78 },
  { subject: 'Testing', completion: 87 },
]

<RadarChart cx={150} cy={150} outerRadius={100} width={300} height={300} data={radarData}>
  <PolarGrid stroke="#3a8f8a33" />
  <PolarAngleAxis dataKey="subject" tick={{ fill: '#9ca3af', fontSize: 11 }} />
  <Radar dataKey="completion" stroke="#3a8f8a" fill="#3a8f8a" fillOpacity={0.25} />
</RadarChart>
```

4. EPIC STATUS TABLE — enhanced:
Add a progress bar column to each row showing % complete:
```tsx
<div className="w-full bg-navy/30 rounded-full h-1.5">
  <motion.div 
    className="h-1.5 rounded-full"
    style={{ backgroundColor: epic.statusColor }}
    initial={{ width: 0 }}
    animate={{ width: `${epic.completion}%` }}
    transition={{ duration: 0.8, delay: index * 0.05 }}
  />
</div>
```

After implementing: npm run lint && npm run build
Report changes and new chart components added.
```

---

## PROMPT OPT-07: DOCUMENTATION — FUMADOCS THEME + MDX CONTENT
## Terminal B (after OPT-05) | Priority: P1

```
Read /mnt/skills/public/frontend-design/SKILL.md first.

You are enhancing the Fumadocs documentation at /home/claude/acm-ai-site/src/app/docs/
Read the current docs layout.tsx and any existing MDX files first.

TASK: Make the docs look like a premium product documentation site.

1. FUMADOCS THEME OVERRIDE:
In src/app/docs/layout.tsx, customise the Fumadocs theme:
```tsx
import { DocsLayout } from 'fumadocs-ui/layouts/docs'
import { RootToggle } from 'fumadocs-ui/components/layout/root-toggle'

const options = {
  nav: {
    title: (
      <div className="flex items-center gap-2">
        <div className="w-6 h-6 rounded bg-teal flex items-center justify-center">
          <span className="text-white text-xs font-bold">A</span>
        </div>
        <span className="font-semibold text-sm">ACM-AI Docs</span>
      </div>
    ),
  },
  sidebar: {
    tabs: [
      { title: 'Guides', url: '/docs/guides', icon: <BookOpenIcon /> },
      { title: 'PRD', url: '/docs/prd', icon: <FileTextIcon /> },
      { title: 'Architecture', url: '/docs/architecture', icon: <LayersIcon /> },
      { title: 'Epics', url: '/docs/epics', icon: <ListIcon /> },
    ]
  }
}
```

Add custom CSS to override Fumadocs default colours with VAEA tokens:
```css
/* In globals.css, add: */
.fumadocs-sidebar {
  --fd-primary: #3a8f8a;
  --fd-sidebar-bg: #1e2537;
  --fd-sidebar-item-hover: rgba(58,143,138,0.1);
}
[data-docs-item][data-active="true"] {
  color: #3a8f8a !important;
  background: rgba(58,143,138,0.1) !important;
}
```

2. CREATE THESE MDX FILES (read corresponding project docs first):

Read: _bmad-output/project-planning-artifacts/acm-ai/03-prd.md
Create: src/content/docs/prd/index.mdx
Content should include:
- Callout box: "This is the living PRD for ACM-AI. Last updated: Feb 2026."
- Overview table (Priority, Scope, Status)
- FR-100 functional requirements as a table (extract from PRD section 2.1)
- FR-200 data model requirements table
- Link to architecture and epics sections

Read: _bmad-output/project-planning-artifacts/acm-ai/04-architecture.md  
Create: src/content/docs/architecture/pipeline.mdx
Content: The 7-stage pipeline with a CodeBlock showing the architecture ASCII art,
and explanation of each stage as an H3 section.

Create: src/content/docs/guides/model-setup.mdx
Content: The Qwen2.5:32b setup guide (Ollama + OpenRouter), extracted from 
the knowledge base research we conducted:
- Prerequisites
- Ollama installation commands (in CodeBlock with bash syntax)
- OpenRouter configuration
- Verification commands
- Troubleshooting common issues (OpenRouter structured output failures, token limits)

Create: src/content/docs/guides/quick-start.mdx
Content:
1. Installation (clone, env setup, SurrealDB, API, frontend start)
2. First extraction (upload PDF, watch pipeline, view grid)
3. Export BAR Excel
Each step as numbered headings with code blocks.

3. ADD CALLOUT COMPONENTS in each MDX:
```mdx
import { Callout } from 'fumadocs-ui/components/callout'

<Callout type="warn" title="Government Compliance">
  Exports must match the Victorian Government BAR template exactly. 
  Use the official VAEA Excel template for validation.
</Callout>

<Callout type="info" title="Local Processing">
  ACM-AI extracts data locally — no PDF content is sent to external servers 
  unless you configure a cloud LLM provider.
</Callout>
```

4. ADD SYNTAX HIGHLIGHTING for all code blocks:
Use Shiki with themes:
- Light mode: 'github-light'
- Dark mode: 'github-dark'

In fumadocs.config.ts:
```ts
import { defineConfig } from 'fumadocs-mdx/config'
import { rehypeCode } from 'fumadocs-core/mdx-plugins'

export default defineConfig({
  mdxOptions: {
    rehypePlugins: [[rehypeCode, { theme: { dark: 'github-dark', light: 'github-light' } }]]
  }
})
```

After implementing: npm run lint && npm run build
Report: MDX files created, any Fumadocs theme issues, build status.
```

---

## PROMPT OPT-08: STATUS PAGE — INFRASTRUCTURE DASHBOARD
## Terminal A (after OPT-06) | Priority: P2

```
Read /mnt/skills/public/frontend-design/SKILL.md first.

You are building the /status page at /home/claude/acm-ai-site/src/app/status/page.tsx
Read the current status page implementation if it exists.

DESIGN DIRECTION: "Mission Control" — dark operational dashboard, like a NASA 
control room or a modern SRE incident board. Dark bg, green/yellow/red status lights.

1. HERO BAR:
Full-width dark strip at top:
"🟢 All Systems Operational" (or 🟡/🔴 based on real status)
Auto-updates every 30 seconds using SWR with refreshInterval: 30000.
Show timestamp: "Last checked: {timeAgo}"

2. INFRASTRUCTURE STATUS CARDS (3 cards in a row):

GITHUB CARD:
```tsx
<StatusCard
  title="GitHub Repository"
  icon={<GithubIcon />}
  status="operational"  // from API
  metrics={[
    { label: "Total Commits", value: data.commits, trend: "+3 today" },
    { label: "Open PRs", value: data.openPRs },
    { label: "CI Status", value: data.ciStatus, badge: true },
    { label: "Last Push", value: timeAgo(data.lastCommitTime) },
  ]}
  details={`"${data.lastCommitMessage}" by ${data.lastCommitAuthor}`}
  link={data.repoUrl}
/>
```

VERCEL CARD:
```tsx
<StatusCard
  title="Vercel Deployment"
  icon={<VercelIcon />}  // triangle SVG
  status={vercelData.state === 'READY' ? 'operational' : 'degraded'}
  metrics={[
    { label: "Environment", value: "Production" },
    { label: "Status", value: vercelData.state, badge: true },
    { label: "Last Deploy", value: timeAgo(vercelData.createdAt) },
    { label: "Build Time", value: `${vercelData.buildDuration}s` },
  ]}
  details={`${vercelData.url}`}
  link={`https://${vercelData.url}`}
/>
```

RAILWAY CARD:
```tsx
<StatusCard
  title="Railway Services"
  icon={<RailwayIcon />}  // simple train icon SVG
  status="operational"
  metrics={[
    { label: "API Service", value: "Running", badge: true },
    { label: "SurrealDB", value: "Running", badge: true },
    { label: "Worker", value: "Running", badge: true },
  ]}
/>
```

3. StatusCard component design:
- Dark card (bg: #1a2035, border: 1px solid rgba(58,143,138,0.2))
- Status indicator dot: 8px circle, top-right of card header
  - operational: #22c55e (green, CSS pulse animation)
  - degraded: #f59e0b (yellow)
  - incident: #ef4444 (red)
- Metric rows: label in gray-400, value in gray-100, bold
- Trend badges: small pill in green/red based on direction

4. PROJECT HEALTH SECTION:
Below the infrastructure cards, show project metrics from sprint data:

```tsx
const sprintData = {
  storiesDone: 87,
  storiesTotal: 122,
  epicsComplete: 16,
  epicsTotal: 17,
  extractionAccuracy: 87,
  lastTestRun: '2026-02-23',
  e2ePass: 27,
  e2eTotal: 31,
}
```

Show as a grid of metric rows with mini progress bars.
Include a "Test Suite" section showing test category breakdown.

5. INCIDENT HISTORY (static, last 30 days):
A simple timeline of resolved issues:
- Feb 22: Migration runner registration fix (resolved)
- Feb 21: Negative results regression fix (resolved)  
- Feb 16: E2E accuracy 70% → 87% via PR #30 (resolved)

After implementing: npm run lint && npm run build
Report build status and any API integration issues.
```

---

## PROMPT OPT-09: ROADMAP PAGE — VISUAL TIMELINE
## Terminal B (after OPT-07) | Priority: P2

```
Read /mnt/skills/public/frontend-design/SKILL.md and
/mnt/skills/examples/canvas-design/SKILL.md first.

From canvas-design skill: commit to a visual philosophy first.
Philosophy for roadmap: "Structured Time" — information encoded in position and 
colour, like a Gantt chart elevated to art. Milestones float like geological strata.

You are building /home/claude/acm-ai-site/src/app/roadmap/page.tsx
Read the current roadmap page if it exists.

1. HORIZONTAL SCROLLABLE TIMELINE:
A full-width horizontal timeline that users can scroll or drag.
Each milestone is a vertical card hanging below the timeline spine.

Timeline spine: a horizontal teal line (#3a8f8a, 2px) with dots at each milestone.
Below the spine: milestone cards. Above the spine: date labels.

Layout:
```
                    FEB 2026                    MAR 2026
─────────────●──────────────●──────────────●──────────────●──→
             │              │              │              │
           [E1 Pipeline]  [E14 UX]    [E18 Quality]   [E19 Site]
           [31 stories ✓] [11 stories ✓] [In progress]  [This!]
```

2. MILESTONE CARDS:
```tsx
type MilestoneStatus = 'done' | 'in-progress' | 'upcoming'

const milestones = [
  { id: 'e1', epic: 'E1', title: 'ACM Extraction Pipeline', stories: 31, 
    status: 'done', date: 'Jan 2026', highlight: 'MinerU + 7-stage LangGraph pipeline' },
  { id: 'e3', epic: 'E3', title: 'Citations & PDF Viewer', stories: 4, 
    status: 'done', date: 'Jan 2026', highlight: 'Click any cell → source PDF page' },
  { id: 'e4', epic: 'E4', title: 'AI Chat Integration', stories: 4, 
    status: 'done', date: 'Feb 2026', highlight: 'CopilotKit + AG-UI SSE streaming' },
  { id: 'e5', epic: 'E5', title: 'BAR Export', stories: 4,
    status: 'in-progress', date: 'Feb 2026', highlight: '47-column VAEA Excel export' },
  { id: 'e14', epic: 'E14', title: 'Enterprise UX', stories: 11,
    status: 'done', date: 'Feb 2026', highlight: 'WCAG 2.1 AA, VAEA branding, skeleton loaders' },
  { id: 'e18', epic: 'E18', title: 'Extraction Quality', stories: 5,
    status: 'in-progress', date: 'Feb 2026', highlight: '84% → 100% accuracy target' },
  { id: 'e17', epic: 'E17', title: 'Live AI Intelligence', stories: 6,
    status: 'upcoming', date: 'Mar 2026', highlight: 'AG-UI streaming, A2A protocol' },
  { id: 'e19', epic: 'E19', title: 'Marketing & Docs', stories: 3,
    status: 'in-progress', date: 'Feb 2026', highlight: 'This site!' },
  { id: 'e13', epic: 'E13', title: 'Knowledge Graph', stories: 3,
    status: 'upcoming', date: 'Q2 2026', highlight: 'React Flow visualization' },
  { id: 'e5s3', epic: 'E5-S3', title: 'BAR Template Mgmt', stories: 1,
    status: 'upcoming', date: 'Mar 2026', highlight: 'Upload official VAEA template' },
]
```

Card visual by status:
- done: teal fill, white text, checkmark icon, solid border
- in-progress: teal outline only, teal text, animated pulse border, coral "Live" badge
- upcoming: navy fill 50%, gray text, outlined, "Planned" badge

3. FRAMER MOTION ENTRANCE:
When user scrolls to timeline:
- The timeline spine draws from left to right (scaleX: 0 → 1, origin left)
- Then dots appear one by one (scale: 0 → 1, staggered 100ms)
- Then cards drop in from above (y: -20 → 0, staggered 80ms)

Use the IntersectionObserver pattern:
```tsx
const { ref, inView } = useInView({ threshold: 0.1 })
<motion.div ref={ref} animate={inView ? 'visible' : 'hidden'}>
```

4. "WHAT'S NEXT" SECTION:
Below the timeline, 3 priority cards for the next sprint:
```
┌────────────────────────┐  ┌────────────────────────┐  ┌────────────────────────┐
│ 🎯 TOP PRIORITY        │  │ ⚡ QUICK WIN           │  │ 🔬 RESEARCH            │
│ E5-S3 BAR Template    │  │ E16-S1 Dashboard       │  │ E17-S1 AG-UI Live     │
│ Management             │  │ Home + Stats           │  │ Streaming              │
│                        │  │                        │  │                        │
│ Unblocks E5-S4         │  │ Welcome page for       │  │ Incremental records    │
│ field mapping          │  │ compliance officers    │  │ into AG Grid live      │
│                        │  │                        │  │                        │
│ [📋 View Story →]      │  │ [📋 View Story →]      │  │ [📋 View Story →]      │
└────────────────────────┘  └────────────────────────┘  └────────────────────────┘
```

After implementing: npm run lint && npm run build
Report build status and timeline render quality.
```

---

## PROMPT OPT-10: FINAL POLISH — ICONS, COLOURS, RESPONSIVENESS, SEO
## Terminal A (final pass) | Priority: P0 before delivery

```
Read /mnt/skills/public/frontend-design/SKILL.md and 
/mnt/skills/examples/theme-factory/SKILL.md first.

From theme-factory: the active theme for ACM-AI is a custom theme:
Name: "VAEA Authority"
Primary: #3a8f8a (teal) 
Accent: #d4614a (coral)
Dark: #2a2f45 (navy)
Fonts: DM Serif Display (display) + DM Sans (body) + JetBrains Mono (code)
Apply this theme consistently to ALL pages.

You are doing a final polish pass on /home/claude/acm-ai-site/
Read ALL page files first (page.tsx for /, /demo, /status, /roadmap, /docs layout).

TASK: Audit and fix 10 specific things:

1. ICON CONSISTENCY AUDIT:
- All pages must use lucide-react icons only (no @radix-ui/react-icons mixed in)
- Replace any emoji used as icons with proper Lucide components
- Icon sizes: 16px for inline text, 20px for buttons, 24px for section headers, 32px for hero
- All icons must have aria-hidden="true" if decorative

2. COLOUR CONSISTENCY AUDIT:
- Search for any hardcoded hex codes that are NOT from the VAEA palette
  (any hex not in: #3a8f8a, #d4614a, #2a2f45, #f4f7f9, #4caf82, #f59e0b, #ef4444, #f97316, #22c55e)
- Replace non-palette colours with CSS variables (var(--teal), var(--coral), etc.)
- Ensure dark mode works correctly: test by adding .dark class to html element

3. TYPOGRAPHY AUDIT:
- All h1 elements: DM Serif Display font
- All h2, h3: DM Sans, font-weight: 600
- All body text: DM Sans, font-weight: 400
- All code blocks: JetBrains Mono
- Check that Google Fonts are loaded in layout.tsx:
  ```tsx
  import { DM_Serif_Display, DM_Sans, JetBrains_Mono } from 'next/font/google'
  const dmSerif = DM_Serif_Display({ weight: '400', subsets: ['latin'] })
  const dmSans = DM_Sans({ subsets: ['latin'] })
  const jetbrains = JetBrains_Mono({ subsets: ['latin'] })
  ```

4. RESPONSIVE BREAKPOINTS — check each section:
Test at these widths and fix any overflow or broken layouts:
- 375px (iPhone SE)
- 768px (iPad)
- 1280px (laptop)
- 1920px (desktop)

Common fixes needed:
- Pipeline pills: horizontal scroll on mobile (overflow-x: auto on container)
- Charts: ensure ResponsiveContainer height is fixed not 100%
- Sidebar (demo page): collapse to a horizontal tab bar on mobile (<768px)
- Hero headline: ensure 40px on mobile, not overflowing
- Status cards: stack vertically on mobile

5. SEO & METADATA — add to all pages:
In each page.tsx, add:
```tsx
export const metadata: Metadata = {
  title: 'ACM-AI — {page specific title} | VAEA Asbestos Compliance Intelligence',
  description: 'ACM-AI converts Victorian Government SAMP/BAR PDF asbestos registers into BAR-compliant spreadsheets using a 7-stage AI extraction pipeline.',
  keywords: ['asbestos compliance', 'BAR register', 'Victorian Government', 'VAEA', 'ACM management'],
  openGraph: {
    title: 'ACM-AI — Asbestos Compliance Intelligence',
    description: 'Transform PDF asbestos registers into government-ready BAR data with AI.',
    type: 'website',
    locale: 'en_AU',
  },
}
```

6. LOADING STATES — add skeletons everywhere:
For any component that uses useSWR or fetches data:
```tsx
if (isLoading) return (
  <div className="animate-pulse space-y-3">
    <div className="h-4 bg-gray-200 rounded w-3/4" />
    <div className="h-4 bg-gray-200 rounded w-1/2" />
    <div className="h-4 bg-gray-200 rounded w-2/3" />
  </div>
)
```

7. ACCESSIBILITY AUDIT:
- All interactive elements must have aria-label or visible text
- Focus rings: add `focus-visible:ring-2 focus-visible:ring-teal focus-visible:ring-offset-2`
- Skip-to-content link at the top of layout:
  ```tsx
  <a href="#main-content" className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 bg-teal text-white px-4 py-2 rounded z-50">
    Skip to main content
  </a>
  ```

8. PERFORMANCE:
- All images (if any): use next/image with proper width/height
- All Lottie players: add loading="lazy" equivalent
- Excalidraw: ensure it's dynamically imported with ssr: false
- Charts: use ResponsiveContainer with debounced resize

9. ERROR BOUNDARIES:
Add an error boundary around Excalidraw and Lottie:
```tsx
'use client'
import { Component } from 'react'
class DiagramErrorBoundary extends Component<{children, fallback}, {hasError}> {
  // standard error boundary pattern
}
```

10. ADD A FAVICON AND OG IMAGE:
Create public/favicon.svg as an SVG:
```svg
<svg viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
  <rect width="32" height="32" rx="6" fill="#3a8f8a"/>
  <text x="16" y="22" font-family="Georgia" font-size="18" font-weight="bold" 
        fill="white" text-anchor="middle">A</text>
</svg>
```

After all fixes, run:
npm run lint && npm run build

Copy to output:
cp -r /home/claude/acm-ai-site /mnt/user-data/outputs/acm-ai-site-final

Report:
- How many icon inconsistencies fixed
- How many colour mismatches fixed  
- Any accessibility violations remaining
- Final build size (output from next build)
- Lighthouse score estimate based on implementation
```

---

## QUICK REFERENCE — SKILL READ COMMANDS

```bash
# Always paste these at the start of each Claude Code session
cat /mnt/skills/public/frontend-design/SKILL.md
cat /mnt/skills/examples/theme-factory/SKILL.md
cat /mnt/skills/examples/canvas-design/SKILL.md
cat /mnt/skills/examples/web-artifacts-builder/SKILL.md
```

## PARALLEL EXECUTION MAP

```
Terminal A                          Terminal B
──────────────────                  ──────────────────
OPT-01 Hero animations              OPT-03 Animation system
OPT-02 GitHub live commits      →   OPT-05 Spreadsheet polish
OPT-04 Pipeline + Excalidraw    →   OPT-07 Fumadocs + MDX
OPT-06 Progress dashboard       →   OPT-09 Roadmap timeline
OPT-08 Status page              
OPT-10 Final polish (both merge)
```

## VAEA THEME QUICK REFERENCE

```
Primary teal:    #3a8f8a | var(--teal)
Accent coral:    #d4614a | var(--coral)
Navy:            #2a2f45 | var(--navy)
Background:      #f4f7f9 | var(--bg)
Card:            #ffffff | var(--card)
Success:         #4caf82 | var(--success)
Warning:         #f59e0b | var(--warn)
Risk High:       #ef4444 | var(--risk-high)
Risk Medium:     #f97316 | var(--risk-medium)
Risk Low:        #22c55e | var(--risk-low)

Fonts:
  Display:   DM Serif Display (Google Fonts)
  Body:      DM Sans (Google Fonts)
  Mono:      JetBrains Mono (Google Fonts)
```
