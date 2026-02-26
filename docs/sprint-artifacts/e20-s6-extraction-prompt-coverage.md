# Story E20-S6: Extraction Prompt Coverage Enhancement — "As Per" + "Not Sampled" Records

**Epic:** E20 — Extraction Completeness & 100% Record Capture  
**Priority:** P1  
**Status:** drafted  
**Depends on:** E20-S5 (investigation complete)  
**Created:** 2026-02-26 — per E20-S5 investigation findings  

---

## User Story

**As a** developer implementing complete ACM record extraction,  
**I want to** enhance prompt engineering to capture "As Per" reference rows and "Not Sampled" assumed positive rows,  
**So that** the extraction pipeline achieves the target 28/31 (90%) accuracy on the Broadmeadows canonical test document.  

---

## Background

E20-S5 investigation (2026-02-26) revealed that 17/31 accuracy represents the **current model baseline**, not a regression:

### Investigation Findings
- ✅ **Prompt rules ARE present**: E20-S3/E18-S5 fixes intact in `prompts/acm/building_extraction.jinja`
- ✅ **Capable model used**: Anthropic (via OpenRouter) with 17/17 high confidence
- ✅ **Schema blocker resolved**: data_issues null→[] coercion fixed record persistence (0→17)
- ❌ **Gap analysis**: 14 missing records = 9 "As Per" reference + 5 "Not Sampled" rows

### Root Cause
**Existing prompt rules are ineffective under real-world conditions.** While instructions exist (lines 222-239, 247-252), the model fails to follow them consistently when processing complex register tables with mixed record types.

### Missing Record Categories

**Category A — "As Per" Reference Rows (9 rows)**
Items that reuse previously collected samples but appear as separate register entries:
- Corridor Adjacent Cells → "As Per 34511-039-001" (Floor covering)
- Lift Foyer → "As Per 34511-039-001" (Floor covering)
- Throughout → "As Per 34511-039-003" (Skirting)
- Kitchen (2 items) → "As Per 34511-039-009" + "As Per 34511-039-003"
- Fan Room/Roof areas (4 items) → Various "As Per" references

**Category B — "Not Sampled" / Assumed Positive Rows (5 rows)**  
Items identified as likely ACM but not formally tested:
- Front Desk Area → Filing Cabinet (Assumed Positive)
- Switch Room (2x) → Fuse cartridge (Assumed Positive)  
- Boiler Room → Fuse cartridge (Assumed Positive)
- Main Foyer → Unknown (Assumed Positive)

---

## Acceptance Criteria

### AC1 — Prompt Analysis & Re-engineering
- [ ] Analyze why existing prompt rules (lines 247-252, 234-239) are ineffective
- [ ] Research prompt engineering techniques for complex table parsing with mixed record types
- [ ] Consider: explicit examples, chain-of-thought reasoning, structured parsing steps, negative examples

### AC2 — "As Per" Reference Row Enhancement
- [ ] Enhance prompt section 11 (lines 247-252) with concrete examples from Broadmeadows PDF
- [ ] Add negative examples: what NOT to do with "As Per" references
- [ ] Test prompt changes with isolated "As Per" reference extractions
- [ ] Target: capture all 9 "As Per" reference rows as distinct records

### AC3 — "Not Sampled" / Assumed Positive Enhancement  
- [ ] Enhance prompt section 8 (lines 234-239) with specific fuse cartridge/filing cabinet examples
- [ ] Add explicit instruction to extract utility room items even without sample numbers
- [ ] Consider separate prompt section for "Assumed Positive" vs "Not Sampled" terminology
- [ ] Target: capture all 5 "Not Sampled" rows with correct results

### AC4 — Prompt Testing & Validation
- [ ] Create isolated test cases for each missing record category
- [ ] Test prompt changes against Broadmeadows PDF using different models (Anthropic, OpenAI, Qwen2.5:32b)
- [ ] Measure improvement: baseline 17/31 → target ≥28/31 (90%)
- [ ] Document which techniques work best for each model class

