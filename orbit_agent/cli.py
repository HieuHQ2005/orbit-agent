from __future__ import annotations

import json
import logging
import typer
from rich.console import Console
from rich.table import Table
from pathlib import Path

from .config import configure_lm, get_config
from .advisor import HighOrbitAdvisor, log_advice
from .tools.dilution import calc_dilution
from .tools.finance import runway_months, expected_value
from .tools.retention import calculate_cohort_retention
from .tools.funnel import analyze_funnel, FunnelStep
from .memory import load_context, save_context
import os
import subprocess

# Setup rich console and logging
console = Console()
logger = logging.getLogger(__name__)

app = typer.Typer(help="Orbit Agent CLI — brutally honest startup advisor")
ctx_app = typer.Typer(help="Manage your Orbit context")
app.add_typer(ctx_app, name="context")

@app.callback()
def _init():
    """Initialize the application"""
    try:
        config = configure_lm()
        console.print(f"[bold]LM:[/bold] {config.lm.model}")
        console.print("[dim]Config loaded from environment[/dim]")
    except Exception as e:
        console.print(f"[bold red]Configuration Error:[/bold red] {e}")
        raise typer.Exit(1)

@app.command()
def ask(
    question: str, 
    playbook_path: str = typer.Option("playbooks/high_orbit.yaml", "--playbook", "-p")
):
    """Ask a brutally honest, high-orbit question."""
    try:
        # Load playbook
        pb_path = Path(playbook_path)
        if pb_path.exists():
            playbook = pb_path.read_text()
            logger.info(f"Loaded playbook: {playbook_path}")
        else:
            playbook = ""
            logger.warning(f"Playbook not found: {playbook_path}")
        
        # Create advisor and get response
        advisor = HighOrbitAdvisor()
        history = [{"role": "user", "content": question}]
        
        with console.status("[bold green]Thinking..."):
            result = advisor(history=history, playbook=playbook)
        
        log_advice(history, result)
        
        # Display results
        console.print("\n[bold underline]Advice[/]:")
        console.print(result.advice)
        
        console.print("\n[bold]48h Actions:[/]")
        # Parse actions from string format
        if isinstance(result.actions_48h, str):
            actions = [line.strip() for line in result.actions_48h.split('\n') if line.strip()]
            for i, action in enumerate(actions[:5], 1):  # Limit to 5 actions
                clean_action = action.lstrip('123456789. -•*').strip()
                if clean_action:  # Only show non-empty actions
                    console.print(f"{i}. {clean_action}")
        else:
            for i, action in enumerate(result.actions_48h, 1):
                console.print(f"{i}. {action}")
        
        console.print(f"\n[bold]Metric to watch:[/] {result.metric_to_watch}")
        
        console.print("\n[bold]Top risks:[/]")
        # Parse risks from string format
        if isinstance(result.risks, str):
            risks = [line.strip() for line in result.risks.split('\n') if line.strip()]
            for risk in risks[:3]:  # Limit to 3 risks
                clean_risk = risk.lstrip('123456789. -•*').strip()
                if clean_risk:  # Only show non-empty risks
                    console.print(f"• {clean_risk}")
        else:
            for risk in result.risks:
                console.print(f"- {risk}")
        
        console.print(f"\n[bold]Critique:[/] {result.critique}")
        console.print(f"[bold]Score:[/] {result.score}/10")
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        raise typer.Exit(0)
    except Exception as e:
        logger.error(f"Ask command failed: {e}")
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)

