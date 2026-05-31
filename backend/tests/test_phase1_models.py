"""
Tests: Phase 1 — DB Models and Skill Tree Integrity

Validates:
- SKILL_TREE has exactly 37 entries with correct level distribution
- No duplicate skill keys in SKILL_TREE
- Every unlocks_after references a valid key or is None
- Only level-first skills have unlocks_after=None
- FIXED_SKILLS backward-compatibility alias works correctly
- ExerciseCompletion model has all required columns with correct defaults
- SkillTestResult model has all required columns with correct defaults
- skill_analyzer.VALID_SKILLS contains all 37 SKILL_TREE keys

No DB connection required — all tests inspect model structure and module-level data.
"""

import pytest


# ---------------------------------------------------------------------------
# SKILL_TREE data integrity
# ---------------------------------------------------------------------------


class TestSkillTreeCount:
    def test_skill_tree_has_37_entries(self):
        """SKILL_TREE must contain exactly 37 skills."""
        from models.skill_progress import SKILL_TREE

        assert len(SKILL_TREE) == 37

    def test_skill_tree_has_13_beginner_skills(self):
        """SKILL_TREE must contain exactly 13 beginner skills."""
        from models.skill_progress import SKILL_TREE

        beginner = [s for s in SKILL_TREE if s["level"] == "beginner"]
        assert len(beginner) == 13

    def test_skill_tree_has_12_intermediate_skills(self):
        """SKILL_TREE must contain exactly 12 intermediate skills."""
        from models.skill_progress import SKILL_TREE

        intermediate = [s for s in SKILL_TREE if s["level"] == "intermediate"]
        assert len(intermediate) == 12

    def test_skill_tree_has_12_advanced_skills(self):
        """SKILL_TREE must contain exactly 12 advanced skills."""
        from models.skill_progress import SKILL_TREE

        advanced = [s for s in SKILL_TREE if s["level"] == "advanced"]
        assert len(advanced) == 12


class TestSkillTreeKeys:
    def test_no_duplicate_skill_keys(self):
        """Each skill key must be unique across SKILL_TREE."""
        from models.skill_progress import SKILL_TREE

        keys = [s["key"] for s in SKILL_TREE]
        assert len(keys) == len(set(keys)), (
            f"Duplicate keys found: {[k for k in keys if keys.count(k) > 1]}"
        )

    def test_every_entry_has_required_keys(self):
        """Every SKILL_TREE entry must have all five required fields."""
        from models.skill_progress import SKILL_TREE

        required_fields = {"key", "label", "level", "order", "unlocks_after"}
        for skill in SKILL_TREE:
            missing = required_fields - set(skill.keys())
            assert not missing, (
                f"Skill '{skill.get('key', '?')}' is missing fields: {missing}"
            )

    def test_level_values_are_valid(self):
        """Every level field must be one of beginner/intermediate/advanced."""
        from models.skill_progress import SKILL_TREE

        valid_levels = {"beginner", "intermediate", "advanced"}
        for skill in SKILL_TREE:
            assert skill["level"] in valid_levels, (
                f"Skill '{skill['key']}' has invalid level: '{skill['level']}'"
            )

    def test_order_values_are_positive_integers(self):
        """Every order field must be a positive integer."""
        from models.skill_progress import SKILL_TREE

        for skill in SKILL_TREE:
            assert isinstance(skill["order"], int) and skill["order"] >= 1, (
                f"Skill '{skill['key']}' has invalid order: {skill['order']}"
            )


