# Telegram entry point (planned, not implemented yet)

This package is reserved for a future Telegram bot that lets either partner log an
expense directly from a chat, as a second entry point alongside the web API.

When built, it will:

- Wire its own dependency injection (repository + service instances, then use cases),
  independently of `app/api/deps.py` — that module is specific to FastAPI's `Depends()`
  mechanism and isn't reusable here.
- Call the exact same `app/use_cases/*` classes the API routes call today (e.g.
  `AddExpenseUseCase`, `GetMonthSummaryUseCase`) — no business logic should be
  duplicated or reimplemented for the bot.
- Need its own way to resolve "which of our two `User` rows sent this Telegram
  message" (e.g. a `telegram_user_id` column added to `users` at that point) —
  intentionally not built now, since there's only one entry point to support today.
