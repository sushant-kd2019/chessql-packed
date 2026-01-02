# ChessQL Desktop GUI

A lightweight desktop application built with Electron that provides a graphical interface for browsing chess games using the ChessQL API.

## Features

- **Search Interface**: Query chess games using natural language or ChessQL syntax
- **Game Thumbnails**: Visual chess board thumbnails showing final positions
- **Game Viewer**: Full game viewer with move-by-move navigation (similar to Lichess)
- **Modern UI**: Clean, responsive interface with smooth animations
- **Real-time Search**: Instant search results with loading indicators

## Prerequisites

- Node.js (v14 or higher)
- Python 3.7+ (for ChessQL backend)
- The ChessQL backend must be running

## Installation

1. Install dependencies:
```bash
npm install
```

2. Make sure the ChessQL backend is set up and running:
```bash
cd ../chessql
pip install -r requirements.txt
python server.py
```

## Running the Application

### Development Mode
```bash
npm run dev
```

### Production Mode
```bash
npm start
```

## Usage

1. **Search for Games**: Use the search box at the top to query games
   - Natural Language: "lecorvus won", "queen sacrificed", "pawn promoted to queen"
   - ChessQL: "SELECT * FROM games WHERE white_player = 'lecorvus'"

2. **Browse Results**: Games are displayed as thumbnails with chess board positions

3. **View Games**: Click on any game thumbnail to open the full game viewer

4. **Navigate Moves**: Use the move controls to step through the game:
   - Previous/Next: Move one move at a time
   - First/Last: Jump to beginning or end of game

## Example Queries

### Natural Language
- "lecorvus won"
- "queen sacrificed"
- "pawn promoted to queen"
- "games where lecorvus was rated over 1500"

### ChessQL
- `SELECT * FROM games WHERE white_player = 'lecorvus'`
- `SELECT * FROM games WHERE (queen sacrificed)`
- `SELECT * FROM games WHERE (pawn promoted to queen x 2)`
- `SELECT * FROM games WHERE (lecorvus won) AND (queen sacrificed)`

## Architecture

- **Main Process** (`main.js`): Handles window management and starts the ChessQL server
- **Renderer Process** (`app.js`): Handles UI interactions and game display
- **Chess Engine** (`chess.js`): Manages chess game logic and move validation
- **API Integration**: Communicates with ChessQL backend via IPC

## File Structure

```
chessql-ui/
├── main.js          # Electron main process
├── index.html       # Main UI template
├── styles.css       # Application styles
├── app.js          # Renderer process logic
├── package.json    # Dependencies and scripts
└── README.md       # This file
```

## Troubleshooting

1. **"Failed to connect to ChessQL server"**: Make sure the ChessQL backend is running on port 9090
2. **Games not loading**: Check that the database file exists and contains games
3. **Chess board not displaying**: Ensure chess.js is properly loaded

## Development

To modify the application:

1. Edit the HTML/CSS in `index.html` and `styles.css`
2. Modify the JavaScript logic in `app.js`
3. Update the main process in `main.js` if needed
4. Run `npm run dev` to test changes

## License

ISC
