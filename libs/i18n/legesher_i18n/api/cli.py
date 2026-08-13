"""CLI commands for translation API usage monitoring."""

import argparse
import sys
from datetime import datetime, timedelta

from .cache import RedisCache, SQLiteCache
from .dashboard import DashboardGenerator
from .usage_tracker import UsageTracker


def format_bytes(bytes_val: int) -> str:
    """Format bytes to human-readable string."""
    for unit in ["B", "KB", "MB", "GB"]:
        if bytes_val < 1024:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024
    return f"{bytes_val:.2f} TB"


def format_currency(amount: float | None) -> str:
    """Format currency to USD, or say so when the price is unknown."""
    if amount is None:
        return "unknown"
    return f"${amount:.2f}"


def cmd_usage_stats(args):
    """Display usage statistics."""
    tracker = UsageTracker(db_path=args.db_path)

    # Parse date range
    start_date = None
    end_date = None

    if args.days:
        start_date = datetime.now() - timedelta(days=args.days)
    elif args.start_date:
        start_date = datetime.fromisoformat(args.start_date)

    if args.end_date:
        end_date = datetime.fromisoformat(args.end_date)

    # Get stats
    stats = tracker.get_usage_stats(start_date, end_date)

    # Display summary
    period = stats.get("period", {})
    total = stats.get("total", {})

    print("\n=== Translation API Usage Statistics ===\n")
    print(
        f"Period: {period.get('start', 'N/A')[:10]} to {period.get('end', 'N/A')[:10]}"
    )
    print()

    # Total stats
    print("Total Usage:")
    print(f"  Requests:        {total.get('requests', 0):,}")
    print(f"  Characters:      {total.get('characters', 0):,}")
    print(f"  Cost:            {format_currency(total.get('cost_usd', 0.0))}")
    print(f"  Cache Hit Rate:  {total.get('cache_hit_rate', 0.0):.1f}%")
    print()

    # Per-provider breakdown
    by_provider = stats.get("by_provider", [])
    if by_provider:
        print("By Provider:")
        for p in by_provider:
            print(
                f"  {p['provider']:<15} {p['requests']:>8,} requests  "
                f"{p['characters']:>12,} chars  {format_currency(p['cost_usd']):>10}"
            )
        print()

    # Top language pairs
    top_pairs = stats.get("top_language_pairs", [])
    if top_pairs:
        print("Top Language Pairs:")
        for p in top_pairs[:10]:
            print(
                f"  {p['pair']:<10} {p['requests']:>8,} requests  {p['characters']:>12,} chars"
            )
        print()

    # Daily trend
    if args.verbose:
        daily_trend = stats.get("daily_trend", [])
        if daily_trend:
            print("Daily Trend (Last 7 Days):")
            for d in reversed(daily_trend):
                print(
                    f"  {d['date']}  {d['requests']:>6,} requests  "
                    f"{format_currency(d['cost_usd']):>8}"
                )
            print()


def cmd_cache_stats(args):
    """Display cache statistics."""
    # Determine cache type
    if args.redis:
        cache = RedisCache(host=args.redis_host, port=args.redis_port)
        cache_type = "Redis"
    else:
        cache = SQLiteCache(db_path=args.cache_db_path)
        cache_type = "SQLite"

    stats = cache.get_stats()

    print(f"\n=== {cache_type} Cache Statistics ===\n")

    if "error" in stats:
        print(f"Error: {stats['error']}")
        return

    # Common stats
    print(f"Backend:        {stats.get('backend', 'unknown')}")
    print(f"Total Entries:  {stats.get('total_entries', 0):,}")
    print(
        f"TTL:            {stats.get('ttl_seconds', 0):,} seconds ({stats.get('ttl_seconds', 0) / 86400:.1f} days)"
    )
    print()

    # SQLite-specific stats
    if "db_size_mb" in stats:
        print(f"Database Size:  {stats['db_size_mb']:.2f} MB")
        by_provider = stats.get("by_provider", {})
        if by_provider:
            print("\nEntries by Provider:")
            for provider, count in by_provider.items():
                print(f"  {provider:<15} {count:>8,}")

    # Redis-specific stats
    if "hits" in stats:
        print(f"Cache Hits:     {stats['hits']:,}")
        print(f"Cache Misses:   {stats['misses']:,}")
        print(f"Hit Rate:       {stats['hit_rate']:.1f}%")
        print(f"Memory Used:    {stats['memory_used_mb']:.2f} MB")

    print()


