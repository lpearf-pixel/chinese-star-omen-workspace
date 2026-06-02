# Chinese Star Omen Workspace

Monorepo workspace for the Chinese star omen research system.

## Apps

- `apps/local-kb-unified`: upstream official KB, ingest, Qdrant, KB Search API
- `apps/star-omen`: downstream query, fallback, candidate cards, sync, rule engine

## Shared Packages

- `packages/kb-contracts`: shared schemas and helper contracts

## Common Commands

```bash
make up
make ingest
make health
make inspect-kaiyuan
make generate-candidate
make sync
