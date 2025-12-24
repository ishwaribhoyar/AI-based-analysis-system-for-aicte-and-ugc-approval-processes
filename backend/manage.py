#!/usr/bin/env python
"""
Management CLI for database operations.
Provides commands for cleaning, loading historical data, and deduplication.

Usage:
    python manage.py clean_db
    python manage.py load_historical_data
    python manage.py dedupe_batches
    python manage.py full_cleanup
"""

import sys
import argparse
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def cmd_clean_db():
    """Purge invalid batches from database."""
    from utils.db_cleaner import purge_invalid_batches
    
    logger.info("Starting database cleanup...")
    result = purge_invalid_batches()
    
    print("\n📊 Cleanup Results:")
    print(f"  Batches deleted: {result['batches_deleted']}")
    print(f"  Blocks deleted: {result['blocks_deleted']}")
    print(f"  Files deleted: {result['files_deleted']}")
    print(f"  Compliance flags deleted: {result['compliance_flags_deleted']}")
    print(f"  Classifications deleted: {result['classifications_deleted']}")
    print(f"  Required docs deleted: {result['required_docs_deleted']}")
    print("\n✅ Cleanup complete!")


def cmd_load_historical_data():
    """Load historical KPI benchmarks into database."""
    from data.historical_kpi_loader import load_historical_kpis_into_db
    
    logger.info("Loading historical KPI data...")
    result = load_historical_kpis_into_db()
    
    print("\n📊 Historical Data Load Results:")
    print(f"  Years loaded: {result['loaded']}")
    print(f"  Years updated: {result['updated']}")
    print(f"  Years skipped (>10 years old): {result['skipped']}")
    print("\n✅ Historical data loaded!")


def cmd_dedupe_batches():
    """Remove duplicate institutions from database."""
    from utils.db_cleaner import remove_duplicate_institutions
    
    logger.info("Removing duplicate batches...")
    result = remove_duplicate_institutions()
    
    print("\n📊 Deduplication Results:")
    print(f"  Duplicates removed: {result['duplicates_removed']}")
    print(f"  Batches kept: {result['batches_kept']}")
    print("\n✅ Deduplication complete!")


def cmd_full_cleanup():
    """Run all cleanup operations."""
    from utils.db_cleaner import run_full_cleanup
    
    logger.info("Running full database cleanup...")
    result = run_full_cleanup()
    
    print("\n📊 Full Cleanup Results:")
    print("\n1. Purge Invalid Batches:")
    print(f"   Batches deleted: {result['purge']['batches_deleted']}")
    print(f"   Blocks deleted: {result['purge']['blocks_deleted']}")
    
    print("\n2. Deduplication:")
    print(f"   Duplicates removed: {result['dedupe']['duplicates_removed']}")
    
    print("\n3. KPI Cleanup:")
    print(f"   Batches cleaned: {result['kpi_cleanup']['batches_cleaned']}")
    
    print("\n4. Database Compaction:")
    print(f"   Status: {result['compact']['status']}")
    
    print("\n✅ Full cleanup complete!")


def cmd_compact_db():
    """Compact SQLite database to reduce file size."""
    from utils.db_cleaner import compact_database
    
    logger.info("Compacting database...")
    result = compact_database()
    
    print(f"\n📊 Compaction Result: {result['status']}")
    print("✅ Database compacted!")


def cmd_show_stats():
    """Show database statistics."""
    from config.database import get_db, close_db, Batch, Block, File
    
    db = get_db()
    try:
        batch_count = db.query(Batch).count()
        block_count = db.query(Block).count()
        file_count = db.query(File).count()
        
        completed = db.query(Batch).filter(Batch.status == 'completed').count()
        failed = db.query(Batch).filter(Batch.status == 'failed').count()
        
        print("\n📊 Database Statistics:")
        print(f"  Total batches: {batch_count}")
        print(f"    - Completed: {completed}")
        print(f"    - Failed: {failed}")
        print(f"    - Other: {batch_count - completed - failed}")
        print(f"  Total blocks: {block_count}")
        print(f"  Total files: {file_count}")
        print(f"  Avg blocks per batch: {block_count / batch_count:.1f if batch_count else 0}")
    finally:
        close_db(db)


def main():
    parser = argparse.ArgumentParser(
        description='Database Management CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python manage.py clean_db          - Remove invalid batches
  python manage.py load_historical   - Load historical KPI data
  python manage.py dedupe            - Remove duplicates
  python manage.py full_cleanup      - Run all cleanup operations
  python manage.py stats             - Show database statistics
        """
    )
    
    parser.add_argument(
        'command',
        choices=['clean_db', 'load_historical', 'dedupe', 'full_cleanup', 'compact', 'stats'],
        help='Command to execute'
    )
    
    args = parser.parse_args()
    
    commands = {
        'clean_db': cmd_clean_db,
        'load_historical': cmd_load_historical_data,
        'dedupe': cmd_dedupe_batches,
        'full_cleanup': cmd_full_cleanup,
        'compact': cmd_compact_db,
        'stats': cmd_show_stats,
    }
    
    try:
        commands[args.command]()
    except Exception as e:
        logger.error(f"Command failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