@app.command()
def chat(playbook_path: str = typer.Option("playbooks/high_orbit.yaml", "--playbook", "-p")):
    """Start an interactive chat session with the Orbit Agent."""
    try:
        # Load playbook
        pb_path = Path(playbook_path)
        if pb_path.exists():
            playbook = pb_path.read_text()
            logger.info(f"Loaded playbook: {playbook_path}")
        else:
            playbook = ""
            logger.warning(f"Playbook not found: {playbook_path}")
        
        advisor = HighOrbitAdvisor()
        history = []

        console.print("[bold]Orbit Agent:[/bold] How can I help you today?")
        console.print("[dim]Type 'exit' or 'quit' to end the conversation[/dim]\n")

        while True:
            try:
                question = console.input("[bold blue]>[/bold blue] ")
                
                if question.lower().strip() in ["exit", "quit", "q"]:
                    console.print("[yellow]Goodbye![/yellow]")
                    break

                if not question.strip():
                    continue

                history.append({"role": "user", "content": question})
                
                with console.status("[bold green]Thinking..."):
                    result = advisor(history=history, playbook=playbook)
                
                log_advice(history, result)

                # Display results
                console.print("\n[bold underline]Advice[/]:")
                console.print(result.advice)
                
                console.print("\n[bold]48h Actions:[/]")
                # Parse actions from string format
                if isinstance(result.actions_48h, str):
                    actions = [line.strip() for line in result.actions_48h.split('\n') if line.strip()]
                    for i, action in enumerate(actions[:5], 1):  # Limit to 5 actions
                        clean_action = action.lstrip('123456789. -•*').strip()
                        if clean_action:  # Only show non-empty actions
                            console.print(f"{i}. {clean_action}")
                else:
                    for i, action in enumerate(result.actions_48h, 1):
                        console.print(f"{i}. {action}")
                
                console.print(f"\n[bold]Metric to watch:[/] {result.metric_to_watch}")
                
                console.print("\n[bold]Top risks:[/]")
                # Parse risks from string format
                if isinstance(result.risks, str):
                    risks = [line.strip() for line in result.risks.split('\n') if line.strip()]
                    for risk in risks[:3]:  # Limit to 3 risks
                        clean_risk = risk.lstrip('123456789. -•*').strip()
                        if clean_risk:  # Only show non-empty risks
                            console.print(f"• {clean_risk}")
                else:
                    for risk in result.risks:
                        console.print(f"- {risk}")
                
                console.print(f"\n[bold]Score:[/] {result.score}/10\n")

                # Add assistant response to history for context
                history.append({"role": "assistant", "content": result.advice})
                
                # Keep history manageable
                if len(history) > 20:
                    history = history[-20:]

            except (KeyboardInterrupt, EOFError):
                console.print("\n[yellow]Goodbye![/yellow]")
                break
            except Exception as e:
                logger.error(f"Chat error: {e}")
                console.print(f"[red]Error: {e}[/red]")

    except Exception as e:
        logger.error(f"Chat command failed: {e}")
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)

@app.command()
def focus(goal: str):
    """Force a 48h focus plan with pre-mortem."""
    enhanced_question = f"Create a ruthless 48h focus plan to achieve: {goal}. Include specific deadlines, success metrics, and a pre-mortem of what could go wrong."
    ask(enhanced_question)

@app.command()
def dilution(
    pre: float = typer.Option(..., help="Pre-money valuation"), 
    raise_amount: float = typer.Option(..., "--raise", help="Raise amount"),
    option_pool_add: float = typer.Option(0.0, "--option-pool-add", help="Additional option pool (post-money fraction)")
):
    """Compute post-money and ownership after a round."""
    try:
        result = calc_dilution(pre, raise_amount, option_pool_add)
        
        table = Table(title="Dilution Analysis")
        table.add_column("Metric", style="bold")
        table.add_column("Value", justify="right")
        
        table.add_row("Pre-money", f"${result.pre_money:,.0f}")
        table.add_row("Raise", f"${result.raise_amount:,.0f}")
        table.add_row("Post-money", f"${result.post_money:,.0f}")
        table.add_row("New investor %", f"{result.new_percent*100:.2f}%")
        table.add_row("Existing holders %", f"{result.existing_percent*100:.2f}%")
        table.add_row("Option pool add (post)", f"{result.option_pool_add*100:.2f}%")
        
        console.print(table)
        logger.info(f"Dilution calculated: pre={pre}, raise={raise_amount}")
        
    except Exception as e:
        logger.error(f"Dilution calculation failed: {e}")
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)

