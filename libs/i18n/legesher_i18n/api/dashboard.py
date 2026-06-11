"""Usage dashboard generator for translation API analytics."""

import logging
from datetime import datetime
from pathlib import Path

from .usage_tracker import UsageTracker

logger = logging.getLogger(__name__)


class DashboardGenerator:
    """
    Generate HTML dashboard for translation usage analytics.

    Creates interactive HTML reports with:
    - Cost breakdown by provider
    - Usage trends over time
    - Most translated language pairs
    - Cache effectiveness metrics
    - Character/request statistics

    Usage:
        from legesher_i18n.api import UsageTracker, DashboardGenerator

        tracker = UsageTracker()
        dashboard = DashboardGenerator(tracker)
        dashboard.generate("usage_report.html")
    """

    def __init__(self, usage_tracker: UsageTracker):
        """
        Initialize dashboard generator.

        Args:
            usage_tracker: UsageTracker instance
        """
        self.usage_tracker = usage_tracker

    def generate(
        self,
        output_path: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        title: str = "Legesher Translation API Usage Dashboard",
    ):
        """
        Generate HTML dashboard.

        Args:
            output_path: Output HTML file path
            start_date: Start of period (default: 30 days ago)
            end_date: End of period (default: now)
            title: Dashboard title
        """
        # Get usage stats
        stats = self.usage_tracker.get_usage_stats(start_date, end_date)

        # Generate HTML
        html = self._generate_html(stats, title)

        # Write to file
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(html, encoding="utf-8")

        logger.info(f"Dashboard generated: {output_path}")

    def _generate_html(self, stats: dict, title: str) -> str:
        """Generate HTML dashboard content."""
        period = stats.get("period", {})
        total = stats.get("total", {})
        by_provider = stats.get("by_provider", [])
        top_pairs = stats.get("top_language_pairs", [])
        daily_trend = stats.get("daily_trend", [])

        # Format dates
        start = period.get("start", "")[:10]
        end = period.get("end", "")[:10]

        # Total statistics
        total_requests = total.get("requests", 0)
        total_chars = total.get("characters", 0)
        total_cost = total.get("cost_usd", 0.0)
        cache_hit_rate = total.get("cache_hit_rate", 0.0)

        # Provider data for charts
        provider_labels = [p["provider"] for p in by_provider]
        provider_requests = [p["requests"] for p in by_provider]
        provider_costs = [p["cost_usd"] for p in by_provider]

        # Language pair data
        pair_labels = [p["pair"] for p in top_pairs]
        pair_requests = [p["requests"] for p in top_pairs]

        # Daily trend data
        daily_labels = [d["date"] for d in reversed(daily_trend)]
        daily_requests = [d["requests"] for d in reversed(daily_trend)]

        # Generate HTML
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js" integrity="sha384-e6nUZLBkQ86NJ6TVVKAeSaK8jWa3NhkYWZFomE39AvDbQWeie9PlQqM3pmYW5d1g" crossorigin="anonymous"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #f5f7fa;
            color: #2c3e50;
            padding: 20px;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}

        header {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}

        h1 {{
            color: #2c3e50;
            margin-bottom: 10px;
        }}

        .period {{
            color: #7f8c8d;
            font-size: 14px;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .stat-card {{
            background: white;
            padding: 25px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}

        .stat-label {{
            font-size: 14px;
            color: #7f8c8d;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 10px;
        }}

        .stat-value {{
            font-size: 32px;
            font-weight: 600;
            color: #2c3e50;
        }}

        .stat-unit {{
            font-size: 16px;
            color: #7f8c8d;
            margin-left: 5px;
        }}

        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 30px;
            margin-bottom: 30px;
        }}

        .chart-card {{
            background: white;
            padding: 25px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}

        .chart-title {{
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 20px;
            color: #2c3e50;
        }}

        .chart-container {{
            position: relative;
            height: 300px;
        }}

        .provider-table {{
            background: white;
            padding: 25px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
        }}

        th {{
            text-align: left;
            padding: 12px;
            background: #f8f9fa;
            font-weight: 600;
            color: #2c3e50;
            border-bottom: 2px solid #e9ecef;
        }}

        td {{
            padding: 12px;
            border-bottom: 1px solid #e9ecef;
        }}

        tr:hover {{
            background: #f8f9fa;
        }}

        .cost {{
            color: #e74c3c;
            font-weight: 600;
        }}

        .cache-badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
        }}

        .cache-good {{
            background: #d4edda;
            color: #155724;
        }}

        .cache-medium {{
            background: #fff3cd;
            color: #856404;
        }}

        .cache-poor {{
            background: #f8d7da;
            color: #721c24;
        }}

        footer {{
            text-align: center;
            color: #7f8c8d;
            padding: 20px;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{title}</h1>
            <div class="period">Period: {start} to {end}</div>
        </header>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Total Requests</div>
                <div class="stat-value">{total_requests:,}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Total Characters</div>
                <div class="stat-value">{total_chars:,}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Total Cost</div>
                <div class="stat-value cost">${total_cost:.2f}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Cache Hit Rate</div>
                <div class="stat-value">{cache_hit_rate:.1f}<span class="stat-unit">%</span></div>
            </div>
        </div>

        <div class="charts-grid">
            <div class="chart-card">
                <div class="chart-title">Requests by Provider</div>
                <div class="chart-container">
                    <canvas id="providerRequestsChart"></canvas>
                </div>
            </div>

            <div class="chart-card">
                <div class="chart-title">Cost by Provider</div>
                <div class="chart-container">
                    <canvas id="providerCostsChart"></canvas>
                </div>
            </div>

            <div class="chart-card">
                <div class="chart-title">Daily Requests Trend (Last 7 Days)</div>
                <div class="chart-container">
                    <canvas id="dailyTrendChart"></canvas>
                </div>
            </div>

            <div class="chart-card">
                <div class="chart-title">Top Language Pairs</div>
                <div class="chart-container">
                    <canvas id="languagePairsChart"></canvas>
                </div>
            </div>
        </div>

        <div class="provider-table">
            <div class="chart-title">Provider Breakdown</div>
            <table>
                <thead>
                    <tr>
                        <th>Provider</th>
                        <th>Requests</th>
                        <th>Characters</th>
                        <th>Cost (USD)</th>
                    </tr>
                </thead>
                <tbody>
"""

        # Add provider rows
        for provider in by_provider:
            html += f"""                    <tr>
                        <td>{provider["provider"]}</td>
                        <td>{provider["requests"]:,}</td>
                        <td>{provider["characters"]:,}</td>
                        <td class="cost">${provider["cost_usd"]:.2f}</td>
                    </tr>
"""

        html += (
            """                </tbody>
            </table>
        </div>

        <footer>
            <p>Generated by Legesher Translation API Dashboard</p>
            <p>Generated at: """
            + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            + """</p>
        </footer>
    </div>

    <script>
        // Chart configuration
        const chartConfig = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'bottom'
                }
            }
        };

        // Provider Requests Chart
        new Chart(document.getElementById('providerRequestsChart'), {
            type: 'doughnut',
            data: {
                labels: """
            + str(provider_labels)
            + """,
                datasets: [{
                    data: """
            + str(provider_requests)
            + """,
                    backgroundColor: [
                        '#3498db',
                        '#2ecc71',
                        '#f39c12',
                        '#e74c3c',
                        '#9b59b6'
                    ]
                }]
            },
            options: chartConfig
        });

        // Provider Costs Chart
        new Chart(document.getElementById('providerCostsChart'), {
            type: 'doughnut',
            data: {
                labels: """
            + str(provider_labels)
            + """,
                datasets: [{
                    data: """
            + str(provider_costs)
            + """,
                    backgroundColor: [
                        '#e74c3c',
                        '#c0392b',
                        '#e67e22',
                        '#d35400',
                        '#8e44ad'
                    ]
                }]
            },
            options: chartConfig
        });

        // Daily Trend Chart
        new Chart(document.getElementById('dailyTrendChart'), {
            type: 'line',
            data: {
                labels: """
            + str(daily_labels)
            + """,
                datasets: [{
                    label: 'Requests',
                    data: """
            + str(daily_requests)
            + """,
                    borderColor: '#3498db',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                ...chartConfig,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });

        // Language Pairs Chart
        new Chart(document.getElementById('languagePairsChart'), {
            type: 'bar',
            data: {
                labels: """
            + str(pair_labels)
            + """,
                datasets: [{
                    label: 'Requests',
                    data: """
            + str(pair_requests)
            + """,
                    backgroundColor: '#2ecc71'
                }]
            },
            options: {
                ...chartConfig,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    </script>
</body>
</html>"""
        )

        return html
