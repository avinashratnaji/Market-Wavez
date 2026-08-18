from pathlib import Path
import argparse
import sys


PROJECT_NAME = "Market Sentinel"
VERSION = "0.2.0"


def print_banner():
    print("=" * 60)
    print(f"{PROJECT_NAME:^60}")
    print(f"{'Version ' + VERSION:^60}")
    print("=" * 60)


def bootstrap():
    root = Path.cwd()

    folders = [
        "market_sentinel",
        "market_sentinel/providers",
        "market_sentinel/providers/base",
        "market_sentinel/providers/india",
        "market_sentinel/providers/usa",
        "market_sentinel/providers/crypto",
        "market_sentinel/providers/commodities",
        "market_sentinel/providers/news",
        "market_sentinel/providers/economy",
        "market_sentinel/providers/geopolitics",
        "market_sentinel/analyzers",
        "market_sentinel/database",
        "market_sentinel/engine",
        "market_sentinel/models",
        "market_sentinel/services",
        "market_sentinel/config",
        "market_sentinel/utils",
        "market_sentinel/telegram",
        "market_sentinel/scheduler",
        "docs",
        "tests",
        "reports",
        "logs",
        "data",
        "scripts",
    ]

    files = [
        "README.md",
        "requirements.txt",
        ".env",
        ".env.example",
        ".gitignore",
        "LICENSE",
        "VERSION",
    ]

    print("\nCreating folders...\n")

    for folder in folders:
        path = root / folder
        path.mkdir(parents=True, exist_ok=True)

        init = path / "__init__.py"

        # Don't create __init__.py in docs/data/logs/etc.
        if "market_sentinel" in str(path):
            init.touch(exist_ok=True)

        print(f"✓ {folder}")

    print("\nCreating files...\n")

    for file in files:
        filepath = root / file
        filepath.touch(exist_ok=True)
        print(f"✓ {file}")

    # VERSION
    (root / "VERSION").write_text("0.1.0\n")

    # README
    (root / "README.md").write_text(
        "# Market Sentinel\n\n"
        "Personal AI Investment Intelligence Assistant\n"
    )

    # .gitignore
    (root / ".gitignore").write_text(
        ".venv/\n"
        "__pycache__/\n"
        "*.pyc\n"
        ".env\n"
        "logs/\n"
        "*.db\n"
        ".idea/\n"
        ".vscode/\n"
    )

    # .env.example
    (root / ".env.example").write_text(
        "POSTGRES_HOST=localhost\n"
        "POSTGRES_PORT=5432\n"
        "POSTGRES_DB=market_sentinel\n"
        "POSTGRES_USER=postgres\n"
        "POSTGRES_PASSWORD=password\n\n"
        "TELEGRAM_TOKEN=\n"
        "TELEGRAM_CHAT_ID=\n\n"
        "ANGEL_API_KEY=\n"
        "ANGEL_CLIENT_ID=\n"
        "ANGEL_PIN=\n"
    )

    print("\nProject bootstrapped successfully!\n")


def doctor():
    print("\nChecking environment...\n")

    print(f"Python : {sys.version.split()[0]}")
    print("Status : OK")

    print("\nNext Step:")
    print("pip install -r requirements.txt")


