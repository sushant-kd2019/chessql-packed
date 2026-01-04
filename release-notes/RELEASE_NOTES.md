# ChessQL v1.0.0 — Initial Release 🎉

**Release Date:** January 4, 2026

ChessQL is a powerful desktop application for chess enthusiasts who want to analyze, search, and explore their game collections using advanced query techniques.

---

## ✨ Features

### 🔐 Lichess Integration
- **Secure OAuth2 Authentication** — Connect your Lichess account using industry-standard PKCE flow
- **Game Import** — Automatically fetch and store your games from Lichess
- **Reference Player Support** — Track specific players for focused analysis

### 🔍 Chess Query Language (CQL)
- **Pattern Matching** — Search for specific positions, piece configurations, and tactical patterns
- **Advanced Filters** — Filter games by result, date, opening, and more
- **PGN Export** — Export matching games in standard PGN format

### 🤖 AI-Powered Natural Language Search
- **Ask in Plain English** — Query your games using natural language (e.g., "Show me games where I sacrificed a knight")
- **OpenAI Integration** — Powered by GPT for intelligent query translation
- **Secure Key Storage** — API key cached locally for convenience

### 🖥️ Desktop Experience
- **Native Application** — Runs as a standalone desktop app (no browser required)
- **Dark Theme** — Easy on the eyes during long analysis sessions
- **Responsive UI** — Clean, modern interface built with Electron

---

## 📦 Installation

### macOS (Apple Silicon)
1. Download `ChessQL-1.0.0-arm64.dmg`
2. Open the DMG and drag **ChessQL** to your Applications folder
3. **First launch:** Right-click the app → Open → Open (required once to bypass Gatekeeper)

---

## ⚙️ Requirements

| Requirement | Details |
|-------------|---------|
| **Operating System** | macOS (Apple Silicon M1/M2/M3/M4) |
| **Internet** | Required for Lichess sync |
| **OpenAI API Key** | Optional — enables natural language search |

---

## 🚀 Getting Started

1. **Launch ChessQL** from your Applications folder
2. **Connect Lichess** — Click "Authenticate with Lichess" and authorize the app
3. **Import Games** — Enter your Lichess username and click "Import Games"
4. **Start Searching** — Use CQL patterns or natural language queries to explore your games

### Example CQL Queries
```
# Find games with a queen sacrifice
cql() piece q on [a-h][1-8] capture

# Find checkmates with a knight
cql() mate piece n attacks k
```

### Example Natural Language Queries
> "Show me games where I castled queenside"  
> "Find games where my opponent blundered a piece"  
> "Games with a bishop pair in the endgame"

---

## 📁 Data Storage

ChessQL stores your data in:
```
~/Library/Application Support/ChessQL/
├── chessql.db      # Game database
└── .env            # OpenAI API key
```

---

## 🐛 Known Issues

- **Gatekeeper Warning** — Since this release is not code-signed, macOS will show a security warning on first launch. This is expected behavior for unsigned apps.
- **Intel Macs** — This release targets Apple Silicon only. Intel Mac support coming soon.

---

## 🙏 Acknowledgments

- [Lichess](https://lichess.org) — For their excellent open API
- [CQL](http://www.gadycosteff.com/cql/) — Chess Query Language specification
- [OpenAI](https://openai.com) — Natural language processing

---

**Full Changelog:** Initial release

