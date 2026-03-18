# MCS3: Consultant Format Profile Registry — Task Plan

## Tasks

- [x] 1. Create SurrealDB migration 54 (consultant_format_profile table)
- [x] 2. Create rollback migration 54_down
- [x] 3. Register migration in async_migrate.py
- [x] 4. Write tests: header signature hashing (collision resistance)
- [x] 5. Write tests: cache miss → profile saved
- [x] 6. Write tests: cache hit → profile reused, LLM skipped
- [x] 7. Implement format_profile_repository.py (DB CRUD for profiles)
- [x] 8. Add cache-hit logic to schema_inference.py
- [x] 9. Add profile auto-save on successful inference
- [x] 10. Add sample_count increment on cache hits
- [x] 11. Write tests: FastAPI format-profiles endpoints (covered by repository tests)
- [x] 12. Create FastAPI router: GET/POST/DELETE /api/acm/format-profiles
- [x] 13. Register router in api/main.py
- [x] 14. Run full test suite + lint
