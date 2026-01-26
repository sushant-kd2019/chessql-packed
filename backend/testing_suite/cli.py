"""
Command-line interface for the testing suite.
"""

import sys
import click
from pathlib import Path

# Add parent directory to path for imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

try:
    from .config import TestConfig
    from .generate_baseline import generate_baseline, save_baseline
    from .test_runner import TestRunner, save_results
    from .report_generator import (
        generate_text_report,
        generate_html_report,
        save_report,
        load_latest_results
    )
except ImportError:
    # Handle direct execution
    from config import TestConfig
    from generate_baseline import generate_baseline, save_baseline
    from test_runner import TestRunner, save_results
    from report_generator import (
        generate_text_report,
        generate_html_report,
        save_report,
        load_latest_results
    )


@click.group()
@click.option(
    "--reference-player",
    default="lecorvus",
    help="Reference player name"
)
@click.option(
    "--db-path",
    default=None,
    help="Path to chess games database"
)
@click.option(
    "--api-key",
    default=None,
    help="OpenAI API key (default: from environment)"
)
@click.pass_context
def cli(ctx, reference_player, db_path, api_key):
    """NL→CQL Testing Suite CLI"""
    ctx.ensure_object(dict)
    ctx.obj['config'] = TestConfig(
        reference_player=reference_player,
        db_path=db_path or TestConfig().db_path,
        api_key=api_key
    )


@cli.command()
@click.option(
    "--output",
    default="baseline_truth.json",
    help="Output filename"
)
@click.pass_context
def generate_baseline_cmd(ctx, output):
    """Generate baseline truth from current system."""
    config = ctx.obj['config']
    
    click.echo("Generating baseline truth...")
    click.echo(f"Reference player: {config.reference_player}")
    click.echo(f"Database: {config.db_path}")
    click.echo("-" * 50)
    
    baseline_data = generate_baseline(config)
    
    if "error" in baseline_data:
        click.echo(f"Error: {baseline_data['error']}", err=True)
        sys.exit(1)
    
    save_baseline(baseline_data, config, output)
    click.echo("\n✓ Baseline generation complete!")


@cli.command()
@click.option(
    "--baseline",
    default="baseline_truth.json",
    help="Baseline filename"
)
@click.option(
    "--output",
    default=None,
    help="Output filename (auto-generated if not provided)"
)
@click.pass_context
def run_tests(ctx, baseline, output):
    """Run test suite and compare with baseline."""
    config = ctx.obj['config']
    
    try:
        runner = TestRunner(config)
        results = runner.run_tests(baseline)
        
        results_path = save_results(results, config, output)
        
        if results["summary"]["failed"] > 0 or results["summary"]["errors"] > 0:
            click.echo("\n✗ Some tests failed or had errors")
            sys.exit(1)
        else:
            click.echo("\n✓ All tests passed!")
            sys.exit(0)
    
    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        click.echo("\nPlease run 'generate-baseline' first.", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--results-file",
    default=None,
    help="Path to results JSON file (default: latest)"
)
@click.option(
    "--format",
    type=click.Choice(["txt", "html", "both"]),
    default="both",
    help="Report format"
)
@click.option(
    "--output",
    default=None,
    help="Output filename (auto-generated if not provided)"
)
@click.pass_context
def view_report(ctx, results_file, format, output):
    """Generate and view test report."""
    import json
    
    config = ctx.obj['config']
    
    # Load results
    if results_file:
        with open(results_file, 'r') as f:
            results = json.load(f)
    else:
        results = load_latest_results(config)
        if not results:
            click.echo("No test results found. Please run tests first.", err=True)
            sys.exit(1)
    
    # Generate reports
    if format in ["txt", "both"]:
        text_report = generate_text_report(results)
        save_report(text_report, config, output, "txt")
        if format == "txt":
            click.echo("\n" + text_report)
    
    if format in ["html", "both"]:
        html_report = generate_html_report(results)
        save_report(html_report, config, output, "html")
        if format == "html":
            report_path = config.reports_dir / (output or f"test_report_latest.html")
            click.echo(f"\nHTML report saved. Open in browser: {report_path}")


@cli.command()
@click.pass_context
def list_baselines(ctx):
    """List available baseline files."""
    config = ctx.obj['config']
    
    baseline_files = sorted(config.baseline_dir.glob("*.json"))
    
    if not baseline_files:
        click.echo("No baseline files found.")
        return
    
    click.echo("Available baseline files:")
    for baseline_file in baseline_files:
        click.echo(f"  - {baseline_file.name}")


@cli.command()
@click.pass_context
def list_reports(ctx):
    """List available test reports."""
    config = ctx.obj['config']
    
    report_files = sorted(
        config.reports_dir.glob("*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    
    if not report_files:
        click.echo("No test reports found.")
        return
    
    click.echo("Available test reports:")
    for report_file in report_files[:10]:  # Show last 10
        click.echo(f"  - {report_file.name}")


def main():
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()

