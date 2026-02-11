# Tech-Spec: E3-S3 ACM Citation Reference Type

**Created:** 2025-12-07
**Status:** Done
**Epic:** E3 - Cell Citations & PDF Viewer
**Story:** S3 - Implement ACM Citation Reference Type
**Implemented:** 2026-01-08
**Reviewed:** 2026-01-08

---

## Overview

### Problem Statement

The chat system can reference sources and notes using `[source:id]` and `[note:id]` patterns. ACM-AI needs a similar pattern `[acm:record_id:field_name]` so AI responses can cite specific ACM data cells.

### Solution

Extend the citation parser in `source-references.tsx` to:
- Recognize `[acm:record_id:field]` pattern
- Convert to clickable link
- Open ACMCellViewer modal on click
- Gracefully handle invalid references

### Scope

**In Scope:**
- Add ACM_REFERENCE_PATTERN regex
- Create ACMCitationLink component
- Integrate with existing citation system

**Out of Scope:**
- Modifying AI prompt (E4-S3)
- Creating new citations

---

## Implementation Plan

### Tasks

- [x] **Task 1: Analyze existing citation patterns**
  - Read `frontend/src/lib/utils/source-references.tsx`
  - Understand parseSourceReferences function

- [x] **Task 2: Add ACM citation pattern**
  - Pattern: `/acm:([^:\]\s]+):?([^:\]\s]*)/g`
  - Match: `[acm:record_id:field]` or `[acm:record_id]`

- [x] **Task 3: Create ACMCitationLink component**
  - Render as clickable badge/link
  - Styled with amber color scheme
  - Open ACMCellViewer modal via onACMClick handler

- [x] **Task 4: Integrate into parseSourceReferences**
  - Added ACM pattern to parseSourceReferences()
  - Created convertSourceReferencesExtended() with ReferenceClickHandlers
  - Created createReferenceLinkComponentExtended() for ReactMarkdown
  - Updated convertReferencesToMarkdownLinks() for ACM support

### Acceptance Criteria

- [x] **AC1**: Parser recognizes `[acm:record_id:field]` pattern
- [x] **AC2**: Converts to clickable link in chat
- [x] **AC3**: Click opens ACMCellViewer modal (via onACMClick handler)
- [x] **AC4**: Gracefully handles invalid references

---

## Code Specification

### File: `frontend/src/lib/utils/source-references.tsx` (modifications)

```typescript
// Add to existing patterns
const ACM_REFERENCE_PATTERN = /\[acm:([^:\]]+):?([^\]]*)\]/g

// Add ACMCitationLink component
function ACMCitationLink({
  recordId,
  field,
  onOpen
}: {
  recordId: string
  field?: string
  onOpen: (recordId: string, field: string) => void
}) {
  const handleClick = () => {
    onOpen(recordId, field || 'product')
  }

  return (
    <button
      onClick={handleClick}
      className="inline-flex items-center gap-1 px-1.5 py-0.5 text-xs font-medium
                 bg-amber-100 text-amber-800 rounded hover:bg-amber-200
                 dark:bg-amber-900 dark:text-amber-200"
    >
      <FileSpreadsheet className="h-3 w-3" />
      ACM {field || 'record'}
    </button>
  )
}

// Add to parseSourceReferences function
export function parseSourceReferences(
  text: string,
  handlers: {
    onSourceClick?: (id: string) => void
    onNoteClick?: (id: string) => void
    onInsightClick?: (id: string) => void
    onACMClick?: (recordId: string, field: string) => void  // NEW
  }
): React.ReactNode[] {
  // ... existing code ...

  // Add ACM pattern matching
  const acmMatches = text.matchAll(ACM_REFERENCE_PATTERN)
  for (const match of acmMatches) {
    const [fullMatch, recordId, field] = match
    // Replace with ACMCitationLink component
  }
}
```

---

## Dependencies

| Dependency | Type | Notes |
|------------|------|-------|
| E3-S2 (PDF Viewer) | Story | Modal to open |
| Existing citation system | Code | source-references.tsx |

---

## Dev Agent Record

### Implementation Notes (2026-01-08)

**File Modified:** `frontend/src/lib/utils/source-references.tsx`

**Changes Made:**
1. Extended `ReferenceType` to include `'acm'`
2. Added optional `field?: string` to `ParsedReference` interface
3. Enhanced `parseSourceReferences()` with ACM pattern matching
4. Created `ReferenceClickHandlers` interface with `onACMClick` handler
5. Created `ACMCitationLink` component with amber badge styling
6. Created `convertSourceReferencesExtended()` for ACM-aware rendering
7. Updated `convertReferencesToMarkdownLinks()` with ACM support
8. Created `createReferenceLinkComponentExtended()` for ReactMarkdown integration

**Verification:**
- TypeScript compilation: ✅ Pass
- ESLint: ✅ Pass (no new warnings)

### Code Review Fixes (2026-01-08)

**Issues Fixed:**
1. **[H2] Fixed ACM pattern for SurrealDB record IDs** - Updated regex to properly capture `table_name:record_id:optional_field` format. Pattern now correctly handles `[acm:acm_record:abc123:product]`.
2. **[M2] Added JSDoc to ACMCitationLink** - Added proper documentation with @param and @example.
3. **[M3] Fixed convertReferencesToCompactMarkdown for ACM** - Updated to include field in deduplication key and hrefs for ACM references.

**Deferred Issues (no test framework in project):**
- **[H1] Unit tests** - Frontend has no Jest/Vitest setup. Tests should be added when test framework is configured.

**Final Verification:**
- TypeScript compilation: ✅ Pass
- Code review: ✅ All fixable issues addressed

---

*Tech-Spec generated by create-tech-spec workflow*
