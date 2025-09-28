"""
Chess PGN Database CLI Interface
Simplified CLI for SQL queries on metadata and regex queries on moves.
"""

import click
import os
import json
from typing import List, Dict, Any
from database import ChessDatabase
from ingestion import PGNIngestion
from query_language import ChessQueryLanguage


@click.group(invoke_without_command=True)
@click.option('--db', default='chess_games.db', help='Database file path')
@click.pass_context
def cli(ctx, db):
    """ChessQL - Chess PGN Database Query Language CLI"""
    ctx.ensure_object(dict)
    ctx.obj['db_path'] = db
    
    # If no command provided, start interactive mode
    if ctx.invoked_subcommand is None:
        _start_interactive_mode(ctx)


@cli.command()
@click.argument('input_path')
@click.option('--pattern', default='*.pgn', help='File pattern for directory ingestion')
@click.pass_context
def ingest(ctx, input_path, pattern):
    """Ingest PGN files into the database."""
    db_path = ctx.obj['db_path']
    
    if not os.path.exists(input_path):
        click.echo(f"Error: Path '{input_path}' does not exist.")
        return
    
    ingestion = PGNIngestion(db_path)
    
    if os.path.isfile(input_path):
        count = ingestion.ingest_file(input_path)
        click.echo(f"Successfully ingested {count} games from {input_path}")
    elif os.path.isdir(input_path):
        count = ingestion.ingest_directory(input_path, pattern)
        click.echo(f"Successfully ingested {count} games from {input_path}")
    else:
        click.echo(f"Error: '{input_path}' is not a valid file or directory.")


@cli.command()
@click.argument('query')
@click.option('--format', 'output_format', default='table', 
              type=click.Choice(['table', 'json', 'csv']), 
              help='Output format')
@click.option('--limit', default=100, help='Maximum number of results')
@click.pass_context
def query(ctx, query, output_format, limit):
    """Execute a query against the chess database.
    
    Query types:
    - SQL queries: SELECT * FROM games WHERE white_player = 'lecorvus'
    - Regex queries: /e4.*c5/ (for moves matching pattern)
    """
    db_path = ctx.obj['db_path']
    
    if not os.path.exists(db_path):
        click.echo(f"Error: Database '{db_path}' does not exist. Run 'ingest' first.")
        return
    
    query_lang = ChessQueryLanguage(db_path)
    
    try:
        results = query_lang.execute_query(query)
        
        if not results:
            click.echo("No results found.")
            return
        
        # Limit results
        results = results[:limit]
        
        if output_format == 'json':
            click.echo(json.dumps(results, indent=2))
        elif output_format == 'csv':
            _output_csv(results)
        else:  # table format
            _output_table(results)
            
    except Exception as e:
        click.echo(f"Error executing query: {e}")


@cli.command()
@click.pass_context
def stats(ctx):
    """Show database statistics."""
    db_path = ctx.obj['db_path']
    
    if not os.path.exists(db_path):
        click.echo(f"Error: Database '{db_path}' does not exist. Run 'ingest' first.")
        return
    
    db = ChessDatabase(db_path)
    stats = db.get_database_stats()
    
    click.echo("Database Statistics:")
    click.echo(f"  Total games: {stats['total_games']}")
    click.echo(f"  Unique players: {stats['unique_players']}")
    click.echo(f"  Results breakdown:")
    for result, count in stats['results'].items():
        click.echo(f"    {result}: {count}")


@cli.command()
@click.pass_context
def examples(ctx):
    """Show example queries."""
    query_lang = ChessQueryLanguage()
    examples = query_lang.get_query_examples()
    
    click.echo("Example Queries:")
    click.echo("=" * 50)
    
    for i, example in enumerate(examples, 1):
        click.echo(f"{i}. {example}")
    
    click.echo("\nQuery Types:")
    click.echo("=" * 50)
    click.echo("SQL queries: Use standard SQL syntax for metadata")
    click.echo("Regex queries: Use /pattern/ syntax for moves")


