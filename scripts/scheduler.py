#!/usr/bin/env python3
"""
Instagram Auto-Poster Scheduler for Logistoria
3 languages: EN / ES / RU
Markets: US, EU, LatAm, CIS, Asia
"""

import os
import sys
import random
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from instagram_poster import InstagramPoster, generate_post

# Контент-план на 2 недели (14 дней)
# Каждый день: 1 пост на основном языке + опционально Stories

CONTENT_PLAN = [
    # Week 1
    {
        "day": 1, "date": "2026-08-04", "market": "cis", "lang": "ru",
        "game": "krossdok", "type": "product_showcase",
        "image": "https://i.imgur.com/jWzP4Ru.jpeg",
        "time_utc": "07:00",  # 10:00 MSK
        "notes": "Krossdok — лидер продаж, СНГ рынок"
    },
    {
        "day": 2, "date": "2026-08-05", "market": "us", "lang": "en",
        "game": "beer_game", "type": "product_showcase",
        "image": "https://i.imgur.com/mqmeUO7.jpeg",
        "time_utc": "14:00",  # 10:00 EDT
        "notes": "The Beer Game — классика MIT, США"
    },
    {
        "day": 3, "date": "2026-08-06", "market": "latam", "lang": "es",
        "game": "storewars", "type": "product_showcase",
        "image": "https://i.imgur.com/eIcDj5q.jpeg",
        "time_utc": "13:00",  # 10:00 BRT
        "notes": "Storewars — FMCG, Латам"
    },
    {
        "day": 4, "date": "2026-08-07", "market": "eu", "lang": "en",
        "game": "kadena", "type": "educational",
        "image": "https://i.imgur.com/asuUoWK.jpeg",
        "time_utc": "08:00",  # 10:00 CEST
        "notes": "Kadena — онлайн обучение, Европа"
    },
    {
        "day": 5, "date": "2026-08-08", "market": "cis", "lang": "ru",
        "game": "heroes_rack", "type": "product_showcase",
        "image": "https://i.imgur.com/IRhzj3O.jpeg",
        "time_utc": "07:00",
        "notes": "Heroes of the Rack — склад, СНГ"
    },
    {
        "day": 6, "date": "2026-08-09", "market": "asia", "lang": "en",
        "game": "market_plays", "type": "product_showcase",
        "image": "https://i.imgur.com/WVC1itl.jpeg",
        "time_utc": "02:00",  # 10:00 SGT
        "notes": "Market Plays — маркетплейсы, Азия"
    },
    {
        "day": 7, "date": "2026-08-10", "market": "us", "lang": "en",
        "game": "krossdok", "type": "client_case",
        "image": "https://i.imgur.com/QWS2rSV.jpeg",
        "time_utc": "14:00",
        "notes": "Кейс Suzuki, США"
    },
    # Week 2
    {
        "day": 8, "date": "2026-08-11", "market": "cis", "lang": "ru",
        "game": "beer_game", "type": "product_showcase",
        "image": "https://i.imgur.com/H3utfyi.jpeg",
        "time_utc": "07:00",
        "notes": "Beer Game для ВУЗов, СНГ"
    },
    {
        "day": 9, "date": "2026-08-12", "market": "eu", "lang": "en",
        "game": "krossdok", "type": "educational",
        "image": "https://i.imgur.com/gKsRaO7.jpeg",
        "time_utc": "08:00",
        "notes": "Почему игры лучше лекций, Европа"
    },
    {
        "day": 10, "date": "2026-08-13", "market": "latam", "lang": "es",
        "game": "kadena", "type": "product_showcase",
        "image": "https://i.imgur.com/6tAqci6.jpeg",
        "time_utc": "13:00",
        "notes": "Kadena — университеты, Латам"
    },
    {
        "day": 11, "date": "2026-08-14", "market": "us", "lang": "en",
        "game": "storewars", "type": "product_showcase",
        "image": "https://i.imgur.com/jWzP4Ru.jpeg",
        "time_utc": "14:00",
        "notes": "Storewars — FMCG, США"
    },
    {
        "day": 12, "date": "2026-08-15", "market": "cis", "lang": "ru",
        "game": "market_plays", "type": "product_showcase",
        "image": "https://i.imgur.com/mqmeUO7.jpeg",
        "time_utc": "07:00",
        "notes": "Market Plays — маркетплейсы, СНГ"
    },
    {
        "day": 13, "date": "2026-08-16", "market": "asia", "lang": "en",
        "game": "heroes_rack", "type": "product_showcase",
        "image": "https://i.imgur.com/eIcDj5q.jpeg",
        "time_utc": "02:00",
        "notes": "Heroes of the Rack — 3PL, Азия"
    },
    {
        "day": 14, "date": "2026-08-17", "market": "eu", "lang": "en",
        "game": "krossdok", "type": "client_case",
        "image": "https://i.imgur.com/asuUoWK.jpeg",
        "time_utc": "08:00",
        "notes": "Print&Play — доставка за 1 день, Европа"
    },
]

