# Contributing to Haki FMCG 2.0

Thank you for your interest in contributing to the **Haki FMCG** enterprise procurement intelligence platform.

---

## 🛠️ Development Workflow

### 1. Branch Strategy
- `main`: Production-ready release branch. Deployed automatically to staging/production.
- `develop`: Ongoing feature integration branch.
- Feature branches: `feat/<feature-name>`
- Bugfix branches: `fix/<issue-name>`
- Documentation: `docs/<topic>`

### 2. Conventional Commits
All commit messages must adhere to the [Conventional Commits](https://www.conventionalcommits.org/) specification:
- `feat(scope): add new capability`
- `fix(scope): resolve bug or calculation error`
- `docs(scope): update documentation or guides`
- `test(scope): add unit or integration tests`
- `refactor(scope): optimize code structure without changing behavior`

### 3. Code Standards & Testing
- **Backend (Python)**:
  - PEP 8 compliant formatting.
  - Run tests: `pytest tests/ -v` and `python test_core_functions_fidelity.py`.
- **Frontend (React 19 / TypeScript)**:
  - Strict TypeScript types (`noImplicitAny`).
  - Run build validation: `npm run build` inside `haki-fmcg-frontend`.

---

## 📝 Pull Request Checklist
Before submitting a Pull Request, ensure:
1. All unit and fidelity tests pass.
2. Code follows domain calculation accuracy rules (physics & metal pricing models).
3. No secrets or API credentials are committed.
4. Descriptive PR title and summary matching `.github/pull_request_template.md`.
