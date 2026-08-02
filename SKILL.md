---
name: logistoria-instagram
version: 1.0.0
description: |
  Автоматизация Instagram для Logistoria — публикации, мониторинг заявок, контент-план.
  Работает через официальный Facebook Graph API (Instagram Basic Display + Instagram Graph API).
  Триггеры: "опубликуй в Instagram", "новая заявка", "контент-план", "проверь комментарии".
author: Artur A. / OpenClaw
license: MIT
---

# Logistoria Instagram Skill

## Что делает

Автоматизирует Instagram-аккаунт `@logistoria_edu` для продажи игр в логистике на международных рынках.

### Возможности:
1. **Автопостинг** — публикация фото/видео с подписями на EN/ES/RU
2. **Stories** — публикация Stories (опросы, анонсы, behind the scenes)
3. **Мониторинг заявок** — автоматическое распознавание заявок в комментариях и DM
4. **Уведомления** — отправка заявок на project@logistoria.com и в Telegram
5. **Контент-план** — 2-недельный план с охватом США, Европы, Латам, СНГ, Азии
6. **"Человеческое" поведение** — нерегулярные интервалы, рабочие часы, естественные ответы

## Архитектура

```
logistoria-instagram/
├── SKILL.md                    # Этот файл
├── HARNESS.md                  # Архитектура и контракты
├── README.md                   # Документация
├── instagram_poster.py         # Основной скрипт публикаций
├── lead_monitor.py             # Мониторинг заявок
├── content-plan.md             # Контент-план на 2 недели
├── .env.example                # Шаблон переменных окружения
├── images/                     # Фото для постов
│   ├── krossdok-01-full.jpg
│   ├── krossdok-02-full.jpg
│   └── ...
└── scripts/
    ├── post_now.py             # Публикация одного поста
    ├── schedule_posts.py       # Планировщик
    └── check_leads.py          # Проверка заявок
```

## Требования

- Python 3.9+
- `requests` (HTTP-запросы к Graph API)
- Facebook App с Instagram Graph API
- Instagram Business Account
- Access Token с разрешением `instagram_content_publish`

## Установка

```bash
git clone https://github.com/kimicito/logistoria-instagram.git
cd logistoria-instagram
cp .env.example .env
# Заполни .env своими токенами
pip install -r requirements.txt
```

## Конфигурация (.env)

```bash
INSTAGRAM_BUSINESS_ID=17841439161166578
ACCESS_TOKEN=EAAUQHQJVkVYBS...
FACEBOOK_PAGE_ID=1201091379758387

# Email-уведомления (опционально)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password

# Telegram для уведомлений
TELEGRAM_USER_ID=143946238
```

## Использование

### Публикация поста
```bash
python scripts/post_now.py --game krossdok --market en --type product
```

### Проверка заявок
```bash
python scripts/check_leads.py
```

### Запуск планировщика (cron)
```bash
# Проверять заявки каждые 2 часа
0 */2 * * * cd /path/to/logistoria-instagram && python scripts/check_leads.py

# Публиковать пост в 10:00 UTC (США утро)
0 10 * * * cd /path/to/logistoria-instagram && python scripts/post_now.py --auto

# Публиковать пост в 14:00 UTC (Европа день)
0 14 * * * cd /path/to/logistoria-instagram && python scripts/post_now.py --auto
```

## Контент-план

См. `content-plan.md` — 2 недели постов для рынков:
- **Пн** — СНГ/Россия (RU)
- **Вт** — США/Европа (EN)
- **Ср** — Латам/Испания (ES)
- **Чт** — Европа/Азия (EN)
- **Пт** — СНГ/Всемирный (RU/EN)

## Поведение "как человек"

- ⏰ Публикации только в рабочие часы целевых рынков
- 🎲 Случайные задержки ±30 минут от планового времени
- 💬 Ответы на заявки через 30 мин — 4 часа (не мгновенно)
- 📊 Максимум 1 пост + 2-3 Stories в день
- 🌍 Чередование языков в зависимости от времени

## Обработка заявок

### Что считать заявкой:
- "Сколько стоит?" / "How much?" / "¿Cuánto cuesta?"
- "Хочу купить" / "Want to buy" / "Quiero comprar"
- Запрос демо, доставки, Print&Play

### Алгоритм:
1. Автоответ в Instagram (через 30-60 мин)
2. Уведомление на project@logistoria.com
3. Уведомление в Telegram (OpenClaw)
4. Сбор статистики в `.lead_monitor_state.json`

## API Endpoints

### Публикация фото
```
POST https://graph.facebook.com/v18.0/{IG_BUSINESS_ID}/media
  ?image_url={URL}
  &caption={TEXT}
  &access_token={TOKEN}

POST https://graph.facebook.com/v18.0/{IG_BUSINESS_ID}/media_publish
  ?creation_id={CONTAINER_ID}
  &access_token={TOKEN}
```

### Получение комментариев
```
GET https://graph.facebook.com/v18.0/{MEDIA_ID}/comments
  ?fields=id,text,username,timestamp
  &access_token={TOKEN}
```

### Ответ на комментарий
```
POST https://graph.facebook.com/v18.0/{COMMENT_ID}/replies
  ?message={TEXT}
  &access_token={TOKEN}
```

## Лимиты API

- **Публикации:** ~25 постов/24ч (неофициально)
- **Stories:** ~100/24ч
- **Комментарии:** ~60/час
- **Rate limit:** 200 calls/hour/user

## Безопасность

- Токен хранится в `.env` (не в git!)
- `.env` добавлен в `.gitignore`
- Токен можно отозвать в любой момент в Facebook Developers

## Логи

```bash
# Просмотр логов
 tail -f logs/instagram.log

# Проверка последних публикаций
python scripts/post_now.py --list

# Проверка заявок за сегодня
python scripts/check_leads.py --today
```

## Доработка

При добавлении новых функций:
1. Обновить `SKILL.md` (этот файл)
2. Обновить `HARNESS.md` (архитектура)
3. Добавить тесты в `tests/`
4. Commit с тегом `[instagram]`

## Поддержка

- Email: project@logistoria.com
- Telegram: @tagartur
- GitHub Issues: https://github.com/kimicito/logistoria-instagram/issues