### AC5 — Integration & E2E Validation
- [ ] Deploy enhanced prompts to extraction pipeline
- [ ] Re-run E2E validation on Broadmeadows PDF via orchestrator
- [ ] Achieve target: ≥28/31 records (90% accuracy)
- [ ] Log validation results to `docs/sprint-artifacts/e20-s6-validation-results.md`

---

## Technical Approach

### Research Phase
1. **Prompt Engineering Literature Review**
   - Chain-of-thought for complex table parsing
   - Few-shot learning with concrete examples
   - Structured reasoning steps (count → identify → extract)
   - Error analysis and negative examples

2. **Model-Specific Considerations**
   - Anthropic: Responds well to detailed instructions and examples
   - OpenAI: Benefits from structured step-by-step approaches  
   - Qwen: May need more explicit formatting guidance

### Implementation Strategies

**Strategy 1: Concrete Examples**
```jinja
### Example: "As Per" References
Input table row:
| Kitchen | Floor covering | As Per 34511-039-009 | Assumed Positive |

Expected output:
{
  "room_id": "Kitchen", 
  "location": "Floor covering",
  "sample_no": "As Per 34511-039-009",
  "sample_result": "Assumed Positive",
  "product": "Floor covering"
}

DO NOT: Skip this row or merge it with sample 34511-039-009
DO: Extract it as a separate, distinct ACM record
```

**Strategy 2: Parsing Steps**
```jinja
Before extracting, follow these steps:
1. COUNT total table rows (including As Per, Not Sampled, No Access)
2. IDENTIFY record types in each row
3. EXTRACT each row as a separate record
4. VERIFY your output count matches step 1
```

**Strategy 3: Negative Examples**
```jinja
❌ WRONG: Skipping "As Per 34511-039-001" because it references another sample
✅ CORRECT: Extract "As Per 34511-039-001" as its own record with its own location
```

### Testing Framework
```python
# Test individual record categories
def test_as_per_references():
    prompt = load_enhanced_prompt()
    pdf_chunk = extract_as_per_section()
    result = llm.invoke(prompt, pdf_chunk)
    assert count_as_per_records(result) == 9

def test_not_sampled_records():
    prompt = load_enhanced_prompt() 
    pdf_chunk = extract_utility_sections()
    result = llm.invoke(prompt, pdf_chunk)
    assert count_not_sampled_records(result) == 5
```

---

## Success Metrics

| Metric | Baseline | Target | Measurement |
|--------|----------|---------|-------------|
| Total Records | 17/31 (55%) | 28/31 (90%) | E2E extraction count |
| "As Per" Records | 0/9 (0%) | 9/9 (100%) | Reference row extraction |
| "Not Sampled" Records | 0/5 (0%) | 5/5 (100%) | Utility room item extraction |
| Model Consistency | Anthropic only | 3+ models | Cross-model validation |

---

## Technical Notes

### Current Prompt Locations
- **"As Per" rules**: `building_extraction.jinja` lines 247-252
- **"Not Sampled" rules**: `building_extraction.jinja` lines 234-239  
- **Completeness check**: `building_extraction.jinja` line 257

### Investigation Evidence
Per E20-S5 analysis:
- Rules exist but model doesn't follow them consistently
- 17/17 high confidence indicates model understands task structure
- Missing records fall into predictable categories
- No schema or technical blockers remain

### Risk Mitigation
- **Risk**: Enhanced prompts reduce accuracy on other record types
- **Mitigation**: Test against multiple PDF documents, not just Broadmeadows
- **Risk**: Model-specific prompts don't generalize  
- **Mitigation**: Test across Anthropic, OpenAI, Qwen model families

---

## Dev Agent Record

**Created:** 2026-02-26  
**Investigation basis:** E20-S5 gap analysis + prompt rule verification  
**Priority justification**: Epic 20 target completion requires 90% accuracy achievement  

### Dependencies
- E20-S5: DONE (investigation complete, baseline established)
- Prompt templates: `prompts/acm/building_extraction.jinja` 
- Test framework: `tests/test_broadmeadows_e2e.py`

### Implementation Notes
Focus on **prompt engineering**, not code changes. The extraction pipeline infrastructure is complete — this is purely about improving LLM instruction clarity and effectiveness for edge case record types.