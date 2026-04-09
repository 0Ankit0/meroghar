# Phase 2 — Story to Surface Mapping Template

Map each approved story to concrete implementation surfaces.

| Story ID | Backend Module | API Endpoint(s) | Frontend Route/Component | Mobile Screen/Provider | Test Coverage (unit/integration/e2e) |
|---|---|---|---|---|---|
| US-001 | `backend/src/apps/iam/` | `/api/v1/auth/login` | `frontend/src/app/(auth)/login/page.tsx` | `mobile/lib/features/auth/presentation/pages/login_page.dart` |  |

## Notes

- Every P0 story must map to at least one backend endpoint and one client surface.
- If mobile is out of scope for a story, note rationale in this file.
