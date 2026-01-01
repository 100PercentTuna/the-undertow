"""
CLI commands for The Undertow.

Provides command-line interface for running the pipeline, managing
sources, and administrative tasks.
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import UUID

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.panel import Panel


console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="undertow")
def cli() -> None:
    """The Undertow - Global Intelligence System CLI."""
    pass


# ============================================================================
# Pipeline Commands
# ============================================================================

@cli.group()
def pipeline() -> None:
    """Pipeline management commands."""
    pass


@pipeline.command("run")
@click.option("--story-id", type=str, help="Story ID to process")
@click.option("--headline", type=str, help="Headline for new story")
@click.option("--summary", type=str, help="Summary for new story")
@click.option("--zones", type=str, help="Comma-separated zones")
@click.option("--dry-run", is_flag=True, help="Show plan without executing")
def run_pipeline(
    story_id: Optional[str],
    headline: Optional[str],
    summary: Optional[str],
    zones: Optional[str],
    dry_run: bool,
) -> None:
    """Run the analysis pipeline for a story."""
    from undertow.core.pipeline.full_orchestrator import get_orchestrator
    from undertow.schemas.stories import Story

    if not story_id and not headline:
        console.print("[red]Error: Must provide --story-id or --headline[/red]")
        sys.exit(1)

    async def _run() -> None:
        orchestrator = get_orchestrator()

        if story_id:
            console.print(f"[blue]Loading story {story_id}...[/blue]")
            # Load from database
            # For now, create a placeholder
            story = Story(
                id=UUID(story_id),
                headline="Loading...",
                summary="",
            )
        else:
            story = Story(
                headline=headline,
                summary=summary or "",
                zones=zones.split(",") if zones else [],
            )

        console.print(Panel(f"[bold]{story.headline}[/bold]", title="Story"))

        if dry_run:
            console.print("[yellow]Dry run - showing pipeline stages:[/yellow]")
            stages = [
                "1. Collection - Gather sources",
                "2. Motivation - Four-layer analysis",
                "3. Chains - Forward/backward tracing",
                "4. Self-Critique - Internal review",
                "5. Adversarial - Challenger/Advocate debate",
                "6. Synthesis - Combine analyses",
                "7. Production - Generate article",
                "8. Final QA - Editor review",
            ]
            for stage in stages:
                console.print(f"  [dim]→[/dim] {stage}")
            return

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Running pipeline...", total=None)

            result = await orchestrator.run_full_pipeline(story)

            if result.success:
                progress.update(task, description="[green]Pipeline complete![/green]")
            else:
                progress.update(task, description=f"[red]Pipeline failed: {result.error}[/red]")

        if result.success:
            console.print(f"\n[green]✓ Article generated[/green]")
            console.print(f"  Quality: {result.article_quality:.0%}")
            console.print(f"  Duration: {result.duration_seconds:.1f}s")
            console.print(f"  Cost: ${result.total_cost:.2f}")
        else:
            console.print(f"\n[red]✗ Pipeline failed[/red]")
            if result.escalation_id:
                console.print(f"  Escalation: {result.escalation_id}")

    asyncio.run(_run())


@pipeline.command("status")
@click.option("--run-id", type=str, help="Pipeline run ID")
def pipeline_status(run_id: Optional[str]) -> None:
    """Check pipeline status."""
    console.print("[blue]Checking pipeline status...[/blue]")

    table = Table(title="Recent Pipeline Runs")
    table.add_column("Run ID", style="cyan")
    table.add_column("Story")
    table.add_column("Status")
    table.add_column("Quality")
    table.add_column("Started")

    # Placeholder data
    table.add_row(
        "abc123",
        "Israel-Somaliland Recognition",
        "[green]completed[/green]",
        "92%",
        "2 hours ago",
    )
    table.add_row(
        "def456",
        "Niger Coup Analysis",
        "[yellow]in_progress[/yellow]",
        "-",
        "5 min ago",
    )

    console.print(table)


# ============================================================================
# Verification Commands
# ============================================================================

@cli.group()
def verify() -> None:
    """Verification and fact-checking commands."""
    pass


@verify.command("extract")
@click.argument("text_file", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), help="Output JSON file")
def extract_claims(text_file: str, output: Optional[str]) -> None:
    """Extract verifiable claims from text."""
    from undertow.verification import get_claim_extractor
    from undertow.verification.claim_extractor import ClaimExtractionInput
    from undertow.llm.router import get_router

    text = Path(text_file).read_text()

    async def _run() -> None:
        router = get_router()
        extractor = get_claim_extractor(router)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Extracting claims...", total=None)

            result = await extractor.run(ClaimExtractionInput(text=text))

            progress.update(task, description="[green]Done![/green]")

        if result.success and result.output:
            console.print(f"\n[green]Found {result.output.total_claims} claims[/green]")
            console.print(f"Verifiable: {result.output.verifiable_claims}")

            for claim in result.output.claims[:10]:
                console.print(f"\n  [cyan]{claim.claim_type}[/cyan]: {claim.text}")
                console.print(f"    Confidence: {claim.confidence:.0%}")

            if output:
                data = {
                    "claims": [c.model_dump() for c in result.output.claims],
                    "total": result.output.total_claims,
                    "verifiable": result.output.verifiable_claims,
                }
                Path(output).write_text(json.dumps(data, indent=2))
                console.print(f"\n[dim]Saved to {output}[/dim]")
        else:
            console.print(f"[red]Extraction failed: {result.error}[/red]")

    asyncio.run(_run())


@verify.command("check")
@click.argument("claim")
@click.option("--zones", type=str, help="Comma-separated zones to search")
def check_claim(claim: str, zones: Optional[str]) -> None:
    """Verify a single claim against sources."""
    from undertow.verification import get_claim_verifier
    from undertow.verification.claim_extractor import ExtractedClaim, ClaimType

    async def _run() -> None:
        verifier = get_claim_verifier()

        extracted = ExtractedClaim(
            claim_id="cli-1",
            text=claim,
            claim_type=ClaimType.FACTUAL,
            confidence=1.0,
            source_sentence=claim,
            requires_verification=True,
        )

        zone_list = zones.split(",") if zones else []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Verifying...", total=None)

            results = await verifier.verify_claims_batch([extracted], zone_list)

            progress.update(task, description="[green]Done![/green]")

        if results:
            result = results[0]
            status_color = {
                "verified": "green",
                "supported": "cyan",
                "disputed": "yellow",
                "refuted": "red",
                "unverifiable": "dim",
            }.get(result.status.value, "white")

            console.print(f"\n[{status_color}]{result.status.value.upper()}[/{status_color}]")
            console.print(f"Score: {result.verification_score:.0%}")
            console.print(f"Independent sources: {result.independent_sources}")

            if result.evidence:
                console.print("\n[bold]Evidence:[/bold]")
                for ev in result.evidence[:3]:
                    console.print(f"  • {ev.get('snippet', '')[:100]}...")

    asyncio.run(_run())


# ============================================================================
# Escalation Commands
# ============================================================================

@cli.group()
def escalations() -> None:
    """Escalation management commands."""
    pass


@escalations.command("list")
@click.option("--status", type=str, help="Filter by status")
@click.option("--priority", type=str, help="Filter by priority")
def list_escalations(status: Optional[str], priority: Optional[str]) -> None:
    """List pending escalations."""
    from undertow.core.human_escalation import get_escalation_service, EscalationPriority

    service = get_escalation_service()
    priority_filter = EscalationPriority(priority) if priority else None
    pending = service.get_pending_escalations(priority_filter)

    table = Table(title="Escalations")
    table.add_column("ID", style="cyan", width=8)
    table.add_column("Priority")
    table.add_column("Story", max_width=40)
    table.add_column("Reason")
    table.add_column("Score")
    table.add_column("Created")

    priority_colors = {
        "critical": "red bold",
        "high": "red",
        "medium": "yellow",
        "low": "dim",
    }

    for e in pending[:20]:
        table.add_row(
            str(e.escalation_id)[:8],
            f"[{priority_colors.get(e.priority.value, 'white')}]{e.priority.value}[/]",
            e.story_headline[:40],
            e.reason.value,
            f"{e.quality_score:.0%}",
            e.created_at.strftime("%m/%d %H:%M"),
        )

    console.print(table)
    console.print(f"\n[dim]Total: {len(pending)} escalations[/dim]")


@escalations.command("resolve")
@click.argument("escalation_id")
@click.option("--approve", is_flag=True, help="Approve the content")
@click.option("--reject", is_flag=True, help="Reject the content")
@click.option("--notes", type=str, required=True, help="Review notes")
@click.option("--reviewer", type=str, required=True, help="Reviewer name")
def resolve_escalation(
    escalation_id: str,
    approve: bool,
    reject: bool,
    notes: str,
    reviewer: str,
) -> None:
    """Resolve an escalation."""
    from undertow.core.human_escalation import get_escalation_service, EscalationStatus

    if approve == reject:
        console.print("[red]Error: Must specify either --approve or --reject[/red]")
        sys.exit(1)

    service = get_escalation_service()
    status = EscalationStatus.APPROVED if approve else EscalationStatus.REJECTED

    async def _run() -> None:
        result = await service.resolve_escalation(
            escalation_id=UUID(escalation_id),
            status=status,
            reviewer=reviewer,
            notes=notes,
        )

        if result:
            console.print(f"[green]✓ Escalation {status.value}[/green]")
        else:
            console.print("[red]Escalation not found[/red]")

    asyncio.run(_run())


# ============================================================================
# RAG / Document Commands
# ============================================================================

@cli.group()
def docs() -> None:
    """Document and RAG management."""
    pass


@docs.command("index")
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--source-type", type=str, default="file", help="Source type")
@click.option("--zones", type=str, help="Comma-separated zones")
def index_document(file_path: str, source_type: str, zones: Optional[str]) -> None:
    """Index a document for RAG."""
    from undertow.rag import get_vector_store

    content = Path(file_path).read_text()

    async def _run() -> None:
        store = await get_vector_store()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Indexing document...", total=None)

            doc_id = await store.add_document(
                content=content,
                source_type=source_type,
                zones=zones.split(",") if zones else [],
                metadata={"file_path": file_path},
            )

            progress.update(task, description="[green]Indexed![/green]")

        console.print(f"\n[green]✓ Document indexed[/green]")
        console.print(f"  ID: {doc_id}")

    asyncio.run(_run())


@docs.command("search")
@click.argument("query")
@click.option("--zones", type=str, help="Comma-separated zones")
@click.option("--limit", type=int, default=5, help="Number of results")
def search_documents(query: str, zones: Optional[str], limit: int) -> None:
    """Search indexed documents."""
    from undertow.rag import get_vector_store

    async def _run() -> None:
        store = await get_vector_store()

        results = await store.search(
            query=query,
            zones=zones.split(",") if zones else None,
            limit=limit,
        )

        console.print(f"\n[bold]Results for:[/bold] {query}\n")

        for i, result in enumerate(results, 1):
            score = result.get("score", 0)
            content = result.get("content", "")[:200]
            source = result.get("source_type", "unknown")

            console.print(f"[cyan]{i}.[/cyan] [{source}] (score: {score:.2f})")
            console.print(f"   {content}...")
            console.print()

    asyncio.run(_run())


# ============================================================================
# Cost Commands
# ============================================================================

@cli.group()
def costs() -> None:
    """Cost tracking and budget management."""
    pass


@costs.command("summary")
@click.option("--period", type=str, default="day", help="day, week, month")
def cost_summary(period: str) -> None:
    """Show cost summary."""
    from undertow.services.cost_tracker import get_cost_tracker

    tracker = get_cost_tracker()
    summary = tracker.get_summary()

    console.print(Panel("[bold]Cost Summary[/bold]", expand=False))

    table = Table()
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")

    table.add_row("Today", f"${summary['today']:.2f}")
    table.add_row("This Week", f"${summary['week']:.2f}")
    table.add_row("This Month", f"${summary['month']:.2f}")
    table.add_row("All Time", f"${summary['total']:.2f}")
    table.add_row("Daily Budget", f"${summary['budget_remaining']:.2f} remaining")

    console.print(table)


@costs.command("by-agent")
def costs_by_agent() -> None:
    """Show costs breakdown by agent."""
    from undertow.services.cost_tracker import get_cost_tracker

    tracker = get_cost_tracker()
    breakdown = tracker.get_breakdown_by_agent()

    table = Table(title="Costs by Agent")
    table.add_column("Agent", style="cyan")
    table.add_column("Calls", justify="right")
    table.add_column("Cost", justify="right")

    for agent, data in sorted(breakdown.items(), key=lambda x: x[1]["cost"], reverse=True):
        table.add_row(agent, str(data["calls"]), f"${data['cost']:.2f}")

    console.print(table)


# ============================================================================
# Source Commands
# ============================================================================

@cli.group()
def sources() -> None:
    """Source management commands."""
    pass


@sources.command("list")
@click.option("--tier", type=int, help="Filter by tier (1-4)")
@click.option("--region", type=str, help="Filter by region")
def list_sources(tier: Optional[int], region: Optional[str]) -> None:
    """List configured sources."""
    from undertow.services.source_scorer import SOURCE_PROFILES, SourceTier

    table = Table(title="Source Profiles")
    table.add_column("Domain", style="cyan")
    table.add_column("Name")
    table.add_column("Tier")
    table.add_column("Reliability")
    table.add_column("Regions", max_width=30)

    tier_filter = SourceTier(tier) if tier else None

    for domain, profile in sorted(SOURCE_PROFILES.items()):
        if tier_filter and profile.tier != tier_filter:
            continue
        if region and region not in profile.regions:
            continue

        tier_style = {1: "green", 2: "cyan", 3: "yellow", 4: "red"}.get(profile.tier.value, "white")

        table.add_row(
            domain,
            profile.name,
            f"[{tier_style}]{profile.tier.value}[/{tier_style}]",
            f"{profile.reliability_score:.0%}",
            ", ".join(profile.regions[:3]) + ("..." if len(profile.regions) > 3 else ""),
        )

    console.print(table)
    console.print(f"\n[dim]Total: {len(SOURCE_PROFILES)} sources[/dim]")


@sources.command("score")
@click.argument("url")
def score_source(url: str) -> None:
    """Score a source URL."""
    from undertow.services.source_scorer import SourceScorer

    scorer = SourceScorer()
    result = scorer.score(url)

    console.print(f"\n[bold]Source Score: {url}[/bold]\n")

    table = Table()
    table.add_column("Metric", style="cyan")
    table.add_column("Score", justify="right")

    table.add_row("Overall", f"{result.overall_score:.0%}")
    table.add_row("Reliability", f"{result.reliability_score:.0%}")
    table.add_row("Depth", f"{result.depth_score:.0%}")
    table.add_row("Timeliness", f"{result.timeliness_score:.0%}")
    table.add_row("Tier", str(result.tier.value))
    table.add_row("Bias", result.bias_indicator.value)

    console.print(table)

    if result.notes:
        console.print(f"\n[dim]Note: {result.notes}[/dim]")


# ============================================================================
# Database Commands
# ============================================================================

@cli.group()
def db() -> None:
    """Database management commands."""
    pass


@db.command("migrate")
@click.option("--revision", type=str, default="head", help="Target revision")
def migrate_db(revision: str) -> None:
    """Run database migrations."""
    import subprocess

    console.print(f"[blue]Running migrations to {revision}...[/blue]")

    result = subprocess.run(
        ["alembic", "upgrade", revision],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        console.print("[green]✓ Migrations complete[/green]")
        if result.stdout:
            console.print(result.stdout)
    else:
        console.print(f"[red]✗ Migration failed[/red]")
        console.print(result.stderr)
        sys.exit(1)


@db.command("rollback")
@click.option("--revision", type=str, default="-1", help="Target revision")
def rollback_db(revision: str) -> None:
    """Rollback database migrations."""
    import subprocess

    console.print(f"[yellow]Rolling back to {revision}...[/yellow]")

    result = subprocess.run(
        ["alembic", "downgrade", revision],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        console.print("[green]✓ Rollback complete[/green]")
    else:
        console.print(f"[red]✗ Rollback failed[/red]")
        console.print(result.stderr)
        sys.exit(1)


# ============================================================================
# Server Commands
# ============================================================================

@cli.command("serve")
@click.option("--host", type=str, default="0.0.0.0", help="Host to bind")
@click.option("--port", type=int, default=8000, help="Port to bind")
@click.option("--reload", is_flag=True, help="Enable auto-reload")
def serve(host: str, port: int, reload: bool) -> None:
    """Start the API server."""
    import uvicorn

    console.print(f"[green]Starting server at http://{host}:{port}[/green]")

    uvicorn.run(
        "undertow.api.main:create_app",
        host=host,
        port=port,
        reload=reload,
        factory=True,
    )


@cli.command("worker")
@click.option("--concurrency", type=int, default=4, help="Number of worker processes")
@click.option("--queues", type=str, default="default", help="Comma-separated queue names")
def worker(concurrency: int, queues: str) -> None:
    """Start a Celery worker."""
    import subprocess

    console.print(f"[green]Starting Celery worker (concurrency={concurrency})...[/green]")

    subprocess.run([
        "celery",
        "-A", "undertow.tasks.celery_app",
        "worker",
        "--loglevel=info",
        f"--concurrency={concurrency}",
        f"-Q", queues,
    ])


# ============================================================================
# Seed Commands
# ============================================================================

@cli.group()
def seed() -> None:
    """Database seeding commands."""
    pass


@seed.command("all")
def seed_all() -> None:
    """Seed all initial data (zones, themes, sources)."""
    from undertow.infrastructure.seeders import get_all_zones, get_all_themes
    
    console.print("[blue]Seeding initial data...[/blue]")
    
    zones = get_all_zones()
    themes = get_all_themes()
    
    console.print(f"  [green]✓[/green] {len(zones)} zones loaded")
    console.print(f"  [green]✓[/green] {len(themes)} themes loaded")
    console.print("\n[green]Seeding complete![/green]")
    console.print("[dim]Note: Zone and theme data is loaded from memory. Use 'db migrate' to create database tables.[/dim]")


@seed.command("zones")
def seed_zones_cmd() -> None:
    """List all available zones."""
    from undertow.infrastructure.seeders import get_all_zones, get_zones_by_region
    
    regions = ["europe", "russia_eurasia", "mena", "africa", "south_asia", "east_asia", "southeast_asia", "oceania", "americas"]
    
    for region in regions:
        zones = get_zones_by_region(region)
        if zones:
            console.print(f"\n[bold cyan]{region.upper().replace('_', ' ')}[/bold cyan]")
            for zone in zones:
                console.print(f"  • {zone['id']}: {zone['name']}")
    
    total = len(get_all_zones())
    console.print(f"\n[dim]Total: {total} zones[/dim]")


# ============================================================================
# Benchmark Commands
# ============================================================================

@cli.group()
def bench() -> None:
    """Performance benchmark commands."""
    pass


@bench.command("quick")
def bench_quick() -> None:
    """Run quick benchmarks (no external dependencies)."""
    from undertow.infrastructure.benchmarks import Benchmark
    import json
    import time
    
    console.print("[blue]Running quick benchmarks...[/blue]\n")
    
    results = []
    
    # JSON serialization
    bench = Benchmark("json_serialize")
    test_data = {"articles": [{"id": i, "headline": f"Article {i}"} for i in range(100)]}
    
    for _ in range(1000):
        with bench.measure():
            json.dumps(test_data)
    
    result = bench.get_result()
    results.append(("JSON Serialize (100 items)", result))
    
    # String operations
    bench = Benchmark("string_ops")
    test_text = "Israel recognized Somaliland as an independent state. " * 100
    
    for _ in range(1000):
        with bench.measure():
            _ = test_text.lower().split()
    
    result = bench.get_result()
    results.append(("String Operations", result))
    
    # Display results
    table = Table(title="Quick Benchmark Results")
    table.add_column("Benchmark", style="cyan")
    table.add_column("Avg (ms)", justify="right")
    table.add_column("P95 (ms)", justify="right")
    table.add_column("P99 (ms)", justify="right")
    
    for name, r in results:
        table.add_row(
            name,
            f"{r.avg_time_ms:.3f}",
            f"{r.p95_ms:.3f}",
            f"{r.p99_ms:.3f}",
        )
    
    console.print(table)


@bench.command("embedding")
def bench_embedding() -> None:
    """Benchmark embedding generation (requires OpenAI API key)."""
    
    async def _run():
        from undertow.infrastructure.benchmarks import benchmark_embedding_latency
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Running embedding benchmark...", total=None)
            
            try:
                result = await benchmark_embedding_latency()
                progress.update(task, description="[green]Done![/green]")
                
                console.print(f"\n[bold]Embedding Benchmark Results[/bold]")
                console.print(f"  Iterations: {result.iterations}")
                console.print(f"  Avg: {result.avg_time_ms:.1f}ms")
                console.print(f"  P95: {result.p95_ms:.1f}ms")
                console.print(f"  P99: {result.p99_ms:.1f}ms")
            except Exception as e:
                progress.update(task, description=f"[red]Failed: {e}[/red]")
    
    asyncio.run(_run())


@bench.command("search")
def bench_search() -> None:
    """Benchmark vector search (requires database)."""
    
    async def _run():
        from undertow.infrastructure.benchmarks import benchmark_vector_search
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Running vector search benchmark...", total=None)
            
            try:
                result = await benchmark_vector_search()
                progress.update(task, description="[green]Done![/green]")
                
                console.print(f"\n[bold]Vector Search Benchmark Results[/bold]")
                console.print(f"  Iterations: {result.iterations}")
                console.print(f"  Avg: {result.avg_time_ms:.1f}ms")
                console.print(f"  P95: {result.p95_ms:.1f}ms")
                console.print(f"  P99: {result.p99_ms:.1f}ms")
            except Exception as e:
                progress.update(task, description=f"[red]Failed: {e}[/red]")
    
    asyncio.run(_run())


# ============================================================================
# Audit Commands
# ============================================================================

@cli.group()
def audit() -> None:
    """Audit log commands."""
    pass


@audit.command("recent")
@click.option("--limit", type=int, default=50, help="Number of events to show")
def audit_recent(limit: int) -> None:
    """Show recent audit events."""
    from undertow.infrastructure.audit import get_audit_logger
    
    logger = get_audit_logger()
    events = logger.get_recent_events(limit=limit)
    
    if not events:
        console.print("[dim]No audit events found[/dim]")
        return
    
    table = Table(title=f"Recent Audit Events (last {len(events)})")
    table.add_column("Time", style="dim")
    table.add_column("Action", style="cyan")
    table.add_column("Resource")
    table.add_column("Actor")
    table.add_column("Status")
    
    for event in reversed(events[-20:]):
        status = "[green]✓[/green]" if event.success else "[red]✗[/red]"
        table.add_row(
            event.timestamp.strftime("%H:%M:%S"),
            event.action.value,
            f"{event.resource_type}:{event.resource_id[:8] if event.resource_id else '-'}",
            event.actor or "-",
            status,
        )
    
    console.print(table)


@audit.command("stats")
def audit_stats() -> None:
    """Show audit statistics."""
    from undertow.infrastructure.audit import get_audit_logger, AuditAction
    
    logger = get_audit_logger()
    events = logger.get_recent_events(limit=1000)
    
    if not events:
        console.print("[dim]No audit events found[/dim]")
        return
    
    # Count by action
    by_action: dict[str, int] = {}
    for event in events:
        by_action[event.action.value] = by_action.get(event.action.value, 0) + 1
    
    table = Table(title="Audit Event Statistics")
    table.add_column("Action", style="cyan")
    table.add_column("Count", justify="right")
    
    for action, count in sorted(by_action.items(), key=lambda x: x[1], reverse=True):
        table.add_row(action, str(count))
    
    console.print(table)
    console.print(f"\n[dim]Total events: {len(events)}[/dim]")


if __name__ == "__main__":
    cli()

