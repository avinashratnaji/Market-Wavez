# Market Sentinel Architecture

## Overview

Market Sentinel is a modular market intelligence platform designed to collect, analyze, rank and distribute financial market intelligence.

The project is divided into independent modules to allow future expansion.

```
                +----------------------+
                |    Data Providers    |
                +----------+-----------+
                           |
      +--------------------+---------------------+
      |                    |                     |
 Angel One           Yahoo Finance        Future Sources
                                          Reuters
                                          Moneycontrol
                                          RBI
                                          SEBI
                                          ET
```

↓

```
News Aggregator
```

↓

```
Classification
Entity Extraction
Sector Mapping
Importance Engine
Scoring Engine
Summary Builder
```

↓

```
Morning Brief Builder
```

↓

```
Telegram Formatter
```

↓

```
Telegram Bot
```

---

## Project Structure

- Providers
- News Engine
- Analytics
- Brief Builders
- Telegram
- Database
- Scheduler

Each module is isolated and independently testable.

---

## Design Goals

- Modular
- Extensible
- Provider independent
- High performance
- Institutional quality
- Easy testing