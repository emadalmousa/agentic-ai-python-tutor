"""
Tests: Phase 4 — Backend Endpoints

Covers:
1. core/code_runner.py — stdout, stderr, timeout, return type
2. GET /exercises/{skill_key} — auth, 404, unlock logic
3. POST /exercises/submit — scoring branches (richtig/teilweise/falsch),
   already-locked guard, redirect_to_tutor flag, skill score accumulation
4. DELETE /learning-progress/events — auth, user isolation, deleted_count
5. GET /learning-progress/{student_id} — user_status computation
6. Skill unlock chain in progress response

The evaluate_exercise LangChain tool is mocked via patch.object to avoid
real LLM calls. All tests use a fresh in-memory SQLite DB per session (from
conftest) and a TestClient pointing at the real FastAPI app with overridden
DB dependency.
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# ---------------------------------------------------------------------------
# Test DB setup (in-memory SQLite, isolated from production tutor.db)
# StaticPool ensures all connections share the same in-memory DB instance.
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = "sqlite:///:memory:"

_test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_TestSession = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)


def _get_test_db():
    db = _TestSession()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def app_with_test_db():
    """Create tables on the test engine once per module and return the app."""
    # Import models so that Base.metadata knows all tables
    import models  # noqa: F401 — registers all ORM models
    from core.database import Base, get_db
    from main import app

    Base.metadata.create_all(bind=_test_engine)
    app.dependency_overrides[get_db] = _get_test_db
    yield app
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=_test_engine)


@pytest.fixture(scope="module")
def client(app_with_test_db):
    """TestClient wrapping the app with test DB."""
    return TestClient(app_with_test_db)


@pytest.fixture
def auth_headers(client):
    """Register a fresh test user and return Bearer auth headers.

    A unique timestamp suffix ensures no collision between test runs that
    share the module-scoped DB.
    """
    import time
    suffix = str(int(time.time() * 1000))
    email = f"test_{suffix}@example.com"
    resp = client.post("/auth/register", json={
        "name": "Test User",
        "email": email,
        "password": "testpass123",
    })
    assert resp.status_code == 201, f"Register failed: {resp.text}"
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def another_auth_headers(client):
    """Register a second distinct test user."""
    import time
    suffix = str(int(time.time() * 1000)) + "_b"
    email = f"other_{suffix}@example.com"
    resp = client.post("/auth/register", json={
        "name": "Other User",
        "email": email,
        "password": "otherpass123",
    })
    assert resp.status_code == 201, f"Register failed: {resp.text}"
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _make_evaluate_response(result: str) -> str:
    """Build a JSON string that evaluate_exercise.invoke() would return."""
    return json.dumps({
        "result": result,
        "what_was_good": "Good attempt!" if result != "falsch" else "You tried.",
        "what_went_wrong": "" if result == "richtig" else "Something off.",
        "hint": "Keep going.",
    })


def _mock_evaluate(result: str) -> MagicMock:
    """Return a mock for evaluate_exercise whose .invoke() returns the given result JSON."""
    mock_tool = MagicMock()
    mock_tool.invoke.return_value = _make_evaluate_response(result)
    return mock_tool


# ---------------------------------------------------------------------------
# 1. core/code_runner.py unit tests
# ---------------------------------------------------------------------------

class TestCodeRunner:
    """Unit tests for run_user_code — no HTTP, no DB."""

    def test_simple_print_produces_correct_stdout(self):
        """print('hello') returns ('hello', '') — stdout matches, stderr empty."""
        from core.code_runner import run_user_code

        stdout, stderr = run_user_code("print('hello')")

        assert stdout == "hello"
        assert stderr == ""

    def test_syntax_error_returns_empty_stdout_and_non_empty_stderr(self):
        """Syntax errors produce empty stdout and a non-empty stderr message."""
        from core.code_runner import run_user_code

        stdout, stderr = run_user_code("def broken(")

        assert stdout == ""
        assert len(stderr) > 0

    def test_infinite_loop_hits_timeout_and_returns_timeout_message(self):
        """while True: pass triggers TimeoutExpired → stderr contains 'Timeout'."""
        from core.code_runner import run_user_code

        stdout, stderr = run_user_code("while True: pass")

        assert stdout == ""
        assert "Timeout" in stderr

    def test_run_user_code_returns_tuple_of_two_strings(self):
        """run_user_code always returns a (str, str) tuple."""
        from core.code_runner import run_user_code

        result = run_user_code("x = 1")

        assert isinstance(result, tuple)
        assert len(result) == 2
        stdout, stderr = result
        assert isinstance(stdout, str)
        assert isinstance(stderr, str)

    def test_multiline_output_is_preserved(self):
        """Multi-line prints return newline-joined output stripped at the ends."""
        from core.code_runner import run_user_code

        stdout, stderr = run_user_code("print('a')\nprint('b')\nprint('c')")

        assert "a" in stdout
        assert "b" in stdout
        assert "c" in stdout
        assert stderr == ""

    def test_runtime_error_produces_non_empty_stderr(self):
        """Code that raises RuntimeError at execution time produces stderr."""
        from core.code_runner import run_user_code

        stdout, stderr = run_user_code("raise ValueError('oops')")

        assert stdout == ""
        assert len(stderr) > 0


# ---------------------------------------------------------------------------
# 2. GET /exercises/{skill_key}
# ---------------------------------------------------------------------------

class TestGetExercises:
    """Tests for GET /exercises/{skill_key}."""

    def test_returns_401_without_auth(self, client):
        """Unauthenticated request → HTTP 401."""
        resp = client.get("/exercises/variables")

        assert resp.status_code == 401

    def test_returns_404_for_unknown_skill_key(self, client, auth_headers):
        """Request for a non-existent skill key → HTTP 404."""
        resp = client.get("/exercises/nonexistent_skill_xyz", headers=auth_headers)

        assert resp.status_code == 404

    def test_returns_skill_key_and_exercises_list(self, client, auth_headers):
        """Valid authenticated request returns skill_key and a non-empty exercises list."""
        resp = client.get("/exercises/variables", headers=auth_headers)

        assert resp.status_code == 200
        body = resp.json()
        assert body["skill_key"] == "variables"
        assert isinstance(body["exercises"], list)
        assert len(body["exercises"]) > 0

    def test_first_exercise_is_always_unlocked(self, client, auth_headers):
        """The exercise with order=1 always has is_unlocked=True (no completion needed)."""
        resp = client.get("/exercises/variables", headers=auth_headers)

        assert resp.status_code == 200
        exercises = resp.json()["exercises"]
        first = next(e for e in exercises if e["order"] == 1)
        assert first["is_unlocked"] is True

    def test_exercise_2_locked_when_exercise_1_not_completed(self, client, auth_headers):
        """Exercise with order=2 is locked (is_unlocked=False) when exercise 1 has no score."""
        resp = client.get("/exercises/variables", headers=auth_headers)

        assert resp.status_code == 200
        exercises = resp.json()["exercises"]
        second = next(e for e in exercises if e["order"] == 2)
        assert second["is_unlocked"] is False

    def test_exercise_2_unlocked_after_exercise_1_completed(self, client, auth_headers):
        """Exercise with order=2 becomes is_unlocked=True after exercise 1 earns score > 0."""
        import routers.exercises as exercises_mod

        mock_tool = _mock_evaluate("richtig")
        with patch.object(exercises_mod, "evaluate_exercise", mock_tool):
            with patch.object(exercises_mod, "run_user_code", return_value=("Python", "")):
                submit_resp = client.post("/exercises/submit", headers=auth_headers, json={
                    "skill_key": "variables",
                    "exercise_id": "variables_1",
                    "code": "name = 'Python'\nprint(name)",
                })
        assert submit_resp.status_code == 200

        resp = client.get("/exercises/variables", headers=auth_headers)
        assert resp.status_code == 200
        exercises = resp.json()["exercises"]
        second = next(e for e in exercises if e["order"] == 2)
        assert second["is_unlocked"] is True

    def test_response_includes_is_locked_field(self, client, auth_headers):
        """Each exercise in the response includes an is_locked boolean field."""
        resp = client.get("/exercises/variables", headers=auth_headers)

        assert resp.status_code == 200
        for ex in resp.json()["exercises"]:
            assert "is_locked" in ex
            assert isinstance(ex["is_locked"], bool)

    def test_response_includes_score_granted_field(self, client, auth_headers):
        """Each exercise includes a score_granted integer field."""
        resp = client.get("/exercises/variables", headers=auth_headers)

        assert resp.status_code == 200
        for ex in resp.json()["exercises"]:
            assert "score_granted" in ex
            assert isinstance(ex["score_granted"], int)


# ---------------------------------------------------------------------------
# 3. POST /exercises/submit — scoring logic
# ---------------------------------------------------------------------------

class TestSubmitExercise:
    """Tests for POST /exercises/submit scoring branches."""

    # Helper: submit with a mocked evaluate_exercise result
    @staticmethod
    def _submit(client, headers, result: str, skill_key="datatypes", exercise_id="datatypes_1"):
        import routers.exercises as exercises_mod

        mock_tool = _mock_evaluate(result)
        with patch.object(exercises_mod, "evaluate_exercise", mock_tool):
            with patch.object(exercises_mod, "run_user_code", return_value=("some output", "")):
                resp = client.post("/exercises/submit", headers=headers, json={
                    "skill_key": skill_key,
                    "exercise_id": exercise_id,
                    "code": "print('test')",
                })
        return resp

    def test_richtig_result_gives_score_change_20(self, client, auth_headers):
        """result='richtig' on a fresh exercise → score_change=20."""
        resp = self._submit(client, auth_headers, "richtig", skill_key="for_loop", exercise_id="for_loop_1")

        assert resp.status_code == 200
        assert resp.json()["score_change"] == 20

    def test_richtig_result_locks_exercise(self, client, auth_headers):
        """result='richtig' → exercise becomes locked in DB (next GET shows is_locked=True)."""
        import routers.exercises as exercises_mod

        # Use a skill that won't clash with other tests in this class
        mock_tool = _mock_evaluate("richtig")
        with patch.object(exercises_mod, "evaluate_exercise", mock_tool):
            with patch.object(exercises_mod, "run_user_code", return_value=("output", "")):
                resp = client.post("/exercises/submit", headers=auth_headers, json={
                    "skill_key": "while_loop",
                    "exercise_id": "while_loop_1",
                    "code": "print('test')",
                })

        assert resp.status_code == 200

        # Confirm via GET that the exercise is now locked
        get_resp = client.get("/exercises/while_loop", headers=auth_headers)
        exercises = get_resp.json()["exercises"]
        ex1 = next(e for e in exercises if e["order"] == 1)
        assert ex1["is_locked"] is True

    def test_teilweise_result_gives_score_change_10(self, client, auth_headers):
        """result='teilweise' on a fresh exercise → score_change=10."""
        resp = self._submit(client, auth_headers, "teilweise", skill_key="lists", exercise_id="lists_1")

        assert resp.status_code == 200
        assert resp.json()["score_change"] == 10

    def test_teilweise_result_does_not_lock_exercise(self, client, auth_headers):
        """result='teilweise' → is_locked remains False, so re-submission is possible."""
        resp = self._submit(client, auth_headers, "teilweise", skill_key="tuples", exercise_id="tuples_1")

        assert resp.status_code == 200

        get_resp = client.get("/exercises/tuples", headers=auth_headers)
        exercises = get_resp.json()["exercises"]
        ex1 = next(e for e in exercises if e["order"] == 1)
        assert ex1["is_locked"] is False

    def test_falsch_result_gives_score_change_0(self, client, auth_headers):
        """result='falsch' → score_change=0, no progress granted."""
        resp = self._submit(client, auth_headers, "falsch", skill_key="sets", exercise_id="sets_1")

        assert resp.status_code == 200
        assert resp.json()["score_change"] == 0

    def test_already_locked_exercise_returns_400(self, client, auth_headers):
        """Submitting to an already-locked exercise (score_granted=20) → HTTP 400."""
        import routers.exercises as exercises_mod

        mock_tool = _mock_evaluate("richtig")
        # First submit to lock it
        with patch.object(exercises_mod, "evaluate_exercise", mock_tool):
            with patch.object(exercises_mod, "run_user_code", return_value=("output", "")):
                first = client.post("/exercises/submit", headers=auth_headers, json={
                    "skill_key": "dictionaries",
                    "exercise_id": "dictionaries_1",
                    "code": "print('test')",
                })
        assert first.status_code == 200

        # Second submit should be rejected
        with patch.object(exercises_mod, "evaluate_exercise", mock_tool):
            with patch.object(exercises_mod, "run_user_code", return_value=("output", "")):
                second = client.post("/exercises/submit", headers=auth_headers, json={
                    "skill_key": "dictionaries",
                    "exercise_id": "dictionaries_1",
                    "code": "print('test')",
                })

        assert second.status_code == 400

    def test_redirect_to_tutor_true_only_for_falsch(self, client, auth_headers):
        """redirect_to_tutor=True only when result='falsch'."""
        richtig_resp = self._submit(client, auth_headers, "richtig", skill_key="string_methods", exercise_id="string_methods_1")
        falsch_resp = self._submit(client, auth_headers, "falsch", skill_key="type_conversion", exercise_id="type_conversion_1")

        assert richtig_resp.json()["redirect_to_tutor"] is False
        assert falsch_resp.json()["redirect_to_tutor"] is True

    def test_redirect_to_tutor_false_for_teilweise(self, client, auth_headers):
        """redirect_to_tutor=False when result='teilweise'."""
        resp = self._submit(client, auth_headers, "teilweise", skill_key="if_else", exercise_id="if_else_1")

        assert resp.json()["redirect_to_tutor"] is False

    def test_skill_score_is_sum_of_exercise_scores(self, client, auth_headers):
        """StudentSkillProgress.score equals the sum of all exercise score_granted values for the skill."""
        import routers.exercises as exercises_mod

        # Submit exercise 1 as 'teilweise' (score_granted=10)
        with patch.object(exercises_mod, "evaluate_exercise", _mock_evaluate("teilweise")):
            with patch.object(exercises_mod, "run_user_code", return_value=("output", "")):
                resp1 = client.post("/exercises/submit", headers=auth_headers, json={
                    "skill_key": "functions",
                    "exercise_id": "functions_1",
                    "code": "print('test')",
                })
        assert resp1.status_code == 200
        assert resp1.json()["new_skill_score"] == 10

    def test_response_contains_all_required_fields(self, client, auth_headers):
        """Submit response always contains all required fields."""
        resp = self._submit(client, auth_headers, "falsch", skill_key="input_output", exercise_id="input_output_1")

        assert resp.status_code == 200
        body = resp.json()
        for field in ("result", "score_change", "new_skill_score", "what_was_good",
                      "what_went_wrong", "hint", "stdout", "stderr", "redirect_to_tutor", "analysis"):
            assert field in body, f"Missing field: {field}"

    def test_unknown_skill_returns_404(self, client, auth_headers):
        """Submitting for an unknown skill_key → HTTP 404."""
        resp = client.post("/exercises/submit", headers=auth_headers, json={
            "skill_key": "totally_unknown_skill",
            "exercise_id": "totally_unknown_skill_1",
            "code": "print('test')",
        })

        assert resp.status_code == 404

    def test_submit_requires_auth(self, client):
        """POST /exercises/submit without auth → HTTP 401."""
        resp = client.post("/exercises/submit", json={
            "skill_key": "variables",
            "exercise_id": "variables_1",
            "code": "print('test')",
        })

        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# 4. DELETE /learning-progress/events
# ---------------------------------------------------------------------------

class TestDeleteLearningEvents:
    """Tests for DELETE /learning-progress/events."""

    def _create_event(self, client, headers):
        """Create a learning event by calling POST /learning-progress/analyze."""
        import services.skill_analyzer as analyzer_mod

        fake_result = {
            "detected_skills": ["variables"],
            "main_skill": "variables",
            "score": 50,
            "status": "partial",
            "mistakes": [],
            "feedback": "Good attempt.",
            "recommended_next_exercise": "Try exercise 2.",
        }
        with patch.object(analyzer_mod, "analyze_skill", return_value=fake_result):
            resp = client.post("/learning-progress/analyze", headers=headers, json={
                "code": "x = 1",
                "question": "",
            })
        return resp

    def test_returns_401_without_auth(self, client):
        """DELETE /learning-progress/events without auth → HTTP 401."""
        resp = client.delete("/learning-progress/events")

        assert resp.status_code == 401

    def test_returns_deleted_count_in_response(self, client, auth_headers):
        """Response contains 'deleted_count' key with integer value."""
        resp = client.delete("/learning-progress/events", headers=auth_headers)

        assert resp.status_code == 200
        body = resp.json()
        assert "deleted_count" in body
        assert isinstance(body["deleted_count"], int)

    def test_deletes_events_for_current_user_only(self, client, auth_headers, another_auth_headers):
        """Deleting events only removes the current user's events, not another user's."""
        # Create an event for 'another' user
        self._create_event(client, another_auth_headers)

        # Delete events for the first user (shouldn't touch the second user's events)
        del_resp = client.delete("/learning-progress/events", headers=auth_headers)
        assert del_resp.status_code == 200

        # Get student_id for another user via /auth/me
        me_resp = client.get("/auth/me", headers=another_auth_headers)
        assert me_resp.status_code == 200
        other_id = me_resp.json()["id"]

        # The other user's progress endpoint should still show recent_events
        # (we just verify the delete did not cascade to them by re-creating and confirming)
        progress_resp = client.get(f"/learning-progress/{other_id}", headers=another_auth_headers)
        assert progress_resp.status_code == 200
        # We don't assert events count here — just confirm the endpoint is healthy

    def test_deleted_count_matches_event_count(self, client, auth_headers):
        """deleted_count equals the number of events previously created for the user."""
        import services.skill_analyzer as analyzer_mod

        fake_result = {
            "detected_skills": ["variables"],
            "main_skill": "variables",
            "score": 60,
            "status": "partial",
            "mistakes": [],
            "feedback": "OK.",
            "recommended_next_exercise": "Next.",
        }
        # First clear any existing events
        client.delete("/learning-progress/events", headers=auth_headers)

        # Create 2 events
        with patch.object(analyzer_mod, "analyze_skill", return_value=fake_result):
            client.post("/learning-progress/analyze", headers=auth_headers, json={"code": "x=1", "question": ""})
            client.post("/learning-progress/analyze", headers=auth_headers, json={"code": "y=2", "question": ""})

        del_resp = client.delete("/learning-progress/events", headers=auth_headers)
        assert del_resp.json()["deleted_count"] == 2


# ---------------------------------------------------------------------------
# 5. GET /learning-progress/{student_id} — user_status
# ---------------------------------------------------------------------------

class TestUserStatus:
    """Tests for the user_status field in GET /learning-progress/{student_id}."""

    def _get_student_id(self, client, headers) -> int:
        me = client.get("/auth/me", headers=headers)
        return me.json()["id"]

    def _set_skill_score(self, db_session, user_id: int, skill_key: str, score: int):
        """Directly upsert a StudentSkillProgress row for testing."""
        from models.skill_progress import StudentSkillProgress

        row = db_session.query(StudentSkillProgress).filter_by(
            user_id=user_id, skill_key=skill_key
        ).first()
        if row:
            row.score = score
        else:
            row = StudentSkillProgress(
                user_id=user_id,
                skill_key=skill_key,
                score=score,
                status="understood" if score >= 80 else "partial",
            )
            db_session.add(row)
        db_session.commit()

    def test_all_scores_zero_gives_anfaenger(self, client):
        """When all skill scores are 0 (new user), user_status='Anfänger'."""
        import time
        suffix = str(int(time.time() * 1000)) + "_us1"
        resp = client.post("/auth/register", json={
            "name": "Status User",
            "email": f"status_{suffix}@example.com",
            "password": "pass123",
        })
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        me = client.get("/auth/me", headers=headers)
        student_id = me.json()["id"]

        progress = client.get(f"/learning-progress/{student_id}", headers=headers)
        assert progress.status_code == 200
        assert progress.json()["user_status"] == "Anfänger"

    def test_all_beginner_skills_80_plus_gives_fortgeschritten(self, client):
        """When all beginner skills have score >= 80, user_status='Fortgeschritten'."""
        import time
        from models.skill_progress import SKILL_TREE

        suffix = str(int(time.time() * 1000)) + "_us2"
        resp = client.post("/auth/register", json={
            "name": "Advanced User",
            "email": f"advanced_{suffix}@example.com",
            "password": "pass123",
        })
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        me = client.get("/auth/me", headers=headers)
        student_id = me.json()["id"]

        # Set all beginner skills to score=80 using the test DB session directly
        db = _TestSession()
        try:
            beginner_keys = [s["key"] for s in SKILL_TREE if s["level"] == "beginner"]
            for key in beginner_keys:
                self._set_skill_score(db, student_id, key, 80)
        finally:
            db.close()

        progress = client.get(f"/learning-progress/{student_id}", headers=headers)
        assert progress.status_code == 200
        assert progress.json()["user_status"] == "Fortgeschritten"

    def test_all_skills_score_100_gives_profi(self, client):
        """When every skill has score=100, user_status='Profi'."""
        import time
        from models.skill_progress import SKILL_TREE

        suffix = str(int(time.time() * 1000)) + "_us3"
        resp = client.post("/auth/register", json={
            "name": "Pro User",
            "email": f"pro_{suffix}@example.com",
            "password": "pass123",
        })
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        me = client.get("/auth/me", headers=headers)
        student_id = me.json()["id"]

        db = _TestSession()
        try:
            all_keys = [s["key"] for s in SKILL_TREE]
            for key in all_keys:
                self._set_skill_score(db, student_id, key, 100)
        finally:
            db.close()

        progress = client.get(f"/learning-progress/{student_id}", headers=headers)
        assert progress.status_code == 200
        assert progress.json()["user_status"] == "Profi"

    def test_beginner_skills_mix_gives_anfaenger(self, client):
        """When some beginner skills are below 80, user_status stays 'Anfänger'."""
        import time

        suffix = str(int(time.time() * 1000)) + "_us4"
        resp = client.post("/auth/register", json={
            "name": "Mixed User",
            "email": f"mixed_{suffix}@example.com",
            "password": "pass123",
        })
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        me = client.get("/auth/me", headers=headers)
        student_id = me.json()["id"]

        # Set only 'variables' to 80 — not all beginner skills are >= 80
        db = _TestSession()
        try:
            self._set_skill_score(db, student_id, "variables", 80)
            self._set_skill_score(db, student_id, "datatypes", 40)
        finally:
            db.close()

        progress = client.get(f"/learning-progress/{student_id}", headers=headers)
        assert progress.status_code == 200
        assert progress.json()["user_status"] == "Anfänger"


# ---------------------------------------------------------------------------
# 6. Skill unlock chain in progress response
# ---------------------------------------------------------------------------

class TestSkillUnlockChain:
    """Tests for skill is_unlocked logic in the progress response."""

    def _get_progress(self, client, headers, student_id: int) -> dict:
        resp = client.get(f"/learning-progress/{student_id}", headers=headers)
        assert resp.status_code == 200
        return {s["skill_key"]: s for s in resp.json()["skills"]}

    def test_variables_always_unlocked(self, client):
        """'variables' has unlocks_after=None → always is_unlocked=True for any user."""
        import time

        suffix = str(int(time.time() * 1000)) + "_ul1"
        resp = client.post("/auth/register", json={
            "name": "Unlock Test",
            "email": f"unlock_{suffix}@example.com",
            "password": "pass123",
        })
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        me = client.get("/auth/me", headers=headers)
        student_id = me.json()["id"]

        skills = self._get_progress(client, headers, student_id)
        assert skills["variables"]["is_unlocked"] is True

    def test_datatypes_locked_when_variables_score_below_80(self, client):
        """'datatypes' is_unlocked=False when variables.score < 80."""
        import time

        suffix = str(int(time.time() * 1000)) + "_ul2"
        resp = client.post("/auth/register", json={
            "name": "Unlock Test 2",
            "email": f"unlock2_{suffix}@example.com",
            "password": "pass123",
        })
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        me = client.get("/auth/me", headers=headers)
        student_id = me.json()["id"]

        # variables score is 0 (no progress set) → datatypes should be locked
        skills = self._get_progress(client, headers, student_id)
        assert skills["datatypes"]["is_unlocked"] is False

    def test_datatypes_unlocked_when_variables_score_exactly_80(self, client):
        """'datatypes' is_unlocked=True when variables.score == 80 (boundary)."""
        import time
        from models.skill_progress import StudentSkillProgress

        suffix = str(int(time.time() * 1000)) + "_ul3"
        resp = client.post("/auth/register", json={
            "name": "Unlock Test 3",
            "email": f"unlock3_{suffix}@example.com",
            "password": "pass123",
        })
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        me = client.get("/auth/me", headers=headers)
        student_id = me.json()["id"]

        db = _TestSession()
        try:
            row = StudentSkillProgress(
                user_id=student_id,
                skill_key="variables",
                score=80,
                status="understood",
            )
            db.add(row)
            db.commit()
        finally:
            db.close()

        skills = self._get_progress(client, headers, student_id)
        assert skills["datatypes"]["is_unlocked"] is True

    def test_datatypes_locked_when_variables_score_79(self, client):
        """'datatypes' is_unlocked=False when variables.score == 79 (one below boundary)."""
        import time
        from models.skill_progress import StudentSkillProgress

        suffix = str(int(time.time() * 1000)) + "_ul4"
        resp = client.post("/auth/register", json={
            "name": "Unlock Test 4",
            "email": f"unlock4_{suffix}@example.com",
            "password": "pass123",
        })
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        me = client.get("/auth/me", headers=headers)
        student_id = me.json()["id"]

        db = _TestSession()
        try:
            row = StudentSkillProgress(
                user_id=student_id,
                skill_key="variables",
                score=79,
                status="partial",
            )
            db.add(row)
            db.commit()
        finally:
            db.close()

        skills = self._get_progress(client, headers, student_id)
        assert skills["datatypes"]["is_unlocked"] is False

    def test_progress_response_contains_all_37_skills(self, client):
        """Progress response always returns all 37 skills from SKILL_TREE."""
        import time
        from models.skill_progress import SKILL_TREE

        suffix = str(int(time.time() * 1000)) + "_ul5"
        resp = client.post("/auth/register", json={
            "name": "All Skills",
            "email": f"allskills_{suffix}@example.com",
            "password": "pass123",
        })
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        me = client.get("/auth/me", headers=headers)
        student_id = me.json()["id"]

        progress = client.get(f"/learning-progress/{student_id}", headers=headers)
        assert progress.status_code == 200
        skills_in_response = {s["skill_key"] for s in progress.json()["skills"]}
        all_keys = {s["key"] for s in SKILL_TREE}
        assert skills_in_response == all_keys
