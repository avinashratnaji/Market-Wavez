"""Render premium, non-redundant Telegram market dashboard cards."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import textwrap

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # Text briefs remain available without visual dependencies.
    Image = ImageDraw = ImageFont = None

from market_sentinel.briefs.models import MorningBrief


@dataclass(frozen=True, slots=True)
class CardSpec:
    slug: str
    title: str
    theme: str
    kind: str


class BriefCardRenderer:
    """Build one focused image per logical dataset, never one crowded poster."""

    SIZE = (1080, 1350)
    ASSETS = Path(__file__).resolve().parents[2] / "assets" / "themes"
    OUTPUT = Path("data") / "generated"
    GREEN = (50, 222, 157)
    RED = (255, 89, 107)
    AMBER = (250, 197, 84)
    WHITE = (239, 245, 255)
    MUTED = (173, 190, 214)
    ACCENT = (105, 226, 218)

    def render(self, brief: MorningBrief, window: str) -> Path:
        """Compatibility API: return the first card."""
        cards = self.render_cards(brief, window)
        if not cards:
            raise RuntimeError("No visual card could be rendered")
        return cards[0]

    def render_cards(self, brief: MorningBrief, window: str, section: str = "full") -> list[Path]:
        if Image is None or ImageDraw is None or ImageFont is None:
            raise RuntimeError("Install requirements-visuals.txt to enable briefing cards")
        window = (window or "full").lower()
        specs = self._specs(brief, window)
        if section != "full":
            allowed = {
                "indian_markets": {
                    "premarket", "postmarket", "heatmap", "india-stocks",
                    "india-news-1", "india-news-2",
                },
                "movers": {"india-movers"},
                "stock_research": {"stocks-today", "stocks-week", "growth"},
                "global_markets": {"global-indices", "global-news-1", "global-news-2", "macro", "mag-seven"},
                "us_movers": {"us-movers"},
                "crypto": {"crypto-market", "crypto-news-1", "crypto-news-2", "commodities"},
                "ipos": {"ipos"},
                "flows": {"flows"},
            }.get(section, set())
            specs = [spec for spec in specs if spec.slug in allowed]
        rendered: list[Path] = []
        for spec in specs:
            path = self._render_spec(brief, window, spec)
            if path:
                rendered.append(path)
        return rendered

    def _specs(self, brief: MorningBrief, window: str) -> list[CardSpec]:
        if window == "morning":
            specs = [
                CardSpec("premarket", "INDIA PRE-MARKET", "premarket", "premarket"),
                CardSpec("summary", "AI-GROUNDED MARKET READ", "summary", "summary"),
                CardSpec("india-news-1", "INDIA CATALYSTS · 1/2", "india_news", "india_news_1"),
                CardSpec("india-news-2", "INDIA CATALYSTS · 2/2", "india_news", "india_news_2"),
                CardSpec("macro", "FED & MACRO WATCH", "summary", "macro"),
                CardSpec("stocks-today", "STOCKS TO RESEARCH · TODAY", "movers", "today_signals"),
                CardSpec("stocks-week", "STOCKS TO RESEARCH · THIS WEEK", "movers", "week_signals"),
                CardSpec("growth", "HIGH-GROWTH RESEARCH CANDIDATES", "summary", "growth_signals"),
                CardSpec("options", "TOP 5 F&O RESEARCH RADAR", "options", "options"),
                CardSpec("ipos", "OPEN IPOs · GMP WATCH", "ipo", "ipos"),
                CardSpec("india-stocks", "INDIA LARGE-CAP WATCH", "movers", "india_leaders"),
            ]
        elif window == "afternoon":
            specs = [
                CardSpec("postmarket", "INDIA CLOSING INDICES", "postmarket", "postmarket"),
                CardSpec("heatmap", "SECTOR HEATMAP", "heatmap", "heatmap"),
                CardSpec("india-movers", "INDIA TOP MOVERS", "india_movers", "india_movers"),
                CardSpec("flows", "INSTITUTIONAL FLOWS", "summary", "flows"),
            ]
        elif window == "night":
            specs = [
                CardSpec("summary", "GLOBAL MARKET READ", "summary", "summary"),
                CardSpec("global-indices", "GLOBAL INDICES", "global_crypto", "global_indices"),
                CardSpec("macro", "FED & MACRO WATCH", "summary", "macro"),
                CardSpec("global-news-1", "GLOBAL MARKET NEWS · 1/2", "global_news", "global_news_1"),
                CardSpec("global-news-2", "GLOBAL MARKET NEWS · 2/2", "global_news", "global_news_2"),
                CardSpec("mag-seven", "MAGNIFICENT SEVEN", "movers", "us_leaders"),
                CardSpec("us-movers", "US TOP MOVERS", "us_movers", "us_movers"),
                CardSpec("commodities", "COMMODITIES", "postmarket", "commodities"),
                CardSpec("crypto-market", "CRYPTO MARKETS", "global_crypto", "crypto"),
                CardSpec("crypto-news-1", "CRYPTO MARKET NEWS · 1/2", "crypto_news", "crypto_news_1"),
                CardSpec("crypto-news-2", "CRYPTO MARKET NEWS · 2/2", "crypto_news", "crypto_news_2"),
            ]
        else:
            specs = [CardSpec("summary", "MARKET INTELLIGENCE", "summary", "summary")]
        return [spec for spec in specs if self._has_data(brief, spec.kind)]

    @staticmethod
    def _has_data(brief: MorningBrief, kind: str) -> bool:
        checks = {
            "premarket": brief.indices or brief.gift_nifty,
            "postmarket": brief.indices,
            "india_news_1": brief.indian_news or brief.top_news,
            "india_news_2": brief.indian_events,
            "global_news_1": brief.global_impact_news,
            "global_news_2": brief.us_events,
            "crypto_news_1": brief.crypto_news[:5],
            "crypto_news_2": brief.crypto_news[5:10],
            "macro": brief.macro_events,
            "options": brief.option_research,
            "ipos": brief.top_ipos,
            "india_leaders": brief.india_leaders,
            "heatmap": brief.sectors,
            "india_movers": brief.gainers or brief.losers,
            "flows": brief.investor_flows,
            "global_indices": brief.global_indices,
            "us_leaders": brief.us_mega_caps,
            "us_movers": brief.us_gainers or brief.us_losers,
            "commodities": brief.commodities,
            "crypto": brief.crypto,
            "summary": brief.ai_summary,
            "today_signals": brief.today_bullish or brief.today_bearish,
            "week_signals": brief.week_bullish or brief.week_bearish,
            "growth_signals": brief.growth_candidates,
        }
        return bool(checks.get(kind))

    def _render_spec(self, brief: MorningBrief, window: str, spec: CardSpec) -> Path | None:
        image = self._background(spec.theme)
        draw = ImageDraw.Draw(image, "RGBA")
        self._panel(draw)
        self._header(draw, brief, spec.title)
        kind = spec.kind
        if kind in {"premarket", "postmarket", "global_indices", "india_leaders", "us_leaders", "commodities", "crypto"}:
            self._draw_quote_card(draw, brief, kind)
        elif kind.startswith(("india_news_", "global_news_", "crypto_news_")):
            self._draw_news(draw, brief, kind)
        elif kind == "macro":
            self._draw_macro(draw, brief)
        elif kind == "options":
            self._draw_options(draw, brief)
        elif kind == "ipos":
            self._draw_ipos(draw, brief)
        elif kind == "heatmap":
            self._draw_heatmap(draw, brief)
        elif kind in {"india_movers", "us_movers"}:
            self._draw_movers(draw, brief, kind)
        elif kind in {"today_signals", "week_signals", "growth_signals"}:
            self._draw_stock_signals(draw, brief, kind)
        elif kind == "flows":
            self._draw_flows(draw, brief)
        else:
            self._draw_summary(draw, brief)
        self._footer(draw)
        self.OUTPUT.mkdir(parents=True, exist_ok=True)
        target = self.OUTPUT / f"{brief.generated_at:%Y%m%d_%H%M}_{window}_{spec.slug}.jpg"
        image.convert("RGB").save(target, "JPEG", quality=91, optimize=True, progressive=True)
        return target

    def _background(self, theme: str):
        aliases = {
            "india_news": ("news", (255, 147, 45, 22)),
            "global_news": ("news", (45, 171, 255, 24)),
            "crypto_news": ("news", (157, 92, 255, 30)),
            "india_movers": ("movers", (32, 210, 155, 20)),
            "us_movers": ("movers", (70, 125, 255, 24)),
        }
        asset, tint = aliases.get(theme, (theme, None))
        path = self.ASSETS / f"{asset}.png"
        if path.exists():
            image = self._cover(Image.open(path).convert("RGB"), self.SIZE)
            if tint:
                overlay = Image.new("RGBA", self.SIZE, tint)
                image = Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")
            return image
        return Image.new("RGB", self.SIZE, (3, 12, 27))

    @staticmethod
    def _cover(image, size):
        scale = max(size[0] / image.width, size[1] / image.height)
        resized = image.resize((int(image.width * scale), int(image.height * scale)), Image.Resampling.LANCZOS)
        left, top = (resized.width - size[0]) // 2, (resized.height - size[1]) // 2
        return resized.crop((left, top, left + size[0], top + size[1]))

    def _panel(self, draw):
        draw.rounded_rectangle((42, 42, 1038, 1218), radius=38, fill=(2, 10, 24, 224), outline=(96, 226, 217, 120), width=2)

    def _header(self, draw, brief: MorningBrief, title: str):
        self._text(draw, (78, 78), title, 49, self.WHITE, bold=True)
        self._text(draw, (80, 145), f"{brief.generated_at:%d %b %Y  ·  %I:%M %p IST}", 25, self.MUTED)
        draw.line((80, 198, 1000, 198), fill=(108, 226, 218, 100), width=2)

    def _footer(self, draw):
        self._text(draw, (1000, 1283), "MARKET WAVEZ", 22, self.WHITE, bold=True, anchor="ra")
        self._text(draw, (1000, 1313), "Verified data · Research only", 17, self.MUTED, anchor="ra")

    def _draw_quote_card(self, draw, brief, kind):
        quotes = {
            "premarket": ([brief.gift_nifty] if brief.gift_nifty else []) + list(brief.indices),
            "postmarket": list(brief.indices),
            "global_indices": list(brief.global_indices),
            "india_leaders": list(brief.india_leaders),
            "us_leaders": list(brief.us_mega_caps),
            "commodities": list(brief.commodities),
            "crypto": list(brief.crypto),
        }[kind]
        y = 235
        if kind in {"premarket", "postmarket"}:
            indices = [q for q in quotes if "VIX" not in q.name.upper()]
            volatility = [q for q in quotes if "VIX" in q.name.upper()]
            y = self._quote_rows(draw, indices[:8], y, "INDICES")
            if volatility:
                self._quote_rows(draw, volatility[:2], y + 18, "VOLATILITY")
        else:
            y = self._quote_rows(draw, quotes[:8] if kind == "crypto" else quotes[:10], y)
            if kind == "us_leaders":
                self._draw_move_reasons(draw, quotes, brief.us_move_reasons, y + 15, "WHY THE BIG MOVES")
            elif kind == "crypto":
                self._draw_move_reasons(draw, quotes, brief.crypto_move_reasons, y + 15, "VERIFIED MARKET DRIVERS", limit=4)

    def _quote_rows(self, draw, quotes, y: int, label: str = "") -> int:
        if label:
            self._text(draw, (80, y), label, 20, self.ACCENT, bold=True)
            y += 42
        for quote in quotes:
            name = quote.name
            company = getattr(quote, "note", "")
            if company and company.lower() != name.lower():
                name = f"{name} · {company}"
            name = textwrap.shorten(name, width=31, placeholder="…")
            unit = getattr(quote, "unit", "")
            value = f"₹{quote.value:,.0f}" if str(unit).startswith("₹") else f"${quote.value:,.2f}" if unit == "$" else f"{quote.value:,.2f}"
            change = float(quote.percent_change)
            colour = self.GREEN if change > 0.001 else self.RED if change < -0.001 else self.AMBER
            draw.ellipse((82, y + 12, 98, y + 28), fill=colour)
            self._text(draw, (118, y), name, 29, self.WHITE, bold=True)
            self._text(draw, (800, y), value, 29, self.WHITE, anchor="ra")
            self._text(draw, (986, y), f"{change:+.2f}%", 29, colour, bold=True, anchor="ra")
            y += 68
        return y

    def _draw_news(self, draw, brief, kind):
        articles = {
            "india_news_1": brief.indian_news or brief.top_news,
            "india_news_2": brief.indian_events,
            "global_news_1": brief.global_impact_news,
            "global_news_2": brief.us_events,
            "crypto_news_1": brief.crypto_news[:5],
            "crypto_news_2": brief.crypto_news[5:10],
        }[kind][:5]
        y = 226
        for number, article in enumerate(articles, 1):
            source = (article.source or "Verified source").strip()
            title = " ".join((article.title or "Market update").split())
            wrapped = textwrap.wrap(title, width=63)[:2]
            self._text(draw, (80, y), f"{number:02d}", 24, self.ACCENT, bold=True)
            for line_number, line in enumerate(wrapped):
                self._text(draw, (132, y + line_number * 31), line, 23, self.WHITE, bold=True)
            summary_y = y + max(1, len(wrapped)) * 31 + 7
            summary = " ".join((article.summary or "").split())
            for line_number, line in enumerate(textwrap.wrap(summary, width=77)[:2]):
                self._text(draw, (132, summary_y + line_number * 27), line, 20, self.MUTED)
            source_y = summary_y + 58
            self._text(draw, (132, source_y), f"Source · {source}", 18, self.ACCENT)
            y = source_y + 52
            if y > 1145:
                break

    def _draw_move_reasons(self, draw, quotes, reasons: dict[str, str], y: int, title: str, limit: int = 3):
        self._text(draw, (80, y), title, 20, self.ACCENT, bold=True)
        y += 40
        selected = sorted(quotes, key=lambda item: abs(float(item.percent_change)), reverse=True)[:limit]
        for quote in selected:
            reason = reasons.get(str(quote.name).upper())
            if not reason:
                reason = (
                    "No asset-specific catalyst was verified; treat the move as broad-market context, not a confirmed cause."
                    if "MARKET DRIVERS" in title else
                    "No company-specific catalyst was verified in the selected news set."
                )
            self._text(draw, (90, y), str(quote.name), 21, self.WHITE, bold=True)
            for index, line in enumerate(textwrap.wrap(reason, width=72)[:2]):
                self._text(draw, (215, y + index * 26), line, 19, self.MUTED)
            y += 72

    def _draw_stock_signals(self, draw, brief, kind):
        if kind == "today_signals":
            groups = (("BULLISH EVIDENCE", brief.today_bullish, self.GREEN), ("BEARISH EVIDENCE", brief.today_bearish, self.RED))
        elif kind == "week_signals":
            groups = (("BULLISH TREND", brief.week_bullish, self.GREEN), ("BEARISH TREND", brief.week_bearish, self.RED))
        else:
            groups = (("REVENUE + EARNINGS + TREND", brief.growth_candidates, self.ACCENT),)
        # Do not spend half a card on an empty opposing bucket.  A short list
        # should have room for the evidence actually available.
        groups = tuple(group for group in groups if group[1])
        y = 226
        per_group = 3 if len(groups) == 2 else 5
        for heading, signals, colour in groups:
            self._text(draw, (80, y), heading, 20, colour, bold=True)
            y += 42
            for signal in signals[:per_group]:
                label = f"{signal.symbol} · {signal.company_name}"
                self._text(draw, (95, y), textwrap.shorten(label, width=42, placeholder="…"), 24, self.WHITE, bold=True)
                self._text(draw, (985, y), f"{signal.score}/100", 23, colour, bold=True, anchor="ra")
                breakdown = (
                    f"Evidence {signal.research_confidence}% · Growth {signal.growth_score}/26 · "
                    f"Quality {signal.quality_score}/24 · Ownership {signal.ownership_score}/10 · "
                    f"Technical {signal.technical_score}/15"
                )
                self._text(draw, (95, y + 33), textwrap.shorten(breakdown, width=92, placeholder="…"), 17, self.ACCENT)
                reason = " · ".join(signal.reasons[:2])
                self._text(draw, (95, y + 58), textwrap.shorten(reason, width=91, placeholder="…"), 18, self.MUTED)
                if signal.key_risks:
                    risk = textwrap.shorten(signal.key_risks[0].replace("Event risk: ", ""), width=88, placeholder="…")
                    self._text(draw, (95, y + 82), f"Risk · {risk}", 17, self.RED)
                y += 122
            y += 18
        self._text(draw, (80, 1155), "Research shortlist · verify price, event risk and liquidity before acting", 18, self.AMBER)

    def _draw_macro(self, draw, brief):
        y = 238
        for event in brief.macro_events[:6]:
            self._text(draw, (80, y), f"{event.starts_at:%d %b}", 28, self.AMBER, bold=True)
            self._text(draw, (230, y), textwrap.shorten(event.name, 45, placeholder="…"), 29, self.WHITE, bold=True)
            for idx, line in enumerate(textwrap.wrap(event.why_it_matters, width=63)[:2]):
                self._text(draw, (230, y + 42 + idx * 30), line, 22, self.MUTED)
            y += 132

    def _draw_options(self, draw, brief):
        y = 226
        for number, setup in enumerate(brief.option_research[:5], 1):
            bias = setup.bias.replace(" option-chain setup", "")
            colour = self.GREEN if "bull" in bias.lower() else self.RED if "bear" in bias.lower() else self.AMBER
            pcr = f"{setup.pcr:.2f}" if setup.pcr is not None else "N/A"
            spot = setup.chain.spot_price or setup.technicals.close
            self._text(draw, (80, y), f"{number}. {textwrap.shorten(setup.display_name, 28, placeholder='…')}", 29, self.WHITE, bold=True)
            self._text(draw, (985, y), bias.upper(), 24, colour, bold=True, anchor="ra")
            support = f"₹{setup.support:,.0f}" if setup.support else "—"
            resistance = f"₹{setup.resistance:,.0f}" if setup.resistance else "—"
            self._text(draw, (105, y + 45), f"Spot ₹{spot:,.2f}   PCR {pcr}   Confidence {setup.confidence_score}/100", 22, self.MUTED)
            self._text(draw, (105, y + 78), f"Support {support}   ·   Resistance {resistance}   ·   {setup.chain.expiry}", 22, self.WHITE)
            y += 174

    def _draw_ipos(self, draw, brief):
        y = 226
        for number, ipo in enumerate(brief.top_ipos[:5], 1):
            pct = ipo.gmp_percent
            colour = self.GREEN if pct and pct > 0 else self.RED if pct and pct < 0 else self.AMBER
            gmp = f"₹{ipo.gmp:,.0f} ({pct:+.1f}%)" if ipo.gmp is not None and pct is not None else "Awaiting GMP"
            issue = f"₹{ipo.price_band_high:,.0f}" if ipo.price_band_high else "—"
            lot = f"{ipo.lot_size:,}" if ipo.lot_size else "—"
            window = f"{ipo.subscription_open:%d %b}–{ipo.subscription_close:%d %b}" if ipo.subscription_open and ipo.subscription_close else ""
            self._text(draw, (80, y), f"{number}. {textwrap.shorten(ipo.name, 34, placeholder='…')}", 29, self.WHITE, bold=True)
            self._text(draw, (985, y), gmp, 27, colour, bold=True, anchor="ra")
            self._text(draw, (105, y + 47), f"{ipo.issue_type or 'IPO'}   ·   Issue {issue}   ·   Lot {lot}   ·   {window}", 22, self.MUTED)
            y += 150

    def _draw_heatmap(self, draw, brief):
        sectors = list(brief.sectors)[:12]
        scale = max([abs(float(item.percent_change)) for item in sectors] or [1])
        y = 230
        for item in sectors:
            change = float(item.percent_change)
            colour = self.GREEN if change > 0 else self.RED if change < 0 else self.AMBER
            self._text(draw, (80, y), textwrap.shorten(item.name, 22, placeholder="…"), 27, self.WHITE, bold=True)
            draw.rounded_rectangle((390, y + 8, 850, y + 29), radius=10, fill=(255, 255, 255, 20))
            width = int(440 * abs(change) / scale)
            draw.rounded_rectangle((390, y + 8, 390 + max(8, width), y + 29), radius=10, fill=(*colour, 220))
            self._text(draw, (985, y), f"{change:+.2f}%", 27, colour, bold=True, anchor="ra")
            y += 70

    def _draw_movers(self, draw, brief, kind):
        gainers, losers = (brief.gainers[:5], brief.losers[:5]) if kind == "india_movers" else (brief.us_gainers[:5], brief.us_losers[:5])
        y = 226
        for heading, items, direction in (("GAINERS", gainers, 1), ("LOSERS", losers, -1)):
            colour = self.GREEN if direction > 0 else self.RED
            self._text(draw, (80, y), heading, 23, colour, bold=True)
            y += 43
            for item in items:
                name = getattr(item, "name", "")
                company = getattr(item, "company_name", "") or getattr(item, "note", "")
                label = f"{name} · {company}" if company and company.lower() != name.lower() else name
                label = textwrap.shorten(label, 36, placeholder="…")
                price = getattr(item, "value", 0)
                unit = "$" if kind == "us_movers" else "₹"
                change = float(getattr(item, "percent_change", 0))
                self._text(draw, (100, y), label, 24, self.WHITE, bold=True)
                self._text(draw, (790, y), f"{unit}{price:,.2f}", 24, self.WHITE, anchor="ra")
                self._text(draw, (985, y), f"{change:+.2f}%", 24, colour, bold=True, anchor="ra")
                y += 55
            y += 22

    def _draw_flows(self, draw, brief):
        flow = brief.investor_flows
        if not flow:
            return
        y = 260
        self._text(draw, (80, y), f"CASH MARKET · {flow.trade_date:%d %b %Y}", 24, self.ACCENT, bold=True)
        y += 90
        for label, buy, sell, net in (("FII / FPI", flow.fii_buy, flow.fii_sell, flow.fii_net), ("DII", flow.dii_buy, flow.dii_sell, flow.dii_net)):
            net_value = float(net or 0)
            colour = self.GREEN if net_value > 0 else self.RED if net_value < 0 else self.AMBER
            self._text(draw, (80, y), label, 36, self.WHITE, bold=True)
            self._text(draw, (985, y), f"{net_value:+,.2f} Cr", 36, colour, bold=True, anchor="ra")
            self._text(draw, (105, y + 62), f"BUY ₹{float(buy or 0):,.2f} Cr", 25, self.MUTED)
            self._text(draw, (985, y + 62), f"SELL ₹{float(sell or 0):,.2f} Cr", 25, self.MUTED, anchor="ra")
            y += 200
        self._text(draw, (80, y), f"Source · {flow.source}", 21, self.MUTED)

    def _draw_summary(self, draw, brief):
        sentiment = (brief.market_sentiment or "Neutral").upper()
        colour = self.GREEN if sentiment == "BULLISH" else self.RED if sentiment == "BEARISH" else self.AMBER
        draw.rounded_rectangle((80, 235, 1000, 340), radius=24, fill=(*colour, 35), outline=(*colour, 170), width=2)
        self._text(draw, (110, 267), f"{sentiment}  ·  HEALTH {brief.health_score}/100", 34, colour, bold=True)
        y = 400
        for bullet in re.split(r"\n+", brief.ai_summary or "")[:5]:
            clean = bullet.lstrip("•- ").strip()
            for idx, line in enumerate(textwrap.wrap(clean, width=58)[:3]):
                self._text(draw, (110 if idx else 85, y), ("• " if idx == 0 else "") + line, 27, self.WHITE if idx == 0 else self.MUTED)
                y += 38
            y += 28

    def _text(self, draw, xy, value, size, fill, bold=False, anchor=None):
        font = self._font(size, bold)
        x, y = xy
        draw.text((x + 2, y + 3), str(value), font=font, fill=(0, 0, 0, 220), anchor=anchor)
        draw.text((x, y), str(value), font=font, fill=fill, anchor=anchor)

    @staticmethod
    def _font(size: int, bold: bool = False):
        candidates = [
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
        ]
        for path in candidates:
            if path.exists():
                return ImageFont.truetype(str(path), size)
        return ImageFont.load_default()