@cli.command()
@click.argument('game_id', type=int)
@click.pass_context
def show(ctx, game_id):
    """Show detailed information about a specific game."""
    db_path = ctx.obj['db_path']
    
    if not os.path.exists(db_path):
        click.echo(f"Error: Database '{db_path}' does not exist. Run 'ingest' first.")
        return
    
    db = ChessDatabase(db_path)
    game = db.execute_sql_query(f"SELECT * FROM games WHERE id = {game_id}")
    
    if not game:
        click.echo(f"Game with ID {game_id} not found.")
        return
    
    game = game[0]
    click.echo(f"Game #{game_id}")
    click.echo("=" * 50)
    click.echo(f"White: {game.get('white_player', 'Unknown')}")
    click.echo(f"Black: {game.get('black_player', 'Unknown')}")
    click.echo(f"Result: {game.get('result', 'Unknown')}")
    click.echo(f"Date: {game.get('date_played', 'Unknown')}")
    click.echo(f"Event: {game.get('event', 'Unknown')}")
    click.echo(f"Site: {game.get('site', 'Unknown')}")
    click.echo(f"Round: {game.get('round', 'Unknown')}")
    click.echo(f"ECO: {game.get('eco_code', 'Unknown')}")
    click.echo(f"Opening: {game.get('opening', 'Unknown')}")
    click.echo(f"Time Control: {game.get('time_control', 'Unknown')}")
    click.echo(f"White Elo: {game.get('white_elo', 'Unknown')}")
    click.echo(f"Black Elo: {game.get('black_elo', 'Unknown')}")
    click.echo("\nMoves:")
    click.echo("-" * 30)
    click.echo(game.get('moves', ''))


def _start_interactive_mode(ctx):
    """Start interactive mode."""
    db_path = ctx.obj['db_path']
    
    if not os.path.exists(db_path):
        click.echo(f"Error: Database '{db_path}' does not exist. Run 'ingest' first.")
        return
    
    query_lang = ChessQueryLanguage(db_path)
    
    click.echo("ChessQL Interactive Mode")
    click.echo("Type 'help' for commands, 'quit' to exit")
    click.echo("=" * 50)
    
    while True:
        try:
            user_input = click.prompt("\nchessql> ", type=str)
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                break
            elif user_input.lower() == 'help':
                _show_help()
            elif user_input.lower() == 'examples':
                _show_examples(query_lang)
            elif user_input.lower() == 'stats':
                _show_stats(query_lang)
            elif user_input.strip():
                results = query_lang.execute_query(user_input)
                if results:
                    _output_table(results[:20])  # Show first 20 results
                    if len(results) > 20:
                        click.echo(f"... and {len(results) - 20} more results")
                else:
                    click.echo("No results found.")
        
        except KeyboardInterrupt:
            click.echo("\nGoodbye!")
            break
        except Exception as e:
            click.echo(f"Error: {e}")


def _show_help():
    """Show help information."""
    click.echo("""
Available Commands:
  help      - Show this help message
  examples  - Show example queries
  stats     - Show database statistics
  quit/exit - Exit interactive mode

Query Types:
  - SQL queries: SELECT * FROM games WHERE white_player = 'lecorvus'
  - Pattern queries: /e4/ (for moves matching pattern)
""")


def _show_examples(query_lang: ChessQueryLanguage):
    """Show query examples."""
    examples = query_lang.get_query_examples()
    click.echo("\nExample Queries:")
    for i, example in enumerate(examples, 1):
        click.echo(f"  {i}. {example}")


def _show_stats(query_lang: ChessQueryLanguage):
    """Show database statistics."""
    db = query_lang.db
    stats = db.get_database_stats()
    
    click.echo(f"\nDatabase Statistics:")
    click.echo(f"  Total games: {stats['total_games']}")
    click.echo(f"  Unique players: {stats['unique_players']}")


def _output_table(results: List[Dict[str, Any]]):
    """Output results in table format."""
    if not results:
        return
    
    # Get column headers dynamically from the first result
    headers = list(results[0].keys())
    
    # Calculate column widths
    widths = [len(header) for header in headers]
    for result in results:
        for i, header in enumerate(headers):
            widths[i] = max(widths[i], len(str(result.get(header, ''))))
    
    # Print header
    header_row = " | ".join(header.ljust(widths[i]) for i, header in enumerate(headers))
    click.echo(header_row)
    click.echo("-" * len(header_row))
    
    # Print rows
    for result in results:
        row = " | ".join([
            str(result.get(header, '')).ljust(widths[i]) for i, header in enumerate(headers)
        ])
        click.echo(row)


def _output_csv(results: List[Dict[str, Any]]):
    """Output results in CSV format."""
    if not results:
        return
    
    import csv
    import sys
    
    if results:
        fieldnames = results[0].keys()
        writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)


if __name__ == '__main__':
    cli()