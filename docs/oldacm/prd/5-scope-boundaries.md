# 5. Scope Boundaries

## Out of Scope
- Cloud-hosted AI inference for OCR, embeddings, or chat (external third‑party APIs). All AI must run locally per NFRs.
- Payment/billing, subscriptions, or licensing management.
- Mobile apps (iOS/Android) – web only for this phase.
- Non-asbestos/general document types beyond the target regulatory documents for this phase (focus: Asbestos Registers/SSAMPs and related regulatory templates).
- Fine-tuning or training custom foundation models; only configuration and optimization of local models are in scope.
- Multi-tenant admin consoles, RBAC beyond basic authenticated user access.
- Advanced analytics/BI dashboards (beyond basic processing metrics and audit trails).

## MVP Validation Plan
- Document upload and storage
  - 95%+ success rate for uploads up to 50MB across PDF/PNG/JPG/TIFF
  - Progress, cancel, and error states behave per UX spec
- OCR quality (Tesseract 5.x)
  - Average word confidence ≥ 70% on benchmark set of target reports
  - Word-level bounding boxes normalized to 0–1000 scale with ≤ 3% positional error
  - Multi-language: English baseline; spot checks for FR/ES/DE
- Preprocessing pipeline
  - Deskew + denoise improves OCR confidence by ≥ 10pp on skewed/noisy samples
  - 300 DPI PDF conversion within memory/time thresholds on minimum-spec hardware
- Layout understanding (LayoutLMv3)
  - Entity extraction F1 ≥ 0.75 on internal test set for key fields used to populate ACM Register
  - Throughput target: ≥ 1 page/sec on baseline CPU; ≥ 3 pages/sec with GPU (where available)
- Provenance viewer
  - 100% of structured fields in ACM Register link back to a valid page + bounding box
  - Click-through latency ≤ 300ms for cached pages
- Conversational chat
  - Document-grounded answers with citation links to page/bbox in ≥ 90% of QA test prompts
  - First token latency ≤ 2s on minimum-spec hardware; streaming responses
- Exports
  - Successful generation of Bar Replacement and ACM Register exports matching template schema
  - Round-trip validation: values in exports match provenance-linked sources
- Security & privacy
  - No document content sent to external APIs during normal operation
  - RLS policies prevent cross-user data access in Supabase
