# Release Checklist

This document provides a comprehensive checklist for releasing new versions of codemate-hub, including model artifact versioning and deployment procedures.

## Table of Contents

- [Pre-Release Checklist](#pre-release-checklist)
- [Release Process](#release-process)
- [Model Versioning](#model-versioning)
- [Post-Release Checklist](#post-release-checklist)
- [Hotfix Process](#hotfix-process)
- [Rollback Procedure](#rollback-procedure)

---

## Pre-Release Checklist

### Code Quality

- [ ] All unit tests pass locally: `pytest tests/ -v --ignore=tests/integration/`
- [ ] All integration tests pass: `./scripts/test-integration.sh full`
- [ ] Code formatted with black: `black src/ tests/`
- [ ] Code linted with ruff: `ruff src/ tests/`
- [ ] No security vulnerabilities in dependencies: `pip check`
- [ ] Documentation updated to reflect changes
- [ ] CHANGELOG.md updated with release notes
- [ ] Version number bumped in `pyproject.toml`

### Functional Validation

- [ ] Clean build successful: `./scripts/build.sh`
- [ ] All services start and become healthy: `./scripts/deploy.sh`
- [ ] Health checks pass: `./scripts/check-health.sh 120`
- [ ] Pipeline executes without errors: `docker exec coding-assistant python src/pipeline.py`
- [ ] Enclave demo runs successfully: `docker exec coding-assistant python zephyr/demo_enclave.py`
- [ ] Orchestrator examples work: `docker exec coding-assistant python -m src.orchestration_examples`
- [ ] Langflow UI accessible and functional: http://localhost:7860
- [ ] Code-Server accessible: http://localhost:8080
- [ ] Ollama API responding: `curl http://localhost:11434/api/tags`

### Model Validation

- [ ] Default models available: `./scripts/model-pull.sh default`
- [ ] Models listed in Ollama: `docker exec ollama ollama list`
- [ ] Embedding model matches `src/memory_setup.py` configuration (line 60)
- [ ] Chroma DB initialized: `ls -la chroma_db/`
- [ ] Memory system functional: `docker exec coding-assistant python src/memory_setup.py`

### Documentation

- [ ] README.md is accurate and complete
- [ ] All example commands tested and working
- [ ] Troubleshooting guide updated with new common issues
- [ ] API documentation updated (if applicable)
- [ ] Migration guide created (for breaking changes)
- [ ] trackers/ files updated with completion status

### Security

- [ ] No secrets committed in repository
- [ ] `.env.example` updated with new variables (if any)
- [ ] Security dependencies updated
- [ ] Container images scanned for vulnerabilities
- [ ] Access controls reviewed

---

## Release Process

### 1. Version Numbering

Follow [Semantic Versioning](https://semver.org/) (MAJOR.MINOR.PATCH):

- **MAJOR**: Breaking changes, incompatible API changes
- **MINOR**: New features, backward-compatible
- **PATCH**: Bug fixes, backward-compatible

**Current version:** Check `pyproject.toml` line 7

**Examples:**
- `0.4.0` → `0.4.1` (bug fix)
- `0.4.1` → `0.5.0` (new feature)
- `0.5.0` → `1.0.0` (major release, breaking changes)

### 2. Update Version

```bash
# Edit pyproject.toml
nano pyproject.toml
# Update version = "X.Y.Z" on line 7

# Verify change
grep "version =" pyproject.toml
```

### 3. Update CHANGELOG.md

```bash
nano CHANGELOG.md
```

Add new section at the top:

```markdown
## Version X.Y.Z - YYYY-MM-DD

### Added
- New feature 1
- New feature 2

### Changed
- Modified behavior 1
- Updated dependency X to version Y

### Fixed
- Bug fix 1
- Bug fix 2

### Deprecated
- Feature X (will be removed in version Y.Z.W)

### Removed
- Removed deprecated feature X

### Security
- Security fix 1
```

### 4. Commit Release Changes

```bash
git add pyproject.toml CHANGELOG.md trackers/
git commit -m "Release version X.Y.Z"
git push origin main
```

### 5. Create Git Tag

```bash
# Create annotated tag
git tag -a vX.Y.Z -m "Release version X.Y.Z"

# Push tag to remote
git push origin vX.Y.Z

# Verify tag
git tag -l
git show vX.Y.Z
```

### 6. Create GitHub Release

1. Go to: https://github.com/tzervas/codemate-hub/releases/new
2. Select tag: `vX.Y.Z`
3. Release title: `Version X.Y.Z - Release Name`
4. Description: Copy from CHANGELOG.md
5. Attach assets (if any):
   - Release notes PDF
   - Example flows (from `docs/langflow/examples/`)
   - Configuration templates
6. Click "Publish release"

### 7. Build and Test Release

```bash
# Clean environment
./scripts/teardown.sh --force

# Build from tagged release
git checkout vX.Y.Z
./scripts/build.sh

# Deploy and validate
./scripts/deploy.sh
./scripts/check-health.sh 180
./scripts/test-integration.sh full

# Return to main
git checkout main
```

---

## Model Versioning

### Model Artifact Strategy

Models are versioned separately from code using tags and digests.

#### Default Models

**Primary model (code generation):**
- Name: `qwen2.5-coder:7b-q4_0`
- Purpose: Code generation, embeddings
- Size: ~4.7GB
- Updated: As needed for quality improvements

**Fallback model (general tasks):**
- Name: `mistral:latest`
- Purpose: General-purpose LLM tasks
- Size: ~4.1GB
- Updated: Monthly or as needed

#### Model Registry

Track model versions in `docs/MODEL_VERSIONS.md`:

```markdown
## Model Version History

### Current Production Models (vX.Y.Z)
- qwen2.5-coder:7b-q4_0 (SHA256: abc123...)
- mistral:latest (SHA256: def456...)

### Previous Versions
- v0.4.0: qwen2.5-coder:7b, mistral:latest
- v0.3.0: codellama:7b, mistral:latest
```

#### Model Update Procedure

When updating default models:

1. **Test new model:**
   ```bash
   ./scripts/model-pull.sh <new-model>
   docker exec ollama ollama list
   ```

2. **Update configuration:**
   - Edit `scripts/model-pull.sh` (update MODEL_DEFAULT)
   - Edit `src/memory_setup.py` (line 60, if embedding model changes)
   - Update README.md references

3. **Validate embeddings:**
   ```bash
   # Reinitialize with new model
   rm -rf chroma_db/
   docker exec coding-assistant python src/memory_setup.py
   ```

4. **Test full pipeline:**
   ```bash
   docker exec coding-assistant python src/pipeline.py
   pytest tests/integration/ -v -m integration
   ```

5. **Document change:**
   - Add to CHANGELOG.md under "Changed"
   - Update `docs/MODEL_SELECTION.md`
   - Update `docs/MODEL_VERSIONS.md`

6. **Tag model configuration:**
   ```bash
   git add scripts/model-pull.sh src/memory_setup.py docs/
   git commit -m "Update default model to <new-model>"
   git tag -a models-vX.Y.Z -m "Model configuration for vX.Y.Z"
   git push origin main models-vX.Y.Z
   ```

#### Model Pruning Strategy

**Before release:**
```bash
# Check disk usage
docker system df

# List unused models
./scripts/model-prune.sh list-unused

# Prune (keeps protected models)
./scripts/model-prune.sh keep-models
```

**Protected models** (never pruned):
- qwen2.5-coder (all variants)
- mistral (latest)

To add models to protected list, edit `scripts/model-prune.sh`.

---

## Post-Release Checklist

### Verification

- [ ] GitHub release published successfully
- [ ] Git tag pushed: `git tag -l | grep vX.Y.Z`
- [ ] CHANGELOG.md updated on main branch
- [ ] Documentation deployed (if using docs site)
- [ ] Release notes sent to stakeholders
- [ ] Docker images built (if publishing to registry)

### Monitoring

- [ ] Monitor GitHub issues for bug reports
- [ ] Monitor deployment logs for errors
- [ ] Check service health on production instances
- [ ] Verify metrics in Grafana (if observability enabled)
- [ ] Review model inference performance

### Communication

- [ ] Announce release in project channels
- [ ] Update project board/tracker status
- [ ] Close completed issues and milestones
- [ ] Thank contributors

### Cleanup

- [ ] Close release milestone in GitHub
- [ ] Archive old documentation versions
- [ ] Update related repositories (if any)
- [ ] Plan next release cycle

---

## Hotfix Process

For critical bugs requiring immediate release:

### 1. Create Hotfix Branch

```bash
# From main or release tag
git checkout -b hotfix/vX.Y.Z main
# or
git checkout -b hotfix/vX.Y.Z vX.Y.Z-1
```

### 2. Apply Fix

```bash
# Make minimal changes
nano src/affected_file.py

# Test thoroughly
pytest tests/ -v
./scripts/test-integration.sh full

# Commit
git add .
git commit -m "Fix: Critical bug description"
```

### 3. Bump Patch Version

```bash
# Update version in pyproject.toml
# X.Y.Z → X.Y.Z+1

# Update CHANGELOG.md
nano CHANGELOG.md
```

### 4. Merge and Release

```bash
# Merge to main
git checkout main
git merge --no-ff hotfix/vX.Y.Z
git push origin main

# Tag and release
git tag -a vX.Y.Z -m "Hotfix release vX.Y.Z"
git push origin vX.Y.Z

# Delete hotfix branch
git branch -d hotfix/vX.Y.Z
```

---

## Rollback Procedure

If a release has critical issues:

### 1. Identify Previous Stable Version

```bash
git tag -l
# Identify last stable version, e.g., vX.Y.Z-1
```

### 2. Rollback Deployment

```bash
# Stop current deployment
./scripts/teardown.sh --force

# Checkout previous version
git checkout vX.Y.Z-1

# Rebuild and deploy
./scripts/build.sh
./scripts/deploy.sh

# Verify health
./scripts/check-health.sh 180
```

### 3. Communicate Issue

- Post incident report in GitHub issue
- Update release notes with "ROLLED BACK" notice
- Communicate to users/stakeholders

### 4. Fix and Re-release

- Fix issue on main branch
- Follow hotfix process for new patch release
- Thoroughly test before releasing

---

## Release Artifacts

### What to Archive

For each release, archive:

1. **Code snapshot:**
   - Git tag (automatic)
   - Source tarball: `git archive vX.Y.Z --format=tar.gz -o codemate-hub-vX.Y.Z.tar.gz`

2. **Configuration:**
   - `docker-compose.yml`
   - `.env.example`
   - `pyproject.toml`

3. **Documentation:**
   - `README.md`
   - `CHANGELOG.md`
   - `docs/` directory

4. **Model artifacts:**
   - List of model names and versions
   - Model digests/checksums
   - `docs/MODEL_VERSIONS.md`

5. **Langflow flows:**
   - `docs/langflow/examples/*.json`
   - Flow documentation

### Storage

- GitHub Releases: Attach key files
- Git tags: Code snapshots
- Documentation site: Versioned docs
- Artifact registry: Docker images (if applicable)

---

## Version History

| Version | Date       | Type    | Description                     |
|---------|------------|---------|---------------------------------|
| 0.4.0   | 2024-12-XX | Minor   | Current version (Task 08)       |
| 0.3.0   | 2024-12-XX | Minor   | Task 05-07 completion           |
| 0.2.0   | 2024-12-XX | Minor   | Task 03-04 completion           |
| 0.1.0   | 2024-12-XX | Minor   | Initial release (Task 01-02)    |

---

## Checklist Template

Use this template for each release:

```markdown
## Release vX.Y.Z Checklist

**Release Manager:** [Name]
**Target Date:** YYYY-MM-DD
**Type:** [Major/Minor/Patch]

### Pre-Release
- [ ] All tests passing
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version bumped in pyproject.toml
- [ ] Models validated
- [ ] Security checks passed

### Release
- [ ] Changes committed
- [ ] Git tag created
- [ ] GitHub release published
- [ ] Release tested from clean deployment

### Post-Release
- [ ] Release verified
- [ ] Stakeholders notified
- [ ] Issues/milestones closed
- [ ] Next release planned

### Sign-off
- [ ] Release Manager: __________ Date: __________
- [ ] Tech Lead: __________ Date: __________
```

---

## Questions?

For questions about the release process:
- Review this checklist
- Check `trackers/PLAN.md` for milestone status
- Refer to `CHANGELOG.md` for version history
- See `docs/` for technical documentation
