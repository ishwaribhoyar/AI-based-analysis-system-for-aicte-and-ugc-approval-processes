"""
Cleanup Cron Job for scheduled database maintenance.
Runs automatically to keep the database clean and performant.

Usage:
    Schedule with system scheduler (cron, Windows Task Scheduler, APScheduler)
    or call directly: python -m cron.cleanup_cron
"""

import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_daily_cleanup():
    """
    Run daily cleanup tasks:
    1. Purge invalid batches
    2. Remove duplicate institutions
    3. Compact database
    """
    logger.info(f"Starting daily cleanup at {datetime.now().isoformat()}")
    
    from utils.db_cleaner import (
        purge_invalid_batches,
        remove_duplicate_institutions,
        compact_database
    )
    
    results = {}
    
    # 1. Purge invalid batches
    try:
        logger.info("Step 1: Purging invalid batches...")
        results['purge'] = purge_invalid_batches()
        logger.info(f"Purged {results['purge']['batches_deleted']} invalid batches")
    except Exception as e:
        logger.error(f"Purge failed: {e}")
        results['purge'] = {'error': str(e)}
    
    # 2. Remove duplicates
    try:
        logger.info("Step 2: Removing duplicate institutions...")
        results['dedupe'] = remove_duplicate_institutions()
        logger.info(f"Removed {results['dedupe']['duplicates_removed']} duplicates")
    except Exception as e:
        logger.error(f"Deduplication failed: {e}")
        results['dedupe'] = {'error': str(e)}
    
    # 3. Compact database
    try:
        logger.info("Step 3: Compacting database...")
        results['compact'] = compact_database()
        logger.info("Database compacted successfully")
    except Exception as e:
        logger.error(f"Compaction failed: {e}")
        results['compact'] = {'error': str(e)}
    
    logger.info(f"Daily cleanup completed at {datetime.now().isoformat()}")
    logger.info(f"Results: {results}")
    
    return results


def run_weekly_cleanup():
    """
    Run weekly cleanup tasks (more thorough):
    1. All daily tasks
    2. Remove redundant KPI entries
    3. Clean up old cache entries
    """
    logger.info("Starting weekly cleanup...")
    
    # Run daily cleanup first
    results = run_daily_cleanup()
    
    # Additional weekly tasks
    from utils.db_cleaner import remove_redundant_kpi_entries
    from config.database import get_db, close_db, PipelineCache
    from datetime import datetime, timezone, timedelta
    
    # Clean redundant KPIs
    try:
        logger.info("Weekly: Cleaning redundant KPI entries...")
        results['kpi_cleanup'] = remove_redundant_kpi_entries()
    except Exception as e:
        logger.error(f"KPI cleanup failed: {e}")
        results['kpi_cleanup'] = {'error': str(e)}
    
    # Clean old cache entries
    try:
        logger.info("Weekly: Cleaning old cache entries...")
        db = get_db()
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        deleted = db.query(PipelineCache).filter(
            PipelineCache.created_at < cutoff
        ).delete()
        db.commit()
        results['cache_cleanup'] = {'deleted': deleted}
        close_db(db)
    except Exception as e:
        logger.error(f"Cache cleanup failed: {e}")
        results['cache_cleanup'] = {'error': str(e)}
    
    logger.info(f"Weekly cleanup completed: {results}")
    return results


# For APScheduler integration
def setup_scheduler():
    """
    Setup APScheduler for automated cleanup jobs.
    Call this from your main application startup.
    """
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger
        
        scheduler = BackgroundScheduler()
        
        # Daily cleanup at 3:00 AM
        scheduler.add_job(
            run_daily_cleanup,
            CronTrigger(hour=3, minute=0),
            id='daily_cleanup',
            name='Daily database cleanup',
            replace_existing=True
        )
        
        # Weekly cleanup on Sunday at 4:00 AM
        scheduler.add_job(
            run_weekly_cleanup,
            CronTrigger(day_of_week='sun', hour=4, minute=0),
            id='weekly_cleanup',
            name='Weekly database cleanup',
            replace_existing=True
        )
        
        scheduler.start()
        logger.info("Cleanup scheduler started successfully")
        return scheduler
        
    except ImportError:
        logger.warning("APScheduler not installed. Automated cleanup disabled.")
        logger.warning("Install with: pip install apscheduler")
        return None


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'weekly':
        run_weekly_cleanup()
    else:
        run_daily_cleanup()
