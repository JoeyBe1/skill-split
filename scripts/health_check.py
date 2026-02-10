#!/usr/bin/env python3
"""
skill-split Health Check Script

Monitors system health and reports status.

Usage:
    python scripts/health_check.py
    python scripts/health_check.py --json
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any


def check_database(db_path: str) -> Dict[str, Any]:
    """Check database health."""
    checks = {}

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Database exists and accessible
        checks['accessible'] = True
        checks['path'] = db_path

        # Get file count
        cursor.execute("SELECT COUNT(*) FROM files")
        checks['file_count'] = cursor.fetchone()[0]

        # Get section count
        cursor.execute("SELECT COUNT(*) FROM sections")
        checks['section_count'] = cursor.fetchone()[0]

        # Get database size
        checks['size_bytes'] = Path(db_path).stat().st_size
        checks['size_mb'] = round(checks['size_bytes'] / (1024 * 1024), 2)

        # Check integrity
        cursor.execute("PRAGMA integrity_check")
        integrity_result = cursor.fetchone()[0]
        checks['integrity'] = integrity_result == 'ok'

        # Check FTS5 index
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sections_fts'")
        checks['fts5_enabled'] = cursor.fetchone() is not None

        conn.close()
        checks['status'] = 'healthy'

    except Exception as e:
        checks['status'] = 'unhealthy'
        checks['error'] = str(e)
        checks['accessible'] = False

    return checks


def check_performance(db_path: str) -> Dict[str, Any]:
    """Check performance metrics."""
    metrics = {}

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Query performance test
        start = datetime.now()
        cursor.execute("SELECT COUNT(*) FROM sections WHERE content LIKE '%test%'")
        cursor.fetchone()
        end = datetime.now()

        query_time_ms = (end - start).total_seconds() * 1000
        metrics['query_time_ms'] = round(query_time_ms, 2)
        metrics['query_performance'] = 'good' if query_time_ms < 100 else 'slow'

        # Cache hit rate (if implemented)
        metrics['cache_enabled'] = False  # TODO: check from config

        conn.close()

    except Exception as e:
        metrics['error'] = str(e)
        metrics['status'] = 'error'

    return metrics


def check_indexes(db_path: str) -> Dict[str, Any]:
    """Check database indexes."""
    index_info = {}

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get all indexes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = cursor.fetchall()

        index_info['total_indexes'] = len(indexes)
        index_info['indexes'] = [idx[0] for idx in indexes]

        # Check for critical indexes
        critical = ['idx_sections_file', 'idx_sections_parent', 'idx_navigation']
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        existing = {idx[0] for idx in cursor.fetchall()}

        index_info['critical_indexes_present'] = all(
            any(crit in existing for crit in critical)
            for crit in ['idx_sections_file', 'idx_sections_parent']
        )

        conn.close()

    except Exception as e:
        index_info['error'] = str(e)

    return index_info


def generate_report(checks: Dict) -> str:
    """Generate human-readable report."""
    report = []

    report.append("=" * 50)
    report.append("skill-split Health Check")
    report.append("=" * 50)
    report.append(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")

    # Database Status
    report.append("📊 Database Status")
    report.append("-" * 30)

    if checks['database']['status'] == 'healthy':
        report.append(f"✅ Status: {checks['database']['status'].upper()}")
        report.append(f"📁 Files: {checks['database']['file_count']:,}")
        report.append(f"📄 Sections: {checks['database']['section_count']:,}")
        report.append(f"💾 Size: {checks['database']['size_mb']} MB")
        report.append(f"🔒 Integrity: {'PASS' if checks['database']['integrity'] else 'FAIL'}")
        report.append(f"🔍 FTS5: {'Enabled' if checks['database']['fts5_enabled'] else 'Disabled'}")
    else:
        report.append(f"❌ Status: {checks['database']['status'].upper()}")
        report.append(f"⚠️  Error: {checks['database'].get('error', 'Unknown')}")

    report.append("")

    # Performance
    report.append("⚡ Performance")
    report.append("-" * 30)

    if 'error' not in checks['performance']:
        report.append(f"🕐 Query Time: {checks['performance']['query_time_ms']} ms")
        report.append(f"📈 Performance: {checks['performance']['query_performance'].upper()}")
    else:
        report.append(f"⚠️  Error: {checks['performance']['error']}")

    report.append("")

    # Indexes
    report.append("🗂️  Indexes")
    report.append("-" * 30)

    if 'error' not in checks['indexes']:
        report.append(f"📊 Total Indexes: {checks['indexes']['total_indexes']}")
        report.append(f"🔑 Critical: {'✅ Present' if checks['indexes']['critical_indexes_present'] else '⚠️  Missing'}")

    report.append("")
    report.append("=" * 50)

    return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(
        description="Health check for skill-split"
    )

    parser.add_argument(
        "--db",
        default="skill_split.db",
        help="Database path (default: skill_split.db)"
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON format"
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output"
    )

    args = parser.parse_args()

    # Run all checks
    results = {
        'timestamp': datetime.now().isoformat(),
        'database': check_database(args.db),
        'performance': check_performance(args.db),
        'indexes': check_indexes(args.db)
    }

    # Determine overall health
    results['overall_status'] = (
        'healthy' if results['database']['status'] == 'healthy'
        else 'unhealthy'
    )

    # Output
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(generate_report(results))

    # Exit code
    sys.exit(0 if results['overall_status'] == 'healthy' else 1)


if __name__ == "__main__":
    main()
