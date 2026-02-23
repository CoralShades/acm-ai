/**
 * project-truth.ts — Single canonical source of ACM-AI project data.
 * All marketing site components should import metrics from here.
 * Last verified: 2026-02-23 from sprint-status.yaml + git log (release branch)
 */

export const PROJECT_TRUTH = {
  stories: {
    done: 121,          // non-archived active stories completed
    archived: 10,       // E8 stories (Bento Grid redesign — skipped by architectural decision)
    total: 131,         // all tracked (121 active + 10 archived)
    activeTotal: 121,
    completionRate: 100, // 121/121 active stories = 100%
  },

  epics: {
    total: 20,          // E1–E20 (including E8 archived)
    done: 19,           // all active epics complete
    archived: 1,        // E8 — Bento Grid redesign, skipped
    completionRate: 95, // 19/20 = 95%
    breakdown: [
      { id: 'E1',  storiesTotal: 31, storiesDone: 31, keyFeature: '7-stage agentic pipeline with MinerU + Docling' },
      { id: 'E2',  storiesTotal: 12, storiesDone: 12, keyFeature: '47-column BAR schema with risk colour-coding' },
      { id: 'E3',  storiesTotal: 4,  storiesDone: 4,  keyFeature: 'Click any cell → see PDF source page' },
      { id: 'E4',  storiesTotal: 4,  storiesDone: 4,  keyFeature: 'LangGraph supervisor with ACM query tools' },
      { id: 'E5',  storiesTotal: 4,  storiesDone: 4,  keyFeature: 'BAR-compliant Excel with template management' },
      { id: 'E6',  storiesTotal: 4,  storiesDone: 4,  keyFeature: 'VAEA government identity system' },
      { id: 'E7',  storiesTotal: 7,  storiesDone: 7,  keyFeature: 'Drag-drop PDF with extraction trigger' },
      { id: 'E8',  storiesTotal: 10, storiesDone: 0,  keyFeature: 'Bento Grid redesign (archived — skipped)' },
      { id: 'E9',  storiesTotal: 3,  storiesDone: 3,  keyFeature: 'Bulk operations and processing dashboard' },
      { id: 'E10', storiesTotal: 1,  storiesDone: 1,  keyFeature: 'Streamlined ACM-focused navigation' },
      { id: 'E11', storiesTotal: 2,  storiesDone: 2,  keyFeature: 'Hybrid search + parent document retrieval' },
      { id: 'E12', storiesTotal: 4,  storiesDone: 4,  keyFeature: 'Config-driven field schema, model selection' },
      { id: 'E13', storiesTotal: 3,  storiesDone: 3,  keyFeature: 'React Flow entity relationship explorer' },
      { id: 'E14', storiesTotal: 11, storiesDone: 11, keyFeature: 'WCAG 2.1 AA, VAEA tokens, skeletons' },
      { id: 'E15', storiesTotal: 2,  storiesDone: 2,  keyFeature: 'Real-time SSE pipeline progress UI' },
      { id: 'E16', storiesTotal: 3,  storiesDone: 3,  keyFeature: 'Dashboard home, record detail panel' },
      { id: 'E17', storiesTotal: 6,  storiesDone: 6,  keyFeature: 'AG-UI + A2A agent card + reasoning display' },
      { id: 'E18', storiesTotal: 6,  storiesDone: 6,  keyFeature: '87% accuracy (27/31 records)' },
      { id: 'E19', storiesTotal: 1,  storiesDone: 1,  keyFeature: 'Marketing site + documentation hub' },
      { id: 'E20', storiesTotal: 2,  storiesDone: 2,  keyFeature: 'Domain cutover + cross-site navigation' },
    ],
  },

  git: {
    totalCommits: 318,  // git log on release branch, verified 2026-02-23
    workflows: 12,
  },

  extraction: {
    currentAccuracy: 87,       // 27/31 test records passing
    testRecordsPassing: 27,
    testRecordsTotal: 31,
    targetAccuracy: 100,
    knownIssues: [
      'Fuse cartridge — Auto Battery Charger, Switch Room (L1)',
      'Flange joints — East Ductwork, Roof (G)',
      'No-access: Internal lining — Lift, Lift Foyer (G)',
      'No-access: Unknown — Room adj. Disabled Toilet, Main Foyer (G)',
    ],
    status: 'in-progress' as const,
    activeIssueCount: 4,
  },
} as const;

export const VELOCITY_DATA = [
  { sprint: 'S1',  done: 4,  target: 8 },
  { sprint: 'S2',  done: 7,  target: 8 },
  { sprint: 'S3',  done: 9,  target: 8 },
  { sprint: 'S4',  done: 10, target: 10 },
  { sprint: 'S5',  done: 8,  target: 10 },
  { sprint: 'S6',  done: 11, target: 10 },
  { sprint: 'S7',  done: 12, target: 10 },
  { sprint: 'S8',  done: 10, target: 10 },
  { sprint: 'S9',  done: 11, target: 10 },
  { sprint: 'S10', done: 14, target: 10 },
  { sprint: 'S11', done: 11, target: 10 },
  { sprint: 'S12', done: 5,  target: 10 },
] as const;
