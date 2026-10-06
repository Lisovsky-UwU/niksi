# Niksi

Семейный бюджет на двоих в виде тетради в клетку. Двое ведут общий бюджет по месяцам: лимиты по
категориям, траты с комментариями, доходы, личная «серая зона» каждого, сверка с реальными деньгами,
накопления и цели. Всё это доступно в веб-приложении (удобно с телефона) и в общей беседе в Telegram.

- **Бюджетный месяц** начинается в день первой полной зарплаты и длится до начала следующего,
  например «Сентябрь: с 5 сентября по 4 октября».
- **Категории с лимитами** и цветами; остаток на месяц и сколько можно тратить в день.
- **Траты:** кто потратил, на что (комментарий в пару слов или пару предложений), редактирование,
  фильтры по категориям и датам.
- **Доход:** ожидаемый на месяц у каждого и фактические поступления («Аванс 40 000 ₽»).
- **Серая зона:** личные деньги каждого. Видно, кто сколько взял, но не на что потратил.
- **Итог месяца столбиком;** остаток переходит в следующий месяц.
- **Сверка:** вы вводите, сколько денег на самом деле, расхождение с записями учитывается в месяце.
- **Накопления:** накопительный счёт, вклад, цель с суммой и сроком (сколько откладывать в месяц), архив.
- **Профиль:** имя, пароль, аватар.
- **Telegram-бот:** траты одной строкой («450 прод пятёрочка»), остатки, уведомления, вечерняя сводка.

## Устройство

```
                ┌──────────────── docker compose ─────────────────────┐
 браузер ──────►│ web (Caddy) ──/api/*──► backend (FastAPI) ──► db    │
 телефон        │   статика Vue            │                (Postgres)|
                │                          │ те же use cases          │
 Telegram ◄────►│ bot (aiogram, long polling) ─────────────────► db   │
                └─────────────────────────────────────────────────────┘
```

| Часть | Стек | Где |
| --- | --- | --- |
| Веб-приложение | Vue 3, TypeScript, Pinia, Vue Router, Vite | `frontend/` |
| API | Python 3.13, FastAPI, SQLAlchemy 2, Pydantic 2, Alembic | `backend/` |
| Telegram-бот | aiogram 3, тот же код, что у API | `backend/app/telegram/` |
| База | PostgreSQL 17 | контейнер `db` |
| Раздача и прокси | Caddy 2: статика, `/api` → backend, HTTPS для своего домена | `frontend/Caddyfile` |

Бэкенд разделён на слои, и бот с API используют одну бизнес-логику:

```
backend/app/
  domain/          модели и правила без фреймворков (периоды месяцев, лимиты, тексты сообщений)
  interfaces/      контракты репозиториев и сервисов
  infrastructure/  SQLAlchemy, хеширование паролей, JWT, отправка в Telegram
  use_cases/       бизнес-операции: добавить трату, посчитать итог месяца, сверка…
  api/             FastAPI: роуты, схемы запросов, сборка зависимостей
  telegram/        бот: разбор сообщений, ответы (BotService), aiogram
  scripts/         создание двух аккаунтов
backend/alembic/   миграции базы
backend/tests/     тесты (pytest)
frontend/src/      views (страницы), components, stores (Pinia), api, utils
```

Вход — по email и паролю, сессия хранится в httpOnly-куке. Страница и API отдаются с одного адреса
(через Caddy в Docker, через прокси Vite при разработке), поэтому кука работает без CORS.

## Быстрый старт в Docker

Нужны Docker и Docker Compose.

```bash
cp .env.example .env
```

Заполните в `.env` как минимум `POSTGRES_PASSWORD`, `SECRET_KEY` и два аккаунта `SEED_USER1_*`,
`SEED_USER2_*`. Случайный ключ можно получить так:
`python -c "import secrets; print(secrets.token_hex(32))"`.

