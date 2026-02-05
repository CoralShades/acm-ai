# Story 1.8: Site Configuration Data Entry

**Status:** ready-for-dev
**Created:** 2026-02-05
**Epic:** E1 - ACM Data Extraction Pipeline
**Priority:** P0 (Victorian BAR Compliance)

## Story

**As a** user uploading ACM assessment documents,
**I want** to configure site metadata that cannot be extracted from PDFs (Department, Agency, Building Type, etc.),
**So that** my BAR exports are complete with all required Victorian Government fields and comply with submission requirements.

## Context

### Problem
Victorian Government BAR (Building Asbestos Register) exports require ~47 columns of data. Some fields cannot be extracted from consultant PDFs because they represent organizational/administrative metadata that isn't present in assessment reports:
- Department (DJCS, DHHS, DET, etc.)
- Agency (Victoria Police, District Health, etc.)
- Building Type (Police Station, Hospital, School, etc.)
- Owned or Leased
- Frequency of Use
- Public Access (YES/NO)
- Building Unique ID

Currently, users cannot populate these fields, resulting in incomplete BAR exports.

### Solution
Create a Site Configuration feature that:
1. Provides a form UI for entering non-extractable metadata per source document
2. Stores configuration in a dedicated `site_config` table
3. Applies configuration to ACM records during BAR export
4. Supports templates for batch uploads of similar documents

### Dependencies
- **Depends on:** E1-S4 (ACM API Endpoints) - ✅ COMPLETE
- **Blocks:** E7-S7 (Site Configuration During Upload)

## Acceptance Criteria

### AC1: Site Configuration Form Component
- **Given:** A source document with ACM records
- **When:** User opens the site configuration panel
- **Then:** A form displays with fields for:
  - Department (dropdown: DJCS, DHHS, DET, DOT, DJPR, Other)
  - Agency (text input with autocomplete from previous entries)
  - Building Type (dropdown: Police Station, Hospital, School, Office, Residential, Industrial, Other)
  - Owned or Leased (dropdown: Owned, Leased)
  - Frequency of Use (dropdown: Every day, Every day with intermittent breaks, Once every 3-5 days, Every 2-3 weeks, Once every 2-3 months, Annually or less frequently)
  - Public Access (dropdown: YES, NO)
  - Building Unique ID (text input)

### AC2: Configuration Persistence
- **Given:** User fills out site configuration form
- **When:** User clicks Save
- **Then:** Configuration is saved to `site_config` table with `source_id` reference
- **And:** Success feedback is shown to user
- **And:** Form shows saved values on subsequent loads

### AC3: Edit Existing Configuration
- **Given:** A source document with existing site configuration
- **When:** User opens the site configuration panel
- **Then:** Form is pre-populated with saved values
- **And:** User can modify and save changes

### AC4: Configuration Template Support
- **Given:** User is configuring a new source document
- **When:** Similar documents have been configured before
- **Then:** User can apply a template from a previous configuration
- **And:** Template values populate the form (user can modify before saving)

### AC5: Validation Warnings
- **Given:** User is viewing site configuration
- **When:** Required BAR fields are empty
- **Then:** Visual warning indicators show which fields are missing
- **And:** Warning doesn't block save (fields are optional but recommended)

### AC6: API Endpoints
- **Given:** Frontend needs to manage site configuration
- **When:** API calls are made
- **Then:** Following endpoints are available:
  - `GET /api/acm/config?source_id=xxx` - Get config for source
  - `POST /api/acm/config` - Create/update config
  - `GET /api/acm/config/templates` - List available templates
  - `POST /api/acm/config/apply-template` - Apply template to source

## Tasks / Subtasks

### Phase 1: Database Schema & Domain Model

- [ ] **Task 1.1: Create site_config migration** (AC: 2)
  - [ ] Create migration file `migrations/XX.surrealql` for site_config table
  - [ ] Define all fields per PRD 5.1.1 schema
  - [ ] Add indexes for source_id lookup
  - [ ] Create down migration for rollback
  - **Files:** `migrations/XX.surrealql`, `migrations/XX_down.surrealql`

- [ ] **Task 1.2: Create SiteConfig domain model** (AC: 2, 3)
  - [ ] Create `open_notebook/domain/site_config.py`
  - [ ] Extend ObjectModel base class
  - [ ] Implement CRUD operations (get_by_source, save, delete)
  - [ ] Add validators for enum fields
  - **Files:** `open_notebook/domain/site_config.py`

### Phase 2: Backend API