class AutoScheduler:
    def __init__(self):
        self.poster = InstagramPoster()
        self.state_file = Path(__file__).parent / '.scheduler_state.json'
        self.posted = self._load_state()
        
    def _load_state(self):
        if self.state_file.exists():
            with open(self.state_file) as f:
                return set(json.load(f))
        return set()
    
    def _save_state(self):
        with open(self.state_file, 'w') as f:
            json.dump(list(self.posted), f)
    
    def get_todays_post(self):
        """Получить пост для сегодняшнего дня"""
        today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        
        for item in CONTENT_PLAN:
            if item['date'] == today and item['date'] not in self.posted:
                return item
        return None
    
    def post_today(self, dry_run=False):
        """Опубликовать пост на сегодня"""
        item = self.get_todays_post()
        
        if not item:
            print(f"📭 No post scheduled for today ({datetime.now(timezone.utc).date()})")
            return None
        
        print(f"📅 Post for {item['date']}: {item['game']} ({item['lang'].upper()})")
        print(f"🎯 Market: {item['market']} | Time UTC: {item['time_utc']}")
        print(f"📝 {item['notes']}")
        
        # Генерируем пост
        post_text, hashtags = generate_post(item['game'], item['lang'], item['type'])
        
        print(f"\n{'='*60}")
        print(post_text[:500] + "..." if len(post_text) > 500 else post_text)
        print(f"\n🏷️ {' '.join(['#'+h for h in hashtags[:5]])}")
        print(f"{'='*60}")
        
        if dry_run:
            print("\n✅ DRY RUN — not posted")
            return None
        
        # Публикуем
        result = self.poster.publish_photo(item['image'], post_text, hashtags)
        
        if result:
            self.posted.add(item['date'])
            self._save_state()
            print(f"✅ Posted! ID: {result}")
            return result
        else:
            print("❌ Failed to post")
            return None
    
    def preview_week(self):
        """Показать план на неделю"""
        print("📅 CONTENT PLAN (Next 7 Days)")
        print("="*60)
        
        today = datetime.now(timezone.utc).date()
        
        for item in CONTENT_PLAN:
            item_date = datetime.strptime(item['date'], '%Y-%m-%d').date()
            if today <= item_date <= today + timedelta(days=7):
                status = "✅" if item['date'] in self.posted else "⏳"
                print(f"{status} {item['date']} | {item['time_utc']} UTC | "
                      f"{item['lang'].upper()} | {item['game']} | {item['market']}")
                print(f"   📝 {item['notes']}")
                print()

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true', help='Preview only')
    parser.add_argument('--preview-week', action='store_true', help='Show week plan')
    args = parser.parse_args()
    
    scheduler = AutoScheduler()
    
    if args.preview_week:
        scheduler.preview_week()
    else:
        scheduler.post_today(dry_run=args.dry_run)

if __name__ == '__main__':
    main()
