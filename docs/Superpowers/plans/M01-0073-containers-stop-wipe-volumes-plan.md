# M01-0073 — Plan: containers stop wipes volumes

Spec: `docs/Superpowers/specs/M01-0073-containers-stop-wipe-volumes-design.md`. Issue **#133**.

## Task 1: Flip default wipe in parsers and down script

- [ ] `docker-profiles.sh`: default `CCA_WIPE=1`; add `--keep-volumes` → `CCA_WIPE=0`; keep `--wipe` → `CCA_WIPE=1`
- [ ] `docker-all-down.sh`: header text; use `-v` when `CCA_WIPE=1`
- [ ] Commit: `M01-0073 #133: wipe Docker volumes on containers stop by default`

## Task 2: Docs

- [ ] Root `README.md` note under containers section
- [ ] Commit: `M01-0073 #133: document wipe-on-stop for local containers`

## Task 3: Milestone + story complete

- [ ] Update `Milestone_01.md` (TOC + Superpowers rows + feature tree)
- [ ] Close #133 after merge
