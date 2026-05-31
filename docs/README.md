# KI Python Tutor - Documentation Index

This documentation describes the KI Python Tutor system, including its architecture, features, and APIs.

## Getting Started

- [Main Project README](../README.md) - Project goals, installation, and quick start

## Understanding Features

Learn how specific features work:

- **[Exercise & Skill System](understanding-features/exercise-skill-system.md)** - Complete guide to the 37-skill progression system, exercises, and skill tests

## API Reference

Detailed API endpoint documentation:

- **[Exercise Endpoints](api-reference/exercises-endpoints.md)** - Submit code, retrieve exercises, get hints
- **[Skill Tests Endpoints](api-reference/skill-tests-endpoints.md)** - Generate and submit skill tests
- **[Skill Tree Reference](api-reference/skill-tree.md)** - Complete listing of all 37 skills and unlock chains

## System Architecture

The KI Python Tutor consists of:

- **Backend**: FastAPI + SQLAlchemy (PostgreSQL), LangChain agents for AI capabilities
- **Frontend**: Next.js + TypeScript with interactive skill cards and exercise modals
- **LLM Integration**: OpenAI (gpt-4o) or local Ollama for exercise generation and evaluation
- **Code Execution**: Sandboxed Python execution with captured stdout/stderr

### Key Components

```
Backend:
  - Skill Tree: 37 skills across Beginner/Intermediate/Advanced levels
  - Exercise System: Static exercises for Beginner, LLM-generated for higher levels
  - Progress Tracking: Student scores, skill tests, exercise completions
  - LangChain Tools: Exercise evaluators, hint generators, test generators

Frontend:
  - Skill Cards: Clickable skill progression view
  - Exercise Modal: Code editor with submission and hint interface
  - Skill Test Modal: Test interface with multiple choice, code reading, mini-task
  - Progress Dashboard: User skill progression and statistics
```

## Database Schema

Main tables used by the exercise system:

- `users` - User accounts with authentication
- `student_skill_progress` - Current score (0-100) for each user-skill pair
- `exercise_completions` - Tracks (user, skill, exercise) completion state
- `skill_test_results` - Test attempts with scores and pass/fail status
- `learning_events` - Historical analysis events

## Quick Links

| Need | Link |
|------|------|
| Understand exercise flow | [Feature Guide](understanding-features/exercise-skill-system.md) |
| Submit an exercise | [POST /exercises/submit](api-reference/exercises-endpoints.md#post-exercisessubmit) |
| Generate a skill test | [POST /skill-tests/generate](api-reference/skill-tests-endpoints.md#post-skill-testsgenerate) |
| View all skills | [Skill Tree](api-reference/skill-tree.md) |
| Complete project info | [README.md](../README.md) |