- [ ] **Task 2.1: Create API models** (AC: 6)
  - [ ] Add `SiteConfigRequest` model to `api/models.py`
  - [ ] Add `SiteConfigResponse` model
  - [ ] Add `SiteConfigTemplateResponse` model
  - [ ] Add `ApplyTemplateRequest` model
  - **Files:** `api/models.py`

- [ ] **Task 2.2: Implement config endpoints in acm.py** (AC: 6)
  - [ ] `GET /api/acm/config` - Get config by source_id
  - [ ] `POST /api/acm/config` - Create or update config
  - [ ] Handle upsert logic (create if not exists, update if exists)
  - **Files:** `api/routers/acm.py`

- [ ] **Task 2.3: Implement template endpoints** (AC: 4, 6)
  - [ ] `GET /api/acm/config/templates` - List distinct configs as templates
  - [ ] `POST /api/acm/config/apply-template` - Copy config from template source
  - [ ] Template listing should group by similar department/agency combinations
  - **Files:** `api/routers/acm.py`

### Phase 3: Frontend Components

- [ ] **Task 3.1: Create SiteConfigForm component** (AC: 1, 5)
  - [ ] Create `frontend/src/components/acm/SiteConfigForm.tsx`
  - [ ] Use React Hook Form + Zod for validation
  - [ ] Implement dropdown fields with enum options
  - [ ] Add autocomplete for Agency field (fetch from existing configs)
  - [ ] Show validation warnings for empty BAR-required fields
  - **Files:** `frontend/src/components/acm/SiteConfigForm.tsx`

- [ ] **Task 3.2: Create API hooks** (AC: 2, 3, 4)
  - [ ] Create `frontend/src/hooks/useSiteConfig.ts`
  - [ ] `useSiteConfig(sourceId)` - Fetch config for source
  - [ ] `useSaveSiteConfig()` - Mutation for saving
  - [ ] `useSiteConfigTemplates()` - Fetch available templates
  - [ ] `useApplyTemplate()` - Apply template mutation
  - **Files:** `frontend/src/hooks/useSiteConfig.ts`, `frontend/src/lib/api/acm.ts`

- [ ] **Task 3.3: Create SiteConfigPanel component** (AC: 1, 4, 5)
  - [ ] Create `frontend/src/components/acm/SiteConfigPanel.tsx`
  - [ ] Wrapper with header, template selector, and form
  - [ ] Template dropdown with "Apply" button
  - [ ] Loading/error states
  - [ ] Success/failure toast notifications
  - **Files:** `frontend/src/components/acm/SiteConfigPanel.tsx`

- [ ] **Task 3.4: Integrate into ACM view** (AC: 1)
  - [ ] Add "Site Config" button/tab to ACMToolbar or source detail page
  - [ ] Open SiteConfigPanel in modal or side panel
  - [ ] Update existing ACM components to show config status indicator
  - **Files:** `frontend/src/components/acm/ACMToolbar.tsx` or source page

### Phase 4: Testing

- [ ] **Task 4.1: Backend unit tests** (AC: 2, 3, 6)
  - [ ] Test SiteConfig domain model CRUD
  - [ ] Test API endpoints (create, read, update)
  - [ ] Test template listing and application
  - [ ] Test validation of enum fields
  - **Files:** `tests/test_site_config.py`, `tests/test_acm_api.py`

- [ ] **Task 4.2: Frontend component tests** (AC: 1, 5)
  - [ ] Test SiteConfigForm renders all fields
  - [ ] Test form validation
  - [ ] Test template selection
  - [ ] Test save/load flow
  - **Files:** `frontend/src/components/acm/__tests__/SiteConfigForm.test.tsx`

## Dev Notes

### Architecture Patterns to Follow