class TestSkillTreeUnlockChain:
    def test_every_unlocks_after_references_valid_key_or_none(self):
        """Every unlocks_after value must be a key that exists in SKILL_TREE, or None."""
        from models.skill_progress import SKILL_TREE

        all_keys = {s["key"] for s in SKILL_TREE}
        for skill in SKILL_TREE:
            ref = skill["unlocks_after"]
            assert ref is None or ref in all_keys, (
                f"Skill '{skill['key']}' has unlocks_after='{ref}' which is not a valid key"
            )

    def test_only_variables_has_none_in_beginner(self):
        """In beginner level, only 'variables' must have unlocks_after=None."""
        from models.skill_progress import SKILL_TREE

        beginner_none = [
            s["key"] for s in SKILL_TREE
            if s["level"] == "beginner" and s["unlocks_after"] is None
        ]
        assert beginner_none == ["variables"], (
            f"Expected only 'variables' as None in beginner, got: {beginner_none}"
        )

    def test_first_intermediate_skill_has_none(self):
        """The first intermediate skill (list_comprehension) must have unlocks_after=None."""
        from models.skill_progress import SKILL_TREE

        intermediate_none = [
            s["key"] for s in SKILL_TREE
            if s["level"] == "intermediate" and s["unlocks_after"] is None
        ]
        assert intermediate_none == ["list_comprehension"], (
            f"Expected only 'list_comprehension' as None in intermediate, got: {intermediate_none}"
        )

    def test_first_advanced_skill_has_none(self):
        """The first advanced skill (inheritance) must have unlocks_after=None."""
        from models.skill_progress import SKILL_TREE

        advanced_none = [
            s["key"] for s in SKILL_TREE
            if s["level"] == "advanced" and s["unlocks_after"] is None
        ]
        assert advanced_none == ["inheritance"], (
            f"Expected only 'inheritance' as None in advanced, got: {advanced_none}"
        )

    def test_exactly_three_skills_have_unlocks_after_none(self):
        """Exactly 3 skills (one per level) must have unlocks_after=None."""
        from models.skill_progress import SKILL_TREE

        none_skills = [s["key"] for s in SKILL_TREE if s["unlocks_after"] is None]
        assert len(none_skills) == 3, (
            f"Expected 3 skills with unlocks_after=None, got {len(none_skills)}: {none_skills}"
        )

    def test_sequential_unlock_chain_is_valid_per_level(self):
        """Within each level, unlock references form a linear chain without cycles."""
        from models.skill_progress import SKILL_TREE

        for level in ("beginner", "intermediate", "advanced"):
            level_skills = [s for s in SKILL_TREE if s["level"] == level]
            # Build a map from key -> unlocks_after
            chain_map = {s["key"]: s["unlocks_after"] for s in level_skills}
            all_keys = set(chain_map.keys())

            # Walk the chain starting from the None root; each key must appear exactly once
            visited = set()
            # Find the root (unlocks_after == None)
            roots = [k for k, v in chain_map.items() if v is None]
            assert len(roots) == 1, f"Level '{level}' must have exactly one root, got: {roots}"

            # Follow chain using the reverse map (unlocks_after -> next skill)
            next_map = {v: k for k, v in chain_map.items() if v is not None}
            current = roots[0]
            while current is not None:
                assert current not in visited, (
                    f"Cycle detected at '{current}' in level '{level}'"
                )
                visited.add(current)
                current = next_map.get(current)

            assert visited == all_keys, (
                f"Level '{level}' chain does not cover all skills. "
                f"Missing: {all_keys - visited}"
            )


# ---------------------------------------------------------------------------
# FIXED_SKILLS backward compatibility
# ---------------------------------------------------------------------------


class TestFixedSkillsAlias:
    def test_fixed_skills_is_a_list(self):
        """FIXED_SKILLS must be a list (not a generator or tuple at the top level)."""
        from models.skill_progress import FIXED_SKILLS

        assert isinstance(FIXED_SKILLS, list)

    def test_fixed_skills_has_37_items(self):
        """FIXED_SKILLS must contain exactly 37 items, matching SKILL_TREE length."""
        from models.skill_progress import FIXED_SKILLS

        assert len(FIXED_SKILLS) == 37

    def test_fixed_skills_items_are_two_tuples(self):
        """Every item in FIXED_SKILLS must be a (key, label) two-tuple."""
        from models.skill_progress import FIXED_SKILLS

        for item in FIXED_SKILLS:
            assert isinstance(item, tuple), f"Expected tuple, got {type(item)}: {item}"
            assert len(item) == 2, f"Expected 2-tuple, got {len(item)}-tuple: {item}"

    def test_fixed_skills_convertible_to_dict(self):
        """dict(FIXED_SKILLS) must work — keys must be unique strings."""
        from models.skill_progress import FIXED_SKILLS

        d = dict(FIXED_SKILLS)
        assert isinstance(d, dict)
        # No keys were lost (i.e., no duplicates)
        assert len(d) == 37

    def test_fixed_skills_keys_match_skill_tree_keys(self):
        """FIXED_SKILLS keys must match SKILL_TREE keys in the same order."""
        from models.skill_progress import FIXED_SKILLS, SKILL_TREE

        skill_tree_keys = [s["key"] for s in SKILL_TREE]
        fixed_keys = [key for key, _ in FIXED_SKILLS]
        assert fixed_keys == skill_tree_keys

    def test_fixed_skills_labels_match_skill_tree_labels(self):
        """FIXED_SKILLS labels must match SKILL_TREE labels in the same order."""
        from models.skill_progress import FIXED_SKILLS, SKILL_TREE

        skill_tree_labels = [s["label"] for s in SKILL_TREE]
        fixed_labels = [label for _, label in FIXED_SKILLS]
        assert fixed_labels == skill_tree_labels

    def test_fixed_skills_supports_for_loop_unpacking(self):
        """'for key, label in FIXED_SKILLS' must work without error."""
        from models.skill_progress import FIXED_SKILLS

        collected = []
        for key, label in FIXED_SKILLS:
            collected.append((key, label))

        assert len(collected) == 37