def main():
    # Windows PowerShell may still expose a legacy cp1252 stream.  Market
    # panels intentionally use ₹ and emoji, so make CLI preview output UTF-8.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        prog="sentinel",
        description="Market Sentinel CLI"
    )

    sub = parser.add_subparsers(dest="command")

    sub.add_parser(
        "bootstrap",
        help="Create the project structure"
    )

    sub.add_parser(
        "doctor",
        help="Verify the development environment"
    )

    sub.add_parser(
        "scheduler",
        help="Run continuous market data collection"
    )

    sub.add_parser(
        "collect",
        help="Collect live market data"
    )

    sub.add_parser(
        "latest",
        help="Show latest market data"
    )

    sub.add_parser(
        "telegram-test",
        help="Send Telegram test notification"
    )

    telegram_parser = sub.add_parser(
        "telegram",
        help="Send latest market summary"
    )
    telegram_parser.add_argument(
        "--section",
        choices=("full", "indian_markets", "movers", "global_markets", "us_movers", "crypto", "ipos", "flows"),
        default="full",
        help="Send one live terminal panel instead of the full brief",
    )
    telegram_parser.add_argument(
        "--brief",
        choices=("full", "morning", "afternoon", "night"),
        default="full",
        help="Scheduled briefing window to publish",
    )

    sub.add_parser("telegram-listen", help="Run the Telegram command listener")

    options_parser = sub.add_parser(
        "option-radar",
        help="Run the private ten-stock EOD option-chain research radar",
    )
    options_parser.add_argument(
        "--send",
        action="store_true",
        help="Publish the analysis cards to the configured Telegram chat",
    )

    equity_parser = sub.add_parser(
        "equity-research",
        help="Create a private business-quality scorecard from reported financials",
    )
    equity_parser.add_argument("symbol", help="NSE symbol, for example HEROMOTOCO")

    sub.add_parser(
        "analyze",
        help="Analyze latest market snapshot"
    )

    history_parser = sub.add_parser(
        "history",
        help="Show historical prices"
    )

    history_parser.add_argument(
        "symbol",
        help="Market symbol"
    )

    history_parser.add_argument(
        "--limit",
        type=int,
        default=20,
    )

    stats_parser = sub.add_parser(
        "stats",
        help="Show market statistics"
    )

    stats_parser.add_argument(
        "symbol",
        help="Market symbol"
    )

    args = parser.parse_args()

    print_banner()

    if args.command == "bootstrap":
        bootstrap()

    elif args.command == "doctor":
        doctor()

    elif args.command == "collect":
        from market_sentinel.services.market_service import MarketService
        service = MarketService()
        service.collect()

    elif args.command == "latest":
        from market_sentinel.services.market_service import MarketService
        service = MarketService()
        records = service.latest()
        print()
        print("=" * 60)
        print("Latest Market Data")
        print("=" * 60)
        for record in records:
            print(
                f"{record.name:<15}"
                f"{record.price:<12}"
                f"{record.currency}"
            )

    elif args.command == "history":
        from market_sentinel.services.market_service import MarketService
        service = MarketService()
        records = service.history(
            args.symbol,
            args.limit,
        )
        print()
        print("=" * 60)
        print(f"History : {args.symbol}")
        print("=" * 60)
        for record in records:
            print(
                f"{record.collected_at}"
                f"   {record.price}"
                f"   {record.currency}"
            )

    elif args.command == "stats":
        from market_sentinel.services.market_service import MarketService
        service = MarketService()
        symbol, latest, stats = service.statistics(args.symbol)
        print()
        print("=" * 60)
        print("Market Statistics")
        print("=" * 60)
        print(f"Asset           : {latest.name} ({symbol})")
        print()
        print(f"Latest Price    : {float(latest.price):.4f} {latest.currency}")
        print(f"Highest Price   : {float(stats.highest):.4f}")
        print(f"Lowest Price    : {float(stats.lowest):.4f}")
        print(f"Average Price   : {float(stats.average):.4f}")
        print()
        print(f"Records         : {stats.records}")
        print(f"First Record    : {stats.first_time}")
        print(f"Latest Record   : {stats.latest_time}")

    elif args.command == "telegram-test":
        from market_sentinel.telegram.notifier import TelegramNotifier
        from market_sentinel.telegram.formatter import TelegramFormatter
        TelegramNotifier().notify(
            TelegramFormatter.test_message()
        )

    elif args.command == "telegram":
        from market_sentinel.services.morning_brief_service import MorningBriefService
        MorningBriefService().send(section=args.section, window=args.brief)

    elif args.command == "telegram-listen":
        from market_sentinel.telegram.commands import TelegramCommandServer
        TelegramCommandServer().run()

    elif args.command == "option-radar":
        from market_sentinel.research.options.service import DailyOptionsRadarService

        service = DailyOptionsRadarService()
        setups, failures = service.run()
        messages = service.format_messages(setups, failures)
        print("\n\n".join(messages))
        if args.send:
            from market_sentinel.telegram.notifier import TelegramNotifier
            TelegramNotifier().send_brief(messages=messages)

    elif args.command == "equity-research":
        from market_sentinel.research.equity.provider import YahooFinancialProvider
        from market_sentinel.research.equity.scorer import EquityQualityScorer

        card = EquityQualityScorer().score(YahooFinancialProvider().fetch(args.symbol))
        print(f"\n{card.company_name} — PRIVATE EQUITY RESEARCH\n")
        print(f"Quality score: {card.quality_score}/90")
        print(f"Growth: {card.growth_score}/25 | Profitability: {card.profitability_score}/25")
        print(f"Balance sheet: {card.balance_sheet_score}/20 | Cash flow: {card.cash_flow_score}/20")
        if card.strengths:
            print("\nStrengths:\n" + "\n".join(f"• {item}" for item in card.strengths))
        if card.risks:
            print("\nRisks:\n" + "\n".join(f"• {item}" for item in card.risks))
        if card.data_gaps:
            print("\nData gaps:\n" + "\n".join(f"• {item}" for item in card.data_gaps))
        print("\nThis is a reported-fundamentals scorecard, not an investment recommendation.")

    elif args.command == "scheduler":
        from market_sentinel.scheduler.scheduler_service import SchedulerService
        scheduler = SchedulerService()
        scheduler.start()

    elif args.command == "analyze":
        from market_sentinel.services.analytics_service import AnalyticsService

        service = AnalyticsService()

        results = service.analyze_latest()

        print()
        print("=" * 70)
        print("Market Analytics")
        print("=" * 70)

        for asset in results:
            print(asset)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