def cmd_clear_cache(args):
    """Clear the translation cache."""
    # Determine cache type
    if args.redis:
        cache = RedisCache(host=args.redis_host, port=args.redis_port)
        cache_type = "Redis"
    else:
        cache = SQLiteCache(db_path=args.cache_db_path)
        cache_type = "SQLite"

    # Confirm if not forced
    if not args.force:
        response = input(f"Clear all {cache_type} cache entries? (y/N): ")
        if response.lower() != "y":
            print("Aborted.")
            return

    deleted = cache.clear()
    print(f"Cleared {deleted:,} cache entries from {cache_type}.")


def cmd_cleanup_expired(args):
    """Cleanup expired cache entries (SQLite only)."""
    cache = SQLiteCache(db_path=args.cache_db_path)

    deleted = cache.cleanup_expired()
    if deleted > 0:
        print(f"Cleaned up {deleted:,} expired cache entries.")
    else:
        print("No expired entries found.")


def cmd_export_csv(args):
    """Export usage data to CSV."""
    tracker = UsageTracker(db_path=args.db_path)

    # Parse date range
    start_date = None
    end_date = None

    if args.days:
        start_date = datetime.now() - timedelta(days=args.days)
    elif args.start_date:
        start_date = datetime.fromisoformat(args.start_date)

    if args.end_date:
        end_date = datetime.fromisoformat(args.end_date)

    # Export
    tracker.export_csv(args.output, start_date, end_date)
    print(f"Exported usage data to {args.output}")


def cmd_generate_dashboard(args):
    """Generate HTML usage dashboard."""
    tracker = UsageTracker(db_path=args.db_path)
    generator = DashboardGenerator(tracker)

    # Parse date range
    start_date = None
    end_date = None

    if args.days:
        start_date = datetime.now() - timedelta(days=args.days)
    elif args.start_date:
        start_date = datetime.fromisoformat(args.start_date)

    if args.end_date:
        end_date = datetime.fromisoformat(args.end_date)

    # Generate
    generator.generate(
        args.output,
        start_date=start_date,
        end_date=end_date,
        title=args.title,
    )
    print(f"Generated dashboard: {args.output}")


