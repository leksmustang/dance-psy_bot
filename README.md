# Business Automation Bot Prototypes

[Русская версия](./README_RU.md)

A collection of domain-specific Telegram automation prototypes for a dance studio, a psychologist and an automotive-detailing business.

These projects were built before the shared QuickPult runtime. They show how I translate real service workflows into bot states, booking logic and external integrations. The repository is kept as a **portfolio/legacy project**, not as a turnkey production package.

## Implemented patterns

- separate Telegram bots using aiogram and python-telegram-bot
- finite-state conversation flows and persistent user/booking data
- Google Calendar availability lookup and event creation
- trial-session booking, payment state and rescheduling limits
- domain-specific questionnaires, menus and lead qualification
- anti-flood middleware, structured repositories and service layers
- SQLite persistence, Docker configuration and asynchronous I/O

## Architecture

- `app/bots/` — domain entry points and handlers
- `app/repositories/` — persistence operations
- `app/services/` — booking, calendar and validation logic
- `app/middlewares/` — cross-cutting controls such as rate limiting
- `app/models.py` and `app/database.py` — local data layer

## Why this project matters

Maintaining several independent bots revealed the recurring parts of business automation: identity, booking, payment state, human escalation, channel transport and reporting. Those lessons directly led to the shared runtime and versioned configuration model in **[QuickPult](https://quickbizauto.com)**.

## Local setup

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python run.py
```

Google Calendar functions additionally require a service-account credentials file. Never commit that file or real bot tokens.

## Current boundaries

- This is early portfolio code with several domain bots in one repository.
- Deployment requires project-specific content, tokens, calendar configuration and database initialization.
- Some flows are prototypes and should be reviewed and tested before production reuse.
- Active product development has moved to the unified QuickPult platform.

## Stack

Python · aiogram · python-telegram-bot · aiosqlite · Google Calendar API · aiohttp · Docker