# ---------------------------------------------------------------------------
# ExerciseCompletion model column structure
# ---------------------------------------------------------------------------


class TestExerciseCompletionModel:
    def test_exercise_completion_importable(self):
        """ExerciseCompletion must be importable from models.exercise."""
        from models.exercise import ExerciseCompletion  # noqa: F401

        assert True

    def test_exercise_completion_has_correct_tablename(self):
        """ExerciseCompletion.__tablename__ must be 'exercise_completions'."""
        from models.exercise import ExerciseCompletion

        assert ExerciseCompletion.__tablename__ == "exercise_completions"

    def test_exercise_completion_has_user_id_column(self):
        """ExerciseCompletion must have a user_id column."""
        from models.exercise import ExerciseCompletion

        assert hasattr(ExerciseCompletion, "user_id")

    def test_exercise_completion_has_skill_key_column(self):
        """ExerciseCompletion must have a skill_key column."""
        from models.exercise import ExerciseCompletion

        assert hasattr(ExerciseCompletion, "skill_key")

    def test_exercise_completion_has_exercise_id_column(self):
        """ExerciseCompletion must have an exercise_id column."""
        from models.exercise import ExerciseCompletion

        assert hasattr(ExerciseCompletion, "exercise_id")

    def test_exercise_completion_has_score_granted_column(self):
        """ExerciseCompletion must have a score_granted column."""
        from models.exercise import ExerciseCompletion

        assert hasattr(ExerciseCompletion, "score_granted")

    def test_exercise_completion_has_is_locked_column(self):
        """ExerciseCompletion must have an is_locked column."""
        from models.exercise import ExerciseCompletion

        assert hasattr(ExerciseCompletion, "is_locked")

    def test_exercise_completion_score_granted_default_is_zero(self):
        """score_granted column default must be 0."""
        from models.exercise import ExerciseCompletion

        col = ExerciseCompletion.__table__.columns["score_granted"]
        assert col.default.arg == 0

    def test_exercise_completion_is_locked_default_is_false(self):
        """is_locked column default must be False."""
        from models.exercise import ExerciseCompletion

        col = ExerciseCompletion.__table__.columns["is_locked"]
        assert col.default.arg is False

    def test_exercise_completion_has_unique_constraint(self):
        """ExerciseCompletion must declare a UniqueConstraint on (user_id, skill_key, exercise_id)."""
        from models.exercise import ExerciseCompletion
        from sqlalchemy import UniqueConstraint

        constraints = [
            c for c in ExerciseCompletion.__table_args__
            if isinstance(c, UniqueConstraint)
        ]
        assert constraints, "No UniqueConstraint found in ExerciseCompletion.__table_args__"
        uc = constraints[0]
        constrained_cols = {col.key for col in uc.columns}
        assert constrained_cols == {"user_id", "skill_key", "exercise_id"}

    def test_exercise_completion_exportable_from_models_package(self):
        """ExerciseCompletion must be importable from the top-level models package."""
        from models import ExerciseCompletion  # noqa: F401

        assert True


# ---------------------------------------------------------------------------
# SkillTestResult model column structure
# ---------------------------------------------------------------------------


