"""
Tests: Phase 2 — Exercise Data Integrity

Validates:
- EXERCISES dict has exactly 13 keys (all beginner skills)
- Every skill has exactly 5 exercises (total = 65)
- Every exercise has all required fields with non-empty values
- All exercise IDs are unique and match the "{skill_key}_{order}" pattern
- Each skill's exercises are ordered 1-5 with no gaps or duplicates
- exercise["skill_key"] matches the dict key it is stored under
- No description or expected_output contains "input(" (would block subprocess)
- All hints are non-empty strings under 150 characters
- All 13 beginner skills from SKILL_TREE are covered; no non-beginner skills present

No DB connection required — all tests inspect module-level data only.
"""

import re

import pytest


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

REQUIRED_FIELDS = {"id", "skill_key", "order", "title", "description", "expected_output",
                   "test_type", "hint"}

EXPECTED_SKILL_COUNT = 13
EXERCISES_PER_SKILL = 5
TOTAL_EXERCISES = EXPECTED_SKILL_COUNT * EXERCISES_PER_SKILL  # 65


def _all_exercises(exercises: dict) -> list[dict]:
    """Flatten EXERCISES dict into a single list of all exercise dicts."""
    return [ex for exlist in exercises.values() for ex in exlist]


def _beginner_keys() -> list[str]:
    """Return the ordered list of beginner skill keys from SKILL_TREE."""
    from models.skill_progress import SKILL_TREE
    return [s["key"] for s in SKILL_TREE if s["level"] == "beginner"]


# ---------------------------------------------------------------------------
# 1. Structure tests
# ---------------------------------------------------------------------------


class TestExercisesStructure:
    def test_every_skill_has_exactly_5_exercises(self):
        """Each skill in EXERCISES must have exactly 5 exercises."""
        from data.exercises import EXERCISES

        for skill_key, exlist in EXERCISES.items():
            assert len(exlist) == EXERCISES_PER_SKILL, (
                f"Skill '{skill_key}' has {len(exlist)} exercises, expected {EXERCISES_PER_SKILL}"
            )

    def test_exercises_dict_values_are_lists(self):
        """Each EXERCISES value must be a list."""
        from data.exercises import EXERCISES

        for skill_key, exlist in EXERCISES.items():
            assert isinstance(exlist, list), (
                f"EXERCISES['{skill_key}'] is {type(exlist).__name__}, expected list"
            )

    def test_each_exercise_is_a_dict(self):
        """Every exercise entry must be a dict."""
        from data.exercises import EXERCISES

        for skill_key, exlist in EXERCISES.items():
            for i, ex in enumerate(exlist):
                assert isinstance(ex, dict), (
                    f"EXERCISES['{skill_key}'][{i}] is {type(ex).__name__}, expected dict"
                )


# ---------------------------------------------------------------------------
# 2. Field completeness
# ---------------------------------------------------------------------------


