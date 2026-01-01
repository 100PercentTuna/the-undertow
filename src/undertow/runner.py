"""
Main runner for The Undertow.

Runs the daily pipeline on schedule, fully automated.
No human review required - publishes automatically.
"""

import asyncio
import signal
import sys
from datetime import datetime, time, timedelta
from typing import NoReturn

import structlog

from undertow.config import get_settings
from undertow.core.pipeline.simple_orchestrator import SimpleOrchestrator
from undertow.services.newsletter import NewsletterService

logger = structlog.get_logger(__name__)


class UndertowRunner:
    """
    Automated runner for The Undertow.
    
    Runs the pipeline daily at the configured time and sends the newsletter.
    Completely autonomous - no human intervention required.
    """
    
    def __init__(self) -> None:
        self._settings = get_settings()
        self._running = True
        self._orchestrator = SimpleOrchestrator()
        self._newsletter = NewsletterService()
    
    async def run_forever(self) -> NoReturn:
        """Run the scheduler loop forever."""
        logger.info(
            "undertow_runner_started",
            scheduled_hour=self._settings.pipeline_start_hour,
            scheduled_minute=getattr(self._settings, 'pipeline_start_minute', 30),
        )
        
        # Set up signal handlers
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, self._handle_shutdown)
        
        while self._running:
            now = datetime.utcnow()
            next_run = self._get_next_run_time(now)
            
            wait_seconds = (next_run - now).total_seconds()
            
            logger.info(
                "waiting_for_next_run",
                next_run=next_run.isoformat(),
                wait_hours=wait_seconds / 3600,
            )
            
            # Wait until next run time
            try:
                await asyncio.sleep(wait_seconds)
            except asyncio.CancelledError:
                break
            
            if self._running:
                await self._run_daily_pipeline()
    
    def _get_next_run_time(self, now: datetime) -> datetime:
        """Calculate the next run time."""
        run_hour = self._settings.pipeline_start_hour
        run_minute = getattr(self._settings, 'pipeline_start_minute', 30)
        
        # Today's run time
        today_run = now.replace(
            hour=run_hour,
            minute=run_minute,
            second=0,
            microsecond=0,
        )
        
        # If we've passed today's run time, schedule for tomorrow
        if now >= today_run:
            return today_run + timedelta(days=1)
        
        return today_run
    
    async def _run_daily_pipeline(self) -> None:
        """Run the complete daily pipeline."""
        run_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        logger.info("daily_pipeline_started", run_id=run_id)
        
        start_time = datetime.utcnow()
        
        try:
            # Run the simplified pipeline
            result = await self._orchestrator.run_daily()
            
            if result.success:
                # Send newsletter automatically
                await self._newsletter.send_daily_newsletter(
                    articles=result.articles,
                    recipients=self._get_recipients(),
                )
                
                duration = (datetime.utcnow() - start_time).total_seconds()
                
                logger.info(
                    "daily_pipeline_completed",
                    run_id=run_id,
                    articles=len(result.articles),
                    cost=result.total_cost,
                    duration_minutes=duration / 60,
                )
            else:
                logger.error(
                    "daily_pipeline_failed",
                    run_id=run_id,
                    error=result.error,
                )
        
        except Exception as e:
            logger.exception(
                "daily_pipeline_exception",
                run_id=run_id,
                error=str(e),
            )
    
    def _get_recipients(self) -> list[str]:
        """Get newsletter recipients from config."""
        recipients_str = getattr(self._settings, 'newsletter_recipients', '')
        if not recipients_str:
            return []
        return [r.strip() for r in recipients_str.split(',') if r.strip()]
    
    def _handle_shutdown(self, signum, frame) -> None:
        """Handle shutdown signals."""
        logger.info("shutdown_signal_received", signal=signum)
        self._running = False


async def main() -> None:
    """Main entry point."""
    runner = UndertowRunner()
    await runner.run_forever()


if __name__ == "__main__":
    asyncio.run(main())