class TestSkillTestResultModel:
    def test_skill_test_result_importable(self):
        """SkillTestResult must be importable from models.skill_test."""
        from models.skill_test import SkillTestResult  # noqa: F401

        assert True

    def test_skill_test_result_has_correct_tablename(self):
        """SkillTestResult.__tablename__ must be 'skill_test_results'."""
        from models.skill_test import SkillTestResult

        assert SkillTestResult.__tablename__ == "skill_test_results"

    def test_skill_test_result_has_user_id_column(self):
        """SkillTestResult must have a user_id column."""
        from models.skill_test import SkillTestResult

        assert hasattr(SkillTestResult, "user_id")

    def test_skill_test_result_has_skill_key_column(self):
        """SkillTestResult must have a skill_key column."""
        from models.skill_test import SkillTestResult

        assert hasattr(SkillTestResult, "skill_key")

    def test_skill_test_result_has_score_column(self):
        """SkillTestResult must have a score column."""
        from models.skill_test import SkillTestResult

        assert hasattr(SkillTestResult, "score")

    def test_skill_test_result_has_passed_column(self):
        """SkillTestResult must have a passed column."""
        from models.skill_test import SkillTestResult

        assert hasattr(SkillTestResult, "passed")

    def test_skill_test_result_has_attempt_number_column(self):
        """SkillTestResult must have an attempt_number column."""
        from models.skill_test import SkillTestResult

        assert hasattr(SkillTestResult, "attempt_number")

    def test_skill_test_result_attempt_number_default_is_one(self):
        """attempt_number column default must be 1."""
        from models.skill_test import SkillTestResult

        col = SkillTestResult.__table__.columns["attempt_number"]
        assert col.default.arg == 1

    def test_skill_test_result_exportable_from_models_package(self):
        """SkillTestResult must be importable from the top-level models package."""
        from models import SkillTestResult  # noqa: F401

        assert True


# ---------------------------------------------------------------------------
# StudentSkillProgress unique constraint
# ---------------------------------------------------------------------------


class TestStudentSkillProgressConstraint:
    def test_student_skill_progress_has_unique_constraint(self):
        """StudentSkillProgress must declare a UniqueConstraint on (user_id, skill_key)."""
        from models.skill_progress import StudentSkillProgress
        from sqlalchemy import UniqueConstraint

        constraints = [
            c for c in StudentSkillProgress.__table_args__
            if isinstance(c, UniqueConstraint)
        ]
        assert constraints, (
            "No UniqueConstraint found in StudentSkillProgress.__table_args__"
        )
        uc = constraints[0]
        constrained_cols = {col.key for col in uc.columns}
        assert constrained_cols == {"user_id", "skill_key"}


# ---------------------------------------------------------------------------
# skill_analyzer.VALID_SKILLS coverage
# ---------------------------------------------------------------------------


class TestValidSkillsCoverage:
    def test_valid_skills_has_exactly_37_items(self):
        """VALID_SKILLS must contain exactly 37 entries."""
        from services.skill_analyzer import VALID_SKILLS

        assert len(VALID_SKILLS) == 37

    def test_all_skill_tree_keys_in_valid_skills(self):
        """Every key from SKILL_TREE must appear in VALID_SKILLS."""
        from models.skill_progress import SKILL_TREE
        from services.skill_analyzer import VALID_SKILLS

        skill_tree_keys = {s["key"] for s in SKILL_TREE}
        missing = skill_tree_keys - VALID_SKILLS
        assert not missing, f"Keys in SKILL_TREE but missing from VALID_SKILLS: {missing}"

    def test_valid_skills_contains_no_extra_keys(self):
        """VALID_SKILLS must not contain any key that is not in SKILL_TREE."""
        from models.skill_progress import SKILL_TREE
        from services.skill_analyzer import VALID_SKILLS

        skill_tree_keys = {s["key"] for s in SKILL_TREE}
        extra = VALID_SKILLS - skill_tree_keys
        assert not extra, f"Keys in VALID_SKILLS but not in SKILL_TREE: {extra}"

    def test_valid_skills_is_a_set(self):
        """VALID_SKILLS must be a set for O(1) membership checks."""
        from services.skill_analyzer import VALID_SKILLS

        assert isinstance(VALID_SKILLS, set)

    @pytest.mark.parametrize("skill_key", [
        # Beginner
        "variables", "datatypes", "input_output", "string_methods", "type_conversion",
        "if_else", "for_loop", "while_loop", "lists", "tuples", "sets",
        "dictionaries", "functions",
        # Intermediate
        "list_comprehension", "error_handling", "file_io", "classes_basic",
        "instance_methods", "instance_variables", "static_methods", "class_methods",
        "magic_methods", "modules_imports", "lambda_functions", "map_filter_reduce",
        # Advanced
        "inheritance", "polymorphism", "abstract_classes", "interfaces", "decorators",
        "generators", "context_managers", "recursion", "algorithms", "design_patterns",
        "async_await", "testing",
    ])
    def test_each_expected_key_in_valid_skills(self, skill_key: str):
        """Each of the 37 expected skill keys must be individually present in VALID_SKILLS."""
        from services.skill_analyzer import VALID_SKILLS

        assert skill_key in VALID_SKILLS, (
            f"Expected skill key '{skill_key}' not found in VALID_SKILLS"
        )
