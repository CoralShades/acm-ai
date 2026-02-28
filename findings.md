# Findings — E27-S2: Browser Verification

## What to Verify
1. Navigate to extraction page: `/jobs/{source_id}/extract`
2. Start an extraction (or observe in-progress one)
3. ExtractionProgressPanel should show 9 stage pills (was 7)
4. New stages visible: "Docling Tables" (with TableProperties icon) and "Recovery Scan" (with Search icon)
5. Stage pills light up teal when running, emerald when complete

## Frontend Architecture for Verification
- Extract page: `frontend/src/app/(dashboard)/jobs/[id]/extract/page.tsx`
- Progress panel: `frontend/src/components/acm/ExtractionProgressPanel.tsx`
- Stage pills: `frontend/src/components/acm/StageProgressPill.tsx`
- SSE hook: `frontend/src/lib/hooks/use-extraction-progress.ts`

## Services Required
- SurrealDB on port 8000 (Docker)
- API on port 5055 (uvicorn)
- Frontend on port 8502 (Next.js dev)
- Worker (background, for extraction commands)

## Test Sources
- Any uploaded PDF source with a command_id can be used
- Broadmeadows or Alexandra test PDFs in docs/samplePDF/

## Note on Docling Stage Timing
- DOCLING_EXTRACTION runs during SOURCE PROCESSING (before the extraction graph)
- Its events go to a separate PipelineLogger instance
- The extraction graph's PipelineRunState won't include the Docling stage
- To see Docling stage in the progress panel, the frontend would need to merge two PipelineRunState objects
- For this verification, focus on: NO_ACCESS_RECOVERY stage appearing in the extraction graph run
