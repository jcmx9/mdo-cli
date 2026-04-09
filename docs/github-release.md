# Release Workflow

## Versioning

CalVer `YY.M.x` (prod) / `YY.M.x.devN` (dev). Managed by bump-my-version.

## Dev Release

```bash
git checkout dev
# make changes, commit
./scripts/release.sh dev
```

Bumps `.devN` suffix and pushes to `dev`.

## Prod Release

```bash
git checkout dev
./scripts/release.sh prod
```

Strips `.devN`, merges `dev` into `main`, tags, creates GitHub release, returns to `dev`.

## New Month

```bash
./scripts/release.sh prod --new-month
```

Advances the CalVer minor (month) before the prod release.

## Manual Version Check

```bash
bump-my-version show-bump
```
