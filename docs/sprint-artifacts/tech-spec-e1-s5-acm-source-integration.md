# Tech Spec: E1-S5 - Integrate ACM Extraction into Source Processing

> **Story:** E1-S5
> **Epic:** ACM Data Extraction Pipeline
> **Status:** Draft
> **Created:** 2025-12-08

---

## Overview

Integrate ACM extraction transformation into the existing source processing pipeline so that ACM data is automatically extracted when users upload SAMP/ACM Register documents.

---

## User Story

**As a** user
**I want** ACM extraction to happen automatically when I upload a SAMP
**So that** I don't need to manually trigger it

---

## Acceptance Criteria

- [ ] Option to enable ACM extraction on source upload
- [ ] Processing status shown during extraction
- [ ] Errors handled gracefully with user feedback
- [ ] Can re-run extraction if needed

---

## Technical Design

### 1. Backend Changes

#### Modify Source Commands (`commands/source_commands.py`)

```python
# Add ACM extraction option to process_source command
@dataclass
class ProcessSourceCommand:
    source_id: str
    transformations: list[str] = field(default_factory=list)
    enable_acm_extraction: bool = False  # New field

async def handle_process_source(cmd: ProcessSourceCommand):
    source = await Source.get(cmd.source_id)

    # Run standard transformations
    for transform in cmd.transformations:
        await run_transformation(source, transform)

    # Run ACM extraction if enabled
    if cmd.enable_acm_extraction:
        await run_acm_extraction(source)
```

#### ACM Extraction Command

```python
# New command for ACM extraction
@dataclass
class ExtractACMCommand:
    source_id: str
    force_rerun: bool = False

async def handle_extract_acm(cmd: ExtractACMCommand):
    source = await Source.get(cmd.source_id)

    if not cmd.force_rerun:
        existing = await ACMRecord.get_by_source(source.id)
        if existing:
            return {"status": "already_extracted", "count": len(existing)}

    # Delete existing records if re-running
    if cmd.force_rerun:
        await ACMRecord.delete_by_source(source.id)

    # Run extraction
    records = await acm_extraction_transform(source)

    # Save records
    for record in records:
        await record.save()

    return {"status": "success", "count": len(records)}
```

### 2. Frontend Changes

#### Add ACM Toggle to Upload Dialog

Location: `frontend/src/components/sources/AddSourceDialog.tsx`

```tsx
// Add checkbox for ACM extraction
<div className="flex items-center space-x-2">
  <Switch
    id="acm-extraction"
    checked={enableAcmExtraction}
    onCheckedChange={setEnableAcmExtraction}
  />
  <Label htmlFor="acm-extraction">
    Extract ACM Register data (for SAMP documents)
  </Label>
</div>
```

#### Add Re-extract Button to Source Detail

Location: `frontend/src/app/(dashboard)/sources/[id]/page.tsx`

```tsx
// Button to re-run extraction
{hasAcmData && (
  <Button
    variant="outline"
    onClick={() => reExtractAcm(sourceId)}
  >
    <RefreshCw className="w-4 h-4 mr-2" />
    Re-extract ACM Data
  </Button>
)}
```

### 3. Processing Status

#### Status Tracking

Use existing command status tracking:

```python
# In command handler
await update_command_status(
    command_id,
    status="processing",
    message="Extracting ACM data..."
)

# On completion
await update_command_status(
    command_id,
    status="completed",
    message=f"Extracted {len(records)} ACM records"
)
```

#### Frontend Status Display

Reuse existing `CommandProgress` component to show:
- "Extracting ACM data..." during processing
- "Extracted X ACM records" on completion
- Error message on failure

---

## File Changes

| File | Change |
|------|--------|
| `commands/source_commands.py` | Add ACM extraction option |
| `commands/acm_commands.py` | New file for ACM commands |
| `api/routers/acm.py` | Add re-extract endpoint |
| `frontend/.../AddSourceDialog.tsx` | Add ACM toggle |
| `frontend/.../sources/[id]/page.tsx` | Add re-extract button |

---

## Dependencies

- E1-S3: ACM Extraction Transformation (must be complete)
- E1-S4: ACM API Endpoints (must be complete)

---

## Testing

1. Upload a SAMP PDF with ACM toggle enabled
2. Verify extraction runs automatically
3. Check ACM records are created
4. Test re-extraction clears old records
5. Verify error handling for non-ACM documents

---

## Estimated Complexity

**Medium** - Integrates existing components, no new algorithms

---