@app.command()
def runway(
    cash: float = typer.Option(..., help="Current cash on hand"), 
    burn: float = typer.Option(..., help="Monthly burn rate"), 
    growth: float = typer.Option(0.0, help="Monthly revenue growth rate (0.1 = 10%)")
):
    """Rough runway months and default-alive flag."""
    try:
        result = runway_months(cash, burn, growth)
        
        status_color = "green" if result.default_alive else "red"
        status_text = "Default-Alive" if result.default_alive else "Default-Dead"
        
        console.print(f"[bold]Runway:[/bold] {result.months:.1f} months")
        console.print(f"[bold]Status:[/bold] [{status_color}]{status_text}[/{status_color}]")
        
        if not result.default_alive:
            console.print("[yellow]⚠️  You need to reach profitability or raise funds soon![/yellow]")
        
        logger.info(f"Runway calculated: {result.months:.1f} months, alive: {result.default_alive}")
        
    except Exception as e:
        logger.error(f"Runway calculation failed: {e}")
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)

@app.command()
def ev(
    p_upside: float = typer.Option(..., help="Probability of upside scenario"),
    ev_upside: float = typer.Option(..., help="Expected value of upside scenario"),
    p_mid: float = typer.Option(..., help="Probability of mid scenario"),
    ev_mid: float = typer.Option(..., help="Expected value of mid scenario"),
    p_down: float = typer.Option(..., help="Probability of downside scenario"),
    ev_down: float = typer.Option(..., help="Expected value of downside scenario")
):
    """Expected value quick check across 3 scenarios."""
    try:
        result = expected_value(p_upside, ev_upside, p_mid, ev_mid, p_down, ev_down)
        
        table = Table(title="Expected Value Analysis")
        table.add_column("Scenario", style="bold")
        table.add_column("Probability", justify="right")
        table.add_column("Value", justify="right")
        table.add_column("Contribution", justify="right")
        
        table.add_row("Upside", f"{p_upside:.1%}", f"${ev_upside:,.0f}", f"${p_upside * ev_upside:,.0f}")
        table.add_row("Mid", f"{p_mid:.1%}", f"${ev_mid:,.0f}", f"${p_mid * ev_mid:,.0f}")
        table.add_row("Downside", f"{p_down:.1%}", f"${ev_down:,.0f}", f"${p_down * ev_down:,.0f}")
        table.add_row("", "", "", "", style="dim")
        table.add_row("Expected Value", "", "", f"${result:,.0f}", style="bold green")
        
        console.print(table)
        logger.info(f"Expected value calculated: ${result:,.0f}")
        
    except Exception as e:
        logger.error(f"EV calculation failed: {e}")
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)

@app.command()
def retention(cohorts_json: str):
    """Calculate cohort retention from a JSON string."""
    try:
        cohorts = json.loads(cohorts_json)
        results = calculate_cohort_retention(cohorts)
        
        table = Table(title="Cohort Retention Analysis")
        table.add_column("Cohort Size", style="bold")
        
        # Add columns for each time period
        max_periods = max(len(result.retention_rates) for result in results)
        for i in range(max_periods):
            table.add_column(f"Period {i}", justify="right")

        for result in results:
            row = [str(result.cohort[0])]
            for rate in result.retention_rates:
                row.append(f"{rate:.1f}%")
            table.add_row(*row)
            
        console.print(table)
        logger.info(f"Retention analysis completed for {len(results)} cohorts")
        
    except json.JSONDecodeError as e:
        console.print(f"[bold red]JSON Error:[/bold red] Invalid format: {e}")
        raise typer.Exit(1)
    except Exception as e:
        logger.error(f"Retention analysis failed: {e}")
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)