**Backend:**
- Follow existing `ACMRecord` domain model pattern in `open_notebook/domain/acm.py`
- Use `ObjectModel` base class for SiteConfig
- Add endpoints to existing `api/routers/acm.py` (don't create new router)
- Use `repo_query` for database operations

**Frontend:**
- Follow existing component patterns in `frontend/src/components/acm/`
- Use React Query hooks pattern from `frontend/src/hooks/`
- Use Radix UI components (already in project)
- Use React Hook Form + Zod for forms (project standard)
- Use `toast` from sonner for notifications

### Enum Values (from PRD 5.5)

```typescript
// Department options
const DEPARTMENTS = [
  "DJCS",  // Department of Justice and Community Safety
  "DHHS",  // Department of Health and Human Services
  "DET",   // Department of Education and Training
  "DOT",   // Department of Transport
  "DJPR",  // Department of Jobs, Precincts and Regions
  "Other"
];

// Building Type options
const BUILDING_TYPES = [
  "Police Station",
  "Hospital",
  "School",
  "Office",
  "Residential",
  "Industrial",
  "Other"
];

// Frequency of Use options (BAR exact wording)
const FREQUENCY_OPTIONS = [
  "Every day",
  "Every day with intermittent breaks",
  "Once every 3-5 days",
  "Every 2-3 weeks",
  "Once every 2-3 months",
  "Annually or less frequently"
];

// Owned or Leased
const OWNERSHIP_OPTIONS = ["Owned", "Leased"];

// Public Access
const PUBLIC_ACCESS_OPTIONS = ["YES", "NO"];
```

### Database Schema

```sql
-- From PRD 5.1.1
DEFINE TABLE site_config SCHEMAFULL;
DEFINE FIELD source_id ON site_config TYPE record<source>;
DEFINE FIELD department ON site_config TYPE option<string>;
DEFINE FIELD agency ON site_config TYPE option<string>;
DEFINE FIELD building_type ON site_config TYPE option<string>;
DEFINE FIELD owned_or_leased ON site_config TYPE option<string>;
DEFINE FIELD frequency_of_use ON site_config TYPE option<string>;
DEFINE FIELD public_access ON site_config TYPE option<string>;
DEFINE FIELD building_unique_id ON site_config TYPE option<string>;
DEFINE FIELD created_at ON site_config TYPE datetime DEFAULT time::now();
DEFINE FIELD updated_at ON site_config TYPE datetime DEFAULT time::now();

DEFINE INDEX config_source ON site_config FIELDS source_id UNIQUE;
```

**Note:** Index is UNIQUE because there should be one config per source.

### API Response Models

```python
# Add to api/models.py
class SiteConfigRequest(BaseModel):
    source_id: str
    department: Optional[str] = None
    agency: Optional[str] = None
    building_type: Optional[str] = None
    owned_or_leased: Optional[str] = None
    frequency_of_use: Optional[str] = None
    public_access: Optional[str] = None
    building_unique_id: Optional[str] = None

class SiteConfigResponse(BaseModel):
    id: Optional[str] = None
    source_id: str
    department: Optional[str] = None
    agency: Optional[str] = None
    building_type: Optional[str] = None
    owned_or_leased: Optional[str] = None
    frequency_of_use: Optional[str] = None
    public_access: Optional[str] = None
    building_unique_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class SiteConfigTemplateResponse(BaseModel):
    source_id: str
    source_title: str
    department: Optional[str] = None
    agency: Optional[str] = None
```

### Project Structure Notes

**New Files to Create:**
- `migrations/XX.surrealql` - Database schema (check existing migrations for next number)
- `open_notebook/domain/site_config.py` - Domain model
- `frontend/src/components/acm/SiteConfigForm.tsx` - Form component
- `frontend/src/components/acm/SiteConfigPanel.tsx` - Panel wrapper
- `frontend/src/hooks/useSiteConfig.ts` - React Query hooks
- `tests/test_site_config.py` - Backend tests

**Files to Modify:**
- `api/models.py` - Add request/response models
- `api/routers/acm.py` - Add config endpoints
- `frontend/src/lib/api/acm.ts` - Add API client functions
- `frontend/src/components/acm/ACMToolbar.tsx` - Add config button (or source page)

### Testing Standards

- Use pytest for backend tests
- Use React Testing Library for frontend
- Test happy path and edge cases
- Mock API calls in frontend tests

### References

- [PRD Section 5.1.1](file://_bmad-output/project-planning-artifacts/acm-ai/03-prd.md#511-site-configuration-schema-new) - Site Configuration Schema
- [Architecture Section 3.1](file://_bmad-output/project-planning-artifacts/acm-ai/04-architecture.md#31-surrealdb-tables-victorian-bar-format---expanded) - Database Schema
- [Epic E1-S8](file://_bmad-output/project-planning-artifacts/acm-ai/05-epics-and-stories.md#e1-s8-site-configuration-data-entry-new---victorian-bar) - Story Definition
- [Sprint Change Proposal CP#2](file://_bmad-output/sprint-change-proposal-20260204.md) - Victorian BAR Expansion

## Dev Agent Record

### Agent Model Used
(To be filled during implementation)

### Debug Log References
(To be filled during implementation)

### Completion Notes List
(To be filled during implementation)

### File List
(To be filled during implementation)