```bash
docker compose up -d --build                                          # сборка и запуск
docker compose run --rm backend python -m app.scripts.seed_users      # создать два аккаунта (один раз)
```

Приложение откроется на <http://localhost:8080>, а с телефона в той же сети — на
`http://<IP-компьютера>:8080`. Миграции базы применяются сами при каждом старте `backend`.

Полезное:

```bash
docker compose ps                     # что запущено
docker compose logs -f backend        # логи API (или web, bot, db)
docker compose up -d --build          # обновиться после изменений в коде
docker compose down                   # остановить (данные в томе db-data сохраняются)
```

### Свой домен и HTTPS

Направьте домен на сервер и укажите в `.env`:

```
SITE_ADDRESS=niksi.example.com
COOKIE_SECURE=true
HTTP_PORT=80
HTTPS_PORT=443
```

Caddy сам получит и будет продлевать сертификат Let's Encrypt; сертификаты хранятся в томе `caddy-data`.
По обычному HTTP (домашняя сеть) оставьте `SITE_ADDRESS=:80` и `COOKIE_SECURE=false`, иначе браузер не
сохранит куку входа.

### Сервер со своим Nginx и PostgreSQL

Если на сервере уже есть Nginx (раздает TLS) и PostgreSQL в контейнерах, контейнер `db` не нужен,
а Caddy работает по HTTP за Nginx. Это включает `docker-compose.server.yml`.

1. Создайте базу и пользователя в существующем PostgreSQL:

   ```bash
   docker exec -it postgres psql -U postgres      -c "CREATE ROLE niksi LOGIN PASSWORD '<пароль>'"      -c "CREATE DATABASE niksi OWNER niksi"
   ```

2. Узнайте Docker-сеть контейнера PostgreSQL:
   `docker inspect postgres --format '{{range $k, $v := .NetworkSettings.Networks}}{{$k}} {{end}}'`.
3. В `.env`:

   ```
   COMPOSE_FILE=docker-compose.yml:docker-compose.server.yml
   DATABASE_URL=postgresql+psycopg://niksi:<пароль>@postgres:5432/niksi
   POSTGRES_NETWORK=<сеть из шага 2>
   SITE_ADDRESS=:80
   COOKIE_SECURE=true
   HTTP_PORT=3090
   ```

   `POSTGRES_PASSWORD` в этом режиме не нужен. Хост в `DATABASE_URL` - имя контейнера PostgreSQL.
   Приложение слушает только `127.0.0.1:HTTP_PORT`.
4. `docker compose up -d --build`, затем один раз создайте аккаунты (`seed_users`, см. выше).
5. Сайт в Nginx:

   ```nginx
   server {
       listen 443 ssl;
       server_name niksi.example.com;

       ssl_certificate     /etc/nginx/ssl/cert.pem;
       ssl_certificate_key /etc/nginx/ssl/key.pem;

       location / {
           proxy_pass http://127.0.0.1:3090;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

   Если Nginx работает не в сети `host`, а в своей Docker-сети, вместо `127.0.0.1` нужен адрес,
   по которому он видит хост, или общая сеть с контейнером `web`.

### Настройки `.env`

| Переменная | Зачем | По умолчанию |
| --- | --- | --- |
| `POSTGRES_PASSWORD` | пароль базы | обязательна со встроенной базой |
| `DATABASE_URL` | своя база вместо контейнера `db` | собирается из `POSTGRES_PASSWORD` |
| `COMPOSE_FILE` | `docker-compose.yml:docker-compose.server.yml` для сервера со своими Nginx и PostgreSQL | пусто |
| `POSTGRES_NETWORK` | Docker-сеть внешнего PostgreSQL (серверный режим) | пусто |
| `SECRET_KEY` | ключ подписи входа (JWT) | обязательна |
| `SITE_ADDRESS` | `:80` или домен для HTTPS | `:80` |
| `COOKIE_SECURE` | кука только по HTTPS | `false` |
| `HTTP_PORT`, `HTTPS_PORT` | порты на хосте | `8080`, `8443` |
| `COMPOSE_PROFILES` | `telegram` запускает бота | пусто |
| `TELEGRAM_BOT_TOKEN` | токен от @BotFather | пусто |
| `TELEGRAM_BOT_USERNAME` | имя бота без @, для ссылки привязки | пусто |
| `TELEGRAM_API_URL` | адрес Bot API: зеркало, прокси или свой `telegram-bot-api` | `https://api.telegram.org` |
| `TELEGRAM_SUMMARY_TIME` | время вечерней сводки | `21:00` |
| `TELEGRAM_TIMEZONE` | часовой пояс сводки | `Europe/Moscow` |
| `SEED_USER{1,2}_{EMAIL,PASSWORD,NAME}` | два аккаунта для `seed_users` | пусто |