@app.command()
def funnel(funnel_steps_json: str):
    """Analyze a marketing funnel from a JSON string."""
    try:
        steps_data = json.loads(funnel_steps_json)
        steps = [FunnelStep(**step) for step in steps_data]
        result = analyze_funnel(steps)
        
        table = Table(title="Funnel Analysis")
        table.add_column("Step", style="bold")
        table.add_column("Users", justify="right")
        table.add_column("Conversion %", justify="right")

        for i, step in enumerate(result.steps):
            conversion = ""
            if i < len(result.conversion_rates):
                rate = result.conversion_rates[i]
                color = "green" if rate > 20 else "yellow" if rate > 10 else "red"
                conversion = f"[{color}]{rate:.1f}%[/{color}]"
            
            table.add_row(step.name, f"{step.user_count:,}", conversion)
            
        console.print(table)
        logger.info(f"Funnel analysis completed for {len(steps)} steps")
        
    except json.JSONDecodeError as e:
        console.print(f"[bold red]JSON Error:[/bold red] Invalid format: {e}")
        raise typer.Exit(1)
    except Exception as e:
        logger.error(f"Funnel analysis failed: {e}")
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)

@app.command()
def config_info():
    """Show current configuration"""
    try:
        config = get_config()
        
        table = Table(title="Orbit Agent Configuration")
        table.add_column("Setting", style="bold")
        table.add_column("Value")
        
        table.add_row("LM Model", config.lm.model)
        table.add_row("API Base", config.lm.api_base or "Default")
        table.add_row("Max Tokens", str(config.lm.max_tokens))
        table.add_row("Temperature", str(config.lm.temperature))
        table.add_row("Twilio Configured", "Yes" if config.twilio.is_configured else "No")
        table.add_row("Data Directory", str(config.data_dir))
        table.add_row("Playbook Path", str(config.playbook_path))
        table.add_row("Log Level", config.log_level)
        
        console.print(table)
        
    except Exception as e:
        logger.error(f"Config info failed: {e}")
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


@ctx_app.command("show")
def context_show():
    """Show current user context used to personalize advice"""
    try:
        content = load_context()
        if not content:
            console.print("[yellow]No context set. Use 'orbit-agent context set ""<text>""' to save one.[/yellow]")
            return
        console.print("[bold underline]Context[/]:\n" + content)
    except Exception as e:
        logger.error(f"Failed to load context: {e}")
        console.print(f"[bold red]Error:[/bold red] {e}")


@ctx_app.command("set")
def context_set(text: str = typer.Argument(..., help="Context text to save")):
    """Set/replace your user context"""
    try:
        ok = save_context(text)
        if ok:
            console.print("[green]Context saved.[/green]")
        else:
            console.print("[red]Failed to save context.[/red]")
    except Exception as e:
        logger.error(f"Failed to save context: {e}")
        console.print(f"[bold red]Error:[/bold red] {e}")


@ctx_app.command("edit")
def context_edit(editor: str = typer.Option(None, help="Editor to use (default: $EDITOR or nano/vi)")):
    """Open your context file in your editor ($EDITOR)"""
    try:
        from pathlib import Path
        ctx_path = Path.home() / ".orbit" / "context.md"
        ctx_path.parent.mkdir(exist_ok=True)
        if not ctx_path.exists():
            ctx_path.write_text("")

        chosen = editor or os.environ.get("EDITOR") or ("notepad" if os.name == "nt" else "nano")
        console.print(f"[dim]Opening {ctx_path} with {chosen}[/dim]")
        subprocess.run([chosen, str(ctx_path)], check=False)
        console.print("[green]Done.[/green]")
    except Exception as e:
        logger.error(f"Failed to edit context: {e}")
        console.print(f"[bold red]Error:[/bold red] {e}")

if __name__ == "__main__":
    app()
