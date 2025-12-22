# ChessQL Productionising Documentation

Technical documentation for packaging ChessQL as a distributable desktop application.

## Phases

| Phase | Document | Status |
|-------|----------|--------|
| 1 | [Lichess Authentication](./phase1-lichess-authentication.md) | ✅ Complete |
| 2 | [Lichess Game Sync](./phase2-lichess-game-sync.md) | ✅ Complete |
| 3 | Account Management UI | 🔜 Pending |
| 4 | Application Packaging | 🔜 Pending |

## Key Implementation Notes

### Move Format Compatibility (Phase 2)

The piece analyzer was updated to support **both** move formats:
- **PGN format**: `1. e4 e5 2. Nf3 Nc6` (with move numbers)
- **Lichess format**: `e4 e5 Nf3 Nc6` (space-separated, no numbers)

This ensures capture analysis works correctly for games streamed from Lichess.

## Quick Links

- [Main Plan](../PRODUCTIONIZING_PLAN.md)
- [API Docs](http://localhost:9090/docs) (when server is running)

## Architecture Overview

```
ChessQL Desktop App
├── Electron Shell (UI)
│   ├── index.html / app.js
│   └── OAuth handler
│
└── Python Backend (bundled via PyInstaller)
    ├── FastAPI server
    ├── SQLite database
    ├── Lichess auth module
    └── Game sync service
```

