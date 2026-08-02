# Logistoria Instagram Automation

🎲 Автоматизация Instagram для продажи игр в логистике на международных рынках.

## Быстрый старт

```bash
git clone https://github.com/kimicito/logistoria-instagram.git
cd logistoria-instagram
cp .env.example .env
# Отредактируй .env — добавь свои токены
pip install -r requirements.txt
python scripts/post_now.py --test
```

## Возможности

- ✅ Автопостинг фото и Stories
- ✅ Контент-план на 2 недели (EN/ES/RU)
- ✅ Мониторинг заявок из комментариев
- ✅ Уведомления на email и в Telegram
- ✅ "Человеческое" поведение (нерегулярные интервалы)

## Структура

```
.
├── instagram_poster.py      # Публикация постов
├── lead_monitor.py          # Мониторинг заявок
├── content-plan.md          # Контент-план
├── SKILL.md                 # Документация skill
├── HARNESS.md               # Архитектура проекта
├── images/                  # Фото для постов
└── scripts/                 # Утилиты
```

## Лицензия

MIT © Logistoria