class TestFieldCompleteness:
    def test_every_exercise_has_all_required_fields(self):
        """Every exercise must contain all required fields."""
        from data.exercises import EXERCISES

        for skill_key, exlist in EXERCISES.items():
            for ex in exlist:
                missing = REQUIRED_FIELDS - set(ex.keys())
                assert not missing, (
                    f"Exercise '{ex.get('id', '?')}' in skill '{skill_key}' "
                    f"is missing fields: {missing}"
                )

    def test_no_field_is_none(self):
        """No required field value may be None."""
        from data.exercises import EXERCISES

        for skill_key, exlist in EXERCISES.items():
            for ex in exlist:
                for field in REQUIRED_FIELDS:
                    assert ex.get(field) is not None, (
                        f"Exercise '{ex.get('id', '?')}' field '{field}' is None"
                    )

    def test_no_field_is_empty_string(self):
        """No required field value may be an empty string."""
        from data.exercises import EXERCISES

        for skill_key, exlist in EXERCISES.items():
            for ex in exlist:
                for field in REQUIRED_FIELDS:
                    value = ex.get(field)
                    if isinstance(value, str):
                        assert value != "", (
                            f"Exercise '{ex.get('id', '?')}' field '{field}' is empty string"
                        )

    def test_all_string_fields_are_strings(self):
        """String fields (id, skill_key, title, description, expected_output, test_type, hint)
        must all be str instances."""
        from data.exercises import EXERCISES

        string_fields = {"id", "skill_key", "title", "description",
                         "expected_output", "test_type", "hint"}
        for skill_key, exlist in EXERCISES.items():
            for ex in exlist:
                for field in string_fields:
                    value = ex.get(field)
                    assert isinstance(value, str), (
                        f"Exercise '{ex.get('id', '?')}' field '{field}' "
                        f"is {type(value).__name__}, expected str"
                    )

    def test_order_field_is_integer(self):
        """The 'order' field must be an int in every exercise."""
        from data.exercises import EXERCISES

        for skill_key, exlist in EXERCISES.items():
            for ex in exlist:
                assert isinstance(ex.get("order"), int), (
                    f"Exercise '{ex.get('id', '?')}' has non-int order: "
                    f"{ex.get('order')!r}"
                )


# ---------------------------------------------------------------------------
# 3. ID uniqueness and format
# ---------------------------------------------------------------------------


class TestExerciseIds:
    def test_all_exercise_ids_are_unique(self):
        """All 65 exercise IDs must be globally unique."""
        from data.exercises import EXERCISES

        all_ids = [ex["id"] for ex in _all_exercises(EXERCISES)]
        duplicates = [eid for eid in all_ids if all_ids.count(eid) > 1]
        assert not duplicates, (
            f"Duplicate exercise IDs found: {sorted(set(duplicates))}"
        )

    def test_exercise_id_matches_skill_key_order_pattern(self):
        """Every ID must match the pattern '{skill_key}_{order}'."""
        from data.exercises import EXERCISES

        for skill_key, exlist in EXERCISES.items():
            for ex in exlist:
                expected_id = f"{skill_key}_{ex['order']}"
                assert ex["id"] == expected_id, (
                    f"Exercise in '{skill_key}' order {ex['order']} has id='{ex['id']}', "
                    f"expected '{expected_id}'"
                )

    def test_exercise_id_format_regex(self):
        """Every exercise ID must match the regex pattern: word_chars followed by underscore
        and a digit 1-5."""
        from data.exercises import EXERCISES

        pattern = re.compile(r"^[a-z_]+_[1-5]$")
        for ex in _all_exercises(EXERCISES):
            assert pattern.match(ex["id"]), (
                f"Exercise ID '{ex['id']}' does not match expected pattern "
                f"'<skill_key>_<1-5>'"
            )


# ---------------------------------------------------------------------------
# 4. Order integrity
# ---------------------------------------------------------------------------


class TestOrderIntegrity:
    def test_each_skill_has_orders_1_through_5(self):
        """Each skill must have exercises with orders exactly {1, 2, 3, 4, 5}."""
        from data.exercises import EXERCISES

        for skill_key, exlist in EXERCISES.items():
            orders = {ex["order"] for ex in exlist}
            assert orders == {1, 2, 3, 4, 5}, (
                f"Skill '{skill_key}' has order set {sorted(orders)}, "
                f"expected {{1, 2, 3, 4, 5}}"
            )

    def test_no_duplicate_orders_within_skill(self):
        """No two exercises within the same skill may share the same order value."""
        from data.exercises import EXERCISES

        for skill_key, exlist in EXERCISES.items():
            orders = [ex["order"] for ex in exlist]
            duplicates = [o for o in orders if orders.count(o) > 1]
            assert not duplicates, (
                f"Skill '{skill_key}' has duplicate order values: {sorted(set(duplicates))}"
            )

    @pytest.mark.parametrize("order", [1, 2, 3, 4, 5])
    def test_every_skill_has_exercise_at_each_order(self, order: int):
        """Every skill must have exactly one exercise at each order from 1 to 5."""
        from data.exercises import EXERCISES

        for skill_key, exlist in EXERCISES.items():
            orders_present = [ex["order"] for ex in exlist]
            assert order in orders_present, (
                f"Skill '{skill_key}' is missing an exercise at order {order}"
            )


# ---------------------------------------------------------------------------
# 5. skill_key consistency
# ---------------------------------------------------------------------------


class TestSkillKeyConsistency:
    def test_exercise_skill_key_matches_dict_key(self):
        """exercise['skill_key'] must equal the dict key it is stored under."""
        from data.exercises import EXERCISES

        for skill_key, exlist in EXERCISES.items():
            for ex in exlist:
                assert ex["skill_key"] == skill_key, (
                    f"Exercise '{ex['id']}' has skill_key='{ex['skill_key']}' "
                    f"but is stored under key '{skill_key}'"
                )


# ---------------------------------------------------------------------------
# 6. No input() calls
# ---------------------------------------------------------------------------


class TestNoInputCalls:
    def test_description_contains_no_input_call(self):
        """No exercise description may contain 'input(' — would block subprocess execution."""
        from data.exercises import EXERCISES

        for ex in _all_exercises(EXERCISES):
            assert "input(" not in ex["description"], (
                f"Exercise '{ex['id']}' description contains 'input(' which would "
                f"block automated subprocess execution"
            )

    def test_expected_output_contains_no_input_call(self):
        """No exercise expected_output may contain 'input('."""
        from data.exercises import EXERCISES

        for ex in _all_exercises(EXERCISES):
            assert "input(" not in ex["expected_output"], (
                f"Exercise '{ex['id']}' expected_output contains 'input('"
            )


# ---------------------------------------------------------------------------
# 7. Hint field quality
# ---------------------------------------------------------------------------


class TestHintFieldQuality:
    def test_all_hints_are_non_empty(self):
        """Every hint must be a non-empty string."""
        from data.exercises import EXERCISES

        for ex in _all_exercises(EXERCISES):
            hint = ex.get("hint", "")
            assert isinstance(hint, str) and hint.strip() != "", (
                f"Exercise '{ex['id']}' has an empty or whitespace-only hint"
            )

    def test_all_hints_under_150_characters(self):
        """Every hint must be under 150 characters."""
        from data.exercises import EXERCISES

        for ex in _all_exercises(EXERCISES):
            hint = ex["hint"]
            assert len(hint) < 150, (
                f"Exercise '{ex['id']}' hint is {len(hint)} characters, "
                f"exceeds 150-character limit. Hint: '{hint}'"
            )


# ---------------------------------------------------------------------------
# 8. Beginner skills coverage
# ---------------------------------------------------------------------------


class TestBeginnerSkillsCoverage:
    def test_all_13_beginner_skills_are_present(self):
        """All 13 beginner skill keys from SKILL_TREE must appear as keys in EXERCISES."""
        from data.exercises import EXERCISES

        beginner_keys = set(_beginner_keys())
        exercises_keys = set(EXERCISES.keys())
        missing = beginner_keys - exercises_keys
        assert not missing, (
            f"Beginner skills missing from EXERCISES: {sorted(missing)}"
        )

    @pytest.mark.parametrize("skill_key", [
        "variables", "datatypes", "input_output", "string_methods", "type_conversion",
        "if_else", "for_loop", "while_loop", "lists", "tuples", "sets",
        "dictionaries", "functions",
    ])
    def test_each_beginner_skill_individually_present(self, skill_key: str):
        """Each of the 13 beginner skills must individually be a key in EXERCISES."""
        from data.exercises import EXERCISES

        assert skill_key in EXERCISES, (
            f"Beginner skill '{skill_key}' not found as a key in EXERCISES"
        )