def cmd_recent_usage(args):
    """Display recent translation requests."""
    tracker = UsageTracker(db_path=args.db_path)

    records = tracker.get_recent_usage(limit=args.limit)

    print(f"\n=== Recent Translation Requests (Last {len(records)}) ===\n")

    for record in records:
        cached_marker = "[CACHED]" if record.cached else ""
        print(
            f"{record.timestamp.strftime('%Y-%m-%d %H:%M:%S')}  "
            f"{record.provider:<12}  "
            f"{record.source_lang}->{record.target_lang}  "
            f"{record.characters:>6,} chars  "
            f"{format_currency(record.cost_usd):>8}  "
            f"{cached_marker}"
        )

    print()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Legesher Translation API Usage Monitoring CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Usage stats command
    stats_parser = subparsers.add_parser("stats", help="Display usage statistics")
    stats_parser.add_argument(
        "--db-path",
        default=".legesher/usage.db",
        help="Usage database path (default: .legesher/usage.db)",
    )
    stats_parser.add_argument(
        "--days", type=int, help="Show stats for last N days (default: 30)"
    )
    stats_parser.add_argument("--start-date", help="Start date (ISO format)")
    stats_parser.add_argument("--end-date", help="End date (ISO format)")
    stats_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Show detailed information"
    )
    stats_parser.set_defaults(func=cmd_usage_stats)

    # Cache stats command
    cache_parser = subparsers.add_parser("cache-stats", help="Display cache statistics")
    cache_parser.add_argument(
        "--cache-db-path",
        default=".legesher/cache.db",
        help="Cache database path (default: .legesher/cache.db)",
    )
    cache_parser.add_argument("--redis", action="store_true", help="Use Redis cache")
    cache_parser.add_argument("--redis-host", default="localhost", help="Redis host")
    cache_parser.add_argument("--redis-port", type=int, default=6379, help="Redis port")
    cache_parser.set_defaults(func=cmd_cache_stats)

    # Clear cache command
    clear_parser = subparsers.add_parser("clear-cache", help="Clear translation cache")
    clear_parser.add_argument(
        "--cache-db-path",
        default=".legesher/cache.db",
        help="Cache database path (default: .legesher/cache.db)",
    )
    clear_parser.add_argument("--redis", action="store_true", help="Use Redis cache")
    clear_parser.add_argument("--redis-host", default="localhost", help="Redis host")
    clear_parser.add_argument("--redis-port", type=int, default=6379, help="Redis port")
    clear_parser.add_argument(
        "-f", "--force", action="store_true", help="Skip confirmation"
    )
    clear_parser.set_defaults(func=cmd_clear_cache)

    # Cleanup expired command
    cleanup_parser = subparsers.add_parser(
        "cleanup-expired", help="Cleanup expired cache entries (SQLite)"
    )
    cleanup_parser.add_argument(
        "--cache-db-path",
        default=".legesher/cache.db",
        help="Cache database path (default: .legesher/cache.db)",
    )
    cleanup_parser.set_defaults(func=cmd_cleanup_expired)

    # Export CSV command
    export_parser = subparsers.add_parser("export-csv", help="Export usage data to CSV")
    export_parser.add_argument("output", help="Output CSV file path")
    export_parser.add_argument(
        "--db-path",
        default=".legesher/usage.db",
        help="Usage database path (default: .legesher/usage.db)",
    )
    export_parser.add_argument(
        "--days", type=int, help="Export last N days (default: 30)"
    )
    export_parser.add_argument("--start-date", help="Start date (ISO format)")
    export_parser.add_argument("--end-date", help="End date (ISO format)")
    export_parser.set_defaults(func=cmd_export_csv)

    # Generate dashboard command
    dashboard_parser = subparsers.add_parser(
        "dashboard", help="Generate HTML usage dashboard"
    )
    dashboard_parser.add_argument("output", help="Output HTML file path")
    dashboard_parser.add_argument(
        "--db-path",
        default=".legesher/usage.db",
        help="Usage database path (default: .legesher/usage.db)",
    )
    dashboard_parser.add_argument(
        "--days", type=int, help="Dashboard for last N days (default: 30)"
    )
    dashboard_parser.add_argument("--start-date", help="Start date (ISO format)")
    dashboard_parser.add_argument("--end-date", help="End date (ISO format)")
    dashboard_parser.add_argument(
        "--title",
        default="Legesher Translation API Usage Dashboard",
        help="Dashboard title",
    )
    dashboard_parser.set_defaults(func=cmd_generate_dashboard)

    # Recent usage command
    recent_parser = subparsers.add_parser(
        "recent", help="Display recent translation requests"
    )
    recent_parser.add_argument(
        "--db-path",
        default=".legesher/usage.db",
        help="Usage database path (default: .legesher/usage.db)",
    )
    recent_parser.add_argument(
        "--limit", type=int, default=20, help="Number of recent requests (default: 20)"
    )
    recent_parser.set_defaults(func=cmd_recent_usage)

    # Parse and execute
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Execute command
    try:
        args.func(args)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
