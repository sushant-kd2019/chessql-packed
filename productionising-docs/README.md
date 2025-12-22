# ChessQL Productionising Documentation

Technical documentation for packaging ChessQL as a distributable desktop application.

## Phases

| Phase | Document | Status |
|-------|----------|--------|
| 1 | [Lichess Authentication](./phase1-lichess-authentication.md) | ✅ Complete |
| 2 | Lichess Game Streaming | 🔜 Pending |
| 3 | Account Management UI | 🔜 Pending |
| 4 | Application Packaging | 🔜 Pending |

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

