# Test Failure Analysis - 36 Failed Tests

## Summary
- **Total Tests**: 241
- **Passing**: 184 (81.1%)
- **Failing**: 36
- **Skipped**: 14 (analytics)
- **Errors**: 7

## Failures by Category

### 1. Live Class Interactive (3 failures) 🔴 HIGH
```
tests/api/test_live_class_interactive.py::test_create_poll - FAILED
tests/api/test_live_class_interactive.py::test_get_polls - FAILED
tests/api/test_live_class_interactive.py::test_ask_question - FAILED
```
**Likely Issue**: Missing `/live-class/polls` or `/live-class/questions` endpoints
**Priority**: HIGH - core feature

### 2. WebSocket Tests (3+ failures) 🟡 MEDIUM  
```
app/tests/websocket/test_websocket_manager.py::test_websocket_batching - FAILED
tests/integration/test_websocket.py::TestDiscussionWebSocket::test_websocket_connection_authorized - FAILED
```
**Likely Issue**: WebSocket setup/teardown or connection pooling
**Priority**: MEDIUM - affects real-time features

### 3. Question Banks (4 failures) 🟡 MEDIUM
```
tests/api/test_question_banks.py::test_update_question_bank - FAILED
tests/api/test_question_banks.py::test_delete_question_bank - FAILED
tests/api/test_question_banks.py::test_create_bank_question - FAILED
tests/api/test_question_banks.py::test_generate_quiz_from_banks - FAILED
```
**Likely Issue**: Question bank CRUD operations or quiz generation
**Priority**: MEDIUM - instructor feature

### 4. Email Notifications (1 failure) 🟢 LOW
```
tests/api/test_email_notifications.py::test_update_email_preferences - FAILED
```
**Likely Issue**: Preferences endpoint or model mismatch
**Priority**: LOW - non-critical feature

### 5. Groups/Social (2 failures) 🟡 MEDIUM
```
tests/api/test_groups.py::test_group_stats_calculation - FAILED
tests/api/test_collaborative_projects.py::test_create_team_and_join - FAILED
```
**Likely Issue**: Stats calculation logic or team creation
**Priority**: MEDIUM - social features

### 6. LMS Modules (2 failures) 🔴 HIGH
```
tests/api/test_lms.py::test_update_module - FAILED
tests/api/test_lms.py::test_delete_module - FAILED
```
**Likely Issue**: Module CRUD operations or permissions
**Priority**: HIGH - core LMS functionality

### 7. Integration Tests (7+ failures) ⚠️ ERRORS
```
tests/integration/* - Various errors
```
**Likely Issue**: Test setup/teardown, database state, or async issues
**Priority**: MEDIUM - test infrastructure

---

## Recommended Fix Order

### Phase 1: Quick Wins (Fix ~15 tests)
1. **LMS Module CRUD** - Fix update/delete operations
2. **Email Preferences** - Fix single endpoint
3. **Question Bank CRUD** - Fix 4 related endpoints

### Phase 2: Feature Completion (Fix ~10 tests)
4. **Live Class Interactive** - Implement polls/questions endpoints
5. **Groups Stats** - Fix stats calculation
6. **Collaborative Projects** - Fix team creation

### Phase 3: Infrastructure (Fix ~11 tests)
7. **WebSocket Tests** - Fix async test setup
8. **Integration Tests** - Fix test infrastructure issues

---

## Expected Impact
- **Current**: 184/227 passed = 81.1%
- **After Phase 1**: ~199/227 = **87.7%** (+6.6%)
- **After Phase 2**: ~209/227 = **92.1%** (+4.4%)
- **After Phase 3**: ~220/227 = **97.0%** (+4.9%)

---

## Next Steps
1. Start with LMS module fixes (highest ROI)
2. Run tests after each phase
3. Document remaining failures
4. Consider skipping flaky integration tests