## Telegram-бот

Бот живёт в общей беседе пары: записывает траты одной строкой, показывает остатки, принимает доходы
и серую зону, пишет о тратах, добавленных в веб-приложении, и присылает вечернюю сводку.

### Подключение

1. Создайте бота у [@BotFather](https://t.me/BotFather) (`/newbot`) и **отключите privacy mode**:
   `/setprivacy` → бот → `Disable`. Иначе в группе бот увидит только команды, а не строки вроде
   «450 продукты». Если бот уже был в беседе, удалите его и добавьте снова.
2. В `.env` укажите `TELEGRAM_BOT_TOKEN`, `TELEGRAM_BOT_USERNAME` и раскомментируйте
   `COMPOSE_PROFILES=telegram`, затем выполните `docker compose up -d`. Токен читает и `backend`:
   уведомления о тратах из приложения отправляет сам API. Поэтому после изменения токена
   перезапускаются оба сервиса (`up -d` делает это сам).
3. Каждый из двоих: в приложении **Настройки → Telegram → Получить код** и отправить боту `/link КОД`
   или нажать «Открыть бота и привязать» (ссылка появляется, если задан `TELEGRAM_BOT_USERNAME`).
   Код одноразовый и действует 15 минут. Отвязать: `/unlink` или кнопка в настройках.
4. Добавьте бота в общую беседу, и кто-то один пишет там `/bind`: эта беседа становится общей.
   В других группах бот молчит, в личке отвечает как обычно.

Без Docker бот запускается рядом с бэкендом: `cd backend && uv run python -m app.telegram`
(настройки берутся из `backend/.env`).

> С одним токеном может работать только один экземпляр бота. Если бот запущен локально, остановите его
> перед запуском в Docker (и наоборот), иначе Telegram вернёт ошибку `409 Conflict`.

### Что умеет

| В беседе | Что делает бот |
| --- | --- |
| `450 прод пятёрочка`, `кафе 300`, `1500 дом и быт за электричество`, `кафе⏎500⏎академия кофе` | Записывает трату на того, кто написал. Порядок любой, категорию можно сократить или написать с опечаткой; если бот её не узнал, пришлёт кнопки категорий и «Это не трата». Под ответом кнопки «Отменить» и «Другая категория» |
| `/add 450 …` | Записать трату, даже если строка похожа на обычную фразу |
| `+40000 аванс` | Доход |
| `/grey 3000` | Взяли себе из серой зоны |
| `/left` `/cats` `/month` `/last` | Остаток и сколько в день, категории, итог месяца, последние траты |
| `/undo` | Удалить свою последнюю трату |
| `/notify on/off`, `/summary on/off` | Уведомления о тратах из приложения, вечерняя сводка (в `TELEGRAM_SUMMARY_TIME`) |
| `/help` | Подсказка по всем командам |

Обычные сообщения с числами («буду дома в 19», «в кафе в 18:30») бот не трогает. Сумма засчитывается,
только если стоит в начале или в конце сообщения, на отдельной строке или рядом с названием категории, и
не после «в», «к», «до» и похожих слов, которые делают число временем.

### Как устроен

- `app/telegram/parsing.py` разбирает строки: сумму, категорию (полное название, начало слова или
  опечатка через `difflib`), комментарий и доход с плюсом. Тесты: `tests/test_telegram_parsing.py`.
- `app/telegram/service.py` (`BotService`) решает, что бот делает и отвечает, без Telegram-библиотек.
  Он вызывает те же `app/use_cases/*`, что и веб-API, так что бизнес-логика нигде не дублируется.
  Тесты: `tests/test_telegram_bot.py`.
- `app/telegram/bot.py` — обработчики aiogram и цикл вечерней сводки. На каждое сообщение открывается
  своя сессия базы, синхронный код выполняется в отдельном потоке.
- `app/telegram/__main__.py` — запуск через long polling, публичный адрес не нужен.
- Кто пишет, бот узнаёт по `users.telegram_user_id`, а общую беседу хранит в таблице `telegram_chats`.
- Кнопки выбора категории для нераспознанной траты хранятся в памяти бота 30 минут. После перезапуска
  старые кнопки ответят, что устарели.

## Разработка без Docker

Нужны Python 3.13 с [uv](https://docs.astral.sh/uv/), Node.js 22+ и PostgreSQL (удобно в Docker).

**База:**

```bash
docker run -d --name niksi-db -e POSTGRES_USER=niksi -e POSTGRES_PASSWORD=niksi -e POSTGRES_DB=niksi \
  -p 5432:5432 postgres:17-alpine
```

**Бэкенд** (`backend/`, настройки в `backend/.env`, пример — `backend/.env.example`):

```bash
cd backend
uv sync
uv run alembic upgrade head
uv run python -m app.scripts.seed_users
uv run uvicorn main:app --reload --port 8000
uv run python -m app.telegram        # бот, если нужен
```

Для локального запуска по HTTP задайте `COOKIE_SECURE=false` в `backend/.env`.

**Фронт** (`frontend/`): Vite проксирует `/api` на `localhost:8000`.

```bash
cd frontend
npm install
npm run dev                          # http://localhost:5173
npm run dev -- --host 0.0.0.0        # чтобы открыть с телефона в той же сети
npm run build                        # проверка типов и сборка
```

### Тесты

```bash
cd backend && uv run pytest
```

Тесты идут на SQLite в памяти, база не нужна. Они покрывают API целиком: траты, доходы, серую зону,
накопления, сверку, перенос остатка, периоды месяцев, профиль, а также разбор сообщений и ответы
Telegram-бота.

### Миграции

Схема базы меняется только через Alembic:

```bash
cd backend
uv run alembic revision -m "что изменилось"   # новый файл в alembic/versions/, опишите upgrade/downgrade
uv run alembic upgrade head
```

В Docker новые миграции применяются сами при перезапуске `backend`.

## Резервная копия

```bash
docker compose exec db pg_dump -U niksi niksi > niksi-$(date +%F).sql     # сохранить
docker compose exec -T db psql -U niksi niksi < niksi-2026-09-30.sql      # восстановить в пустую базу
```

Все данные лежат в томе `db-data`. `docker compose down` его не трогает, `docker compose down -v` —
удаляет.

## Как считаются деньги

- **Остаток по лимитам** — сумма лимитов категорий минус траты месяца. «В день» — этот остаток,
  делённый на дни до конца периода.
- **Итог месяца:** с прошлого месяца + доходы − траты − серая зона − в накопления (+ из накоплений)
  ± расхождения сверки = остаток, и он переходит в следующий месяц. Для первого месяца перенос можно
  задать вручную.
- **Сверка:** последняя сверка — точка отсчёта. «По записям на руках» = её сумма + всё записанное
  после неё. Разница с реальной суммой сохраняется и попадает в итог месяца, в чей период она пришлась.
- **Проценты по вкладу** увеличивают копилку, но не трогают бюджет месяца.
