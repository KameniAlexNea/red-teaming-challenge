"""Command-line interface for the red-teaming agent."""

import asyncio
import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

from alex_red_teaming.config import Config
from alex_red_teaming.agent import RedTeamingAgent
from alex_red_teaming.utils import setup_logging, validate_config

app = typer.Typer(help="Red-teaming agent for AI models")
console = Console()


@app.command()
def run(
    config_file: str = typer.Option(
        None, "--config", "-c", help="Path to configuration file"
    ),
    target_model: str = typer.Option(
        "gpt-oss-20b", "--target", "-t", help="Target model to test"
    ),
    red_team_model: str = typer.Option(
        "llama3.1:latest", "--red-team", "-r", help="Red-teaming model"
    ),
    max_issues: int = typer.Option(
        5, "--max-issues", "-m", help="Maximum issues to find"
    ),
    output_dir: str = typer.Option(
        "red_teaming_results", "--output", "-o", help="Output directory"
    ),
    log_level: str = typer.Option("INFO", "--log-level", "-l", help="Logging level"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """Run the red-teaming agent."""

    # Setup logging
    setup_logging(log_level)

    # Load configuration
    if config_file:
        # TODO: Implement config file loading
        config = Config.from_env()
    else:
        config = Config.from_env()

    # Override with CLI arguments
    config.ollama.target_model = target_model
    config.ollama.red_teaming_model = red_team_model
    config.red_teaming.max_issues_to_find = max_issues
    config.output.output_dir = output_dir
    config.output.log_level = log_level

    # Validate configuration
    config_dict = {
        "ollama": {
            "base_url": config.ollama.base_url,
            "target_model": config.ollama.target_model,
            "red_teaming_model": config.ollama.red_teaming_model,
            "timeout": config.ollama.timeout,
        },
        "red_teaming": {
            "max_issues_to_find": config.red_teaming.max_issues_to_find,
            "max_conversation_turns": config.red_teaming.max_conversation_turns,
        },
    }

    errors = validate_config(config_dict)
    if errors:
        console.print("[red]Configuration errors:[/red]")
        for error in errors:
            console.print(f"  • {error}")
        raise typer.Exit(1)

    # Display configuration
    console.print(
        Panel.fit(
            f"[bold]Red-Teaming Configuration[/bold]\n\n"
            f"Target Model: [cyan]{config.ollama.target_model}[/cyan]\n"
            f"Red-Team Model: [cyan]{config.ollama.red_teaming_model}[/cyan]\n"
            f"Max Issues: [yellow]{config.red_teaming.max_issues_to_find}[/yellow]\n"
            f"Output Directory: [green]{config.output.output_dir}[/green]\n"
            f"Ollama URL: [blue]{config.ollama.base_url}[/blue]",
            title="Configuration",
        )
    )

    # Run the agent
    async def run_agent():
        agent = RedTeamingAgent(config)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Running red-teaming agent...", total=None)

            try:
                result = await agent.run()
                progress.update(task, description="✅ Red-teaming completed")
                return result
            except Exception as e:
                progress.update(task, description=f"❌ Error: {str(e)}")
                raise

    # Run async function
    try:
        result = asyncio.run(run_agent())

        if result["success"]:
            console.print("\n[green]✅ Red-teaming completed successfully![/green]")

            # Display results table
            table = Table(title="Red-Teaming Results")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="magenta")

            table.add_row("Vulnerabilities Found", str(result["vulnerabilities_found"]))
            table.add_row("Total Conversations", str(result["total_conversations"]))
            table.add_row(
                "Success Rate",
                f"{(result['vulnerabilities_found'] / max(result['total_conversations'], 1)) * 100:.1f}%",
            )

            console.print(table)

            # Display vulnerabilities
            if result["vulnerabilities"] and verbose:
                console.print("\n[bold]Discovered Vulnerabilities:[/bold]")
                for i, vuln in enumerate(result["vulnerabilities"], 1):
                    console.print(f"\n{i}. [red]{vuln['title']}[/red]")
                    console.print(f"   Type: {vuln['type']}")
                    console.print(f"   Severity: {vuln['severity'].upper()}")
                    console.print(f"   Description: {vuln['description'][:100]}...")
        else:
            console.print(
                f"[red]❌ Red-teaming failed: {result.get('error', 'Unknown error')}[/red]"
            )
            raise typer.Exit(1)

    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Red-teaming interrupted by user[/yellow]")
        raise typer.Exit(130)
    except Exception as e:
        console.print(f"[red]❌ Error running red-teaming agent: {e}[/red]")
        if verbose:
            import traceback

            console.print(traceback.format_exc())
        raise typer.Exit(1)


@app.command()
def list_models():
    """List available models on Ollama."""

    async def get_models():
        from alex_red_teaming.ollama_client import OllamaClient
        from alex_red_teaming.config import OllamaConfig

        client = OllamaClient(OllamaConfig())

        try:
            import ollama

            ollama_client = ollama.Client(host=client.config.base_url)
            models = ollama_client.list()

            table = Table(title="Available Ollama Models")
            table.add_column("Model Name", style="cyan")
            table.add_column("Size", style="green")
            table.add_column("Modified", style="yellow")

            for model in models["models"]:
                size = f"{model.get('size', 0) / (1024**3):.1f} GB"
                modified = model.get("modified_at", "Unknown")[:19]
                table.add_row(model["name"], size, modified)

            console.print(table)

        except Exception as e:
            console.print(f"[red]Error connecting to Ollama: {e}[/red]")
            console.print("Make sure Ollama is running on the configured URL")

    asyncio.run(get_models())


@app.command()
def validate_setup():
    """Validate the setup and configuration."""

    console.print("[bold]Validating Red-Teaming Setup[/bold]\n")

    checks = [
        ("Configuration", lambda: Config.from_env()),
        ("Ollama Connection", None),  # Will be implemented
        ("Target Model", None),  # Will be implemented
        ("Red-Team Model", None),  # Will be implemented
    ]

    for check_name, check_func in checks:
        try:
            if check_func:
                check_func()
            console.print(f"✅ {check_name}: [green]OK[/green]")
        except Exception as e:
            console.print(f"❌ {check_name}: [red]FAILED[/red] - {e}")


@app.command()
def generate_config(
    output_file: str = typer.Option(
        "config.yaml", "--output", "-o", help="Output configuration file"
    ),
):
    """Generate a sample configuration file."""

    config_content = """# Red-Teaming Agent Configuration

ollama:
  base_url: "http://localhost:11434"
  red_teaming_model: "llama3.1:latest"
  target_model: "gpt-oss-20b"
  timeout: 120
  temperature: 0.8

red_teaming:
  max_issues_to_find: 5
  max_conversation_turns: 10
  max_retries_per_attack: 3
  vulnerability_categories:
    - "deceptive_alignment"
    - "reward_hacking"
    - "lying_and_deception"
    - "jailbreaking"
    - "prompt_injection"
    - "data_extraction"
    - "harmful_content_generation"
    - "bias_amplification"
    - "misinformation_generation"
    - "privacy_violations"

output:
  output_dir: "red_teaming_results"
  log_level: "INFO"
  save_conversations: true
  save_failed_attempts: true
  report_format: "json"
"""

    try:
        with open(output_file, "w") as f:
            f.write(config_content)
        console.print(f"[green]✅ Configuration file generated: {output_file}[/green]")
    except Exception as e:
        console.print(f"[red]❌ Error generating configuration file: {e}[/red]")


if __name__ == "__main__":
    app()
