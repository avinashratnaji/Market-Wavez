import feedparser

feed = feedparser.parse(
    "https://feeds.reuters.com/reuters/businessNews"
)

print("Status :", feed.status if hasattr(feed, "status") else "No status")
print("Version:", feed.version)
print("Entries:", len(feed.entries))

if hasattr(feed, "bozo"):
    print("Bozo:", feed.bozo)

if hasattr(feed, "bozo_exception"):
    print(feed.bozo_exception)