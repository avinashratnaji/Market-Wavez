# Telegram Setup

## Step 1

Create a bot using BotFather.

Save

- Bot Token

---

## Step 2

Open the bot.

Press

/start

---

## Step 3

Retrieve your Chat ID.

Update

.env

```
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

---

## Step 4

Run

```
python -m tests.test_telegram
```

The Morning Brief should appear in Telegram.

---

## Future

Version 1.1 will support:

- Multiple subscribers
- /start
- /stop
- Automatic broadcasts
- Subscriber database