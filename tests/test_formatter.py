from market_sentinel.briefs.morning import (
    MorningBriefBuilder,
)

from market_sentinel.telegram.morning import (
    MorningFormatter,
)

builder = MorningBriefBuilder()

brief = builder.build()

print()

print(
    MorningFormatter.format(
        brief,
    )
)