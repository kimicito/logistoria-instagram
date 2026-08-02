#!/usr/bin/env python3
"""
Instagram Auto-Poster for Logistoria
"Человеческое" поведение: нерегулярные интервалы, рабочие часы, естественный контент
"""

import os
import time
import random
import requests
from datetime import datetime, timedelta
from pathlib import Path

# Конфигурация
INSTAGRAM_BUSINESS_ID = os.getenv('INSTAGRAM_BUSINESS_ID', '17841439161166578')
ACCESS_TOKEN = os.getenv('INSTAGRAM_ACCESS_TOKEN', '')
API_VERSION = 'v18.0'
BASE_URL = f'https://graph.facebook.com/{API_VERSION}'

# Часовые пояса целевых рынков
MARKETS = {
    'us_east': {'tz': -4, 'hours': (9, 17)},      # США Восток
    'us_west': {'tz': -7, 'hours': (9, 17)},      # США Запад
    'eu_central': {'tz': 2, 'hours': (9, 18)},     # Европа (Берлин)
    'uk': {'tz': 1, 'hours': (9, 17)},             # UK
    'au': {'tz': 10, 'hours': (9, 17)},            # Австралия
    'asia_sg': {'tz': 8, 'hours': (9, 18)},        # Сингапур/Азия
    'sa': {'tz': -3, 'hours': (9, 17)},            # Южная Америка
    'cis': {'tz': 3, 'hours': (10, 19)},           # СНГ/Россия
}

class InstagramPoster:
    def __init__(self):
        self.token = ACCESS_TOKEN
        self.account_id = INSTAGRAM_BUSINESS_ID
        
    def _request(self, endpoint, method='GET', data=None):
        """Выполнить запрос к Graph API"""
        url = f"{BASE_URL}/{endpoint}"
        params = {'access_token': self.token}
        
        try:
            if method == 'POST':
                response = requests.post(url, params=params, data=data)
            else:
                response = requests.get(url, params={**params, **(data or {})})
            
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ API Error: {e}")
            return None
    
    def get_account_info(self):
        """Получить информацию об аккаунте"""
        return self._request(f"{self.account_id}?fields=username,name,followers_count")
    
    def publish_photo(self, image_url, caption, hashtags=None):
        """
        Опубликовать фото с подписью
        
        Args:
            image_url: URL картинки (должен быть доступен публично)
            caption: Текст поста
            hashtags: Список хештегов
        """
        # Добавляем хештеги
        if hashtags:
            caption += "\n\n" + " ".join([f"#{tag}" for tag in hashtags])
        
        # Шаг 1: Создать медиа-контейнер
        container_data = {
            'image_url': image_url,
            'caption': caption,
            'access_token': self.token
        }
        
        result = self._request(
            f"{self.account_id}/media",
            method='POST',
            data=container_data
        )
        
        if not result or 'id' not in result:
            print("❌ Не удалось создать контейнер")
            return None
        
        container_id = result['id']
        print(f"📦 Контейнер создан: {container_id}")
        
        # Ждём обработки (обычно 1-5 секунд)
        time.sleep(5)
        
        # Шаг 2: Опубликовать
        publish_data = {
            'creation_id': container_id,
            'access_token': self.token
        }
        
        result = self._request(
            f"{self.account_id}/media_publish",
            method='POST',
            data=publish_data
        )
        
        if result and 'id' in result:
            print(f"✅ Пост опубликован: https://instagram.com/p/{result.get('id', '')}")
            return result['id']
        else:
            print(f"❌ Ошибка публикации: {result}")
            return None
    
    def publish_story(self, image_url):
        """Опубликовать Story"""
        # Для Story нужно видео или картинка с особой меткой
        # Instagram Graph API поддерживает Stories через containers
        container_data = {
            'image_url': image_url,
            'media_type': 'STORIES',
            'access_token': self.token
        }
        
        result = self._request(
            f"{self.account_id}/media",
            method='POST',
            data=container_data
        )
        
        if not result or 'id' not in result:
            return None
        
        # Публикация
        publish_data = {
            'creation_id': result['id'],
            'access_token': self.token
        }
        
        return self._request(
            f"{self.account_id}/media_publish",
            method='POST',
            data=publish_data
        )
    
    def get_comments(self, media_id):
        """Получить комментарии к посту"""
        return self._request(f"{media_id}/comments?fields=id,text,username,timestamp")
    
    def reply_comment(self, comment_id, message):
        """Ответить на комментарий"""
        data = {
            'message': message,
            'access_token': self.token
        }
        return self._request(f"{comment_id}/replies", method='POST', data=data)
    
    def get_insights(self, media_id):
        """Получить статистику поста"""
        metrics = 'impressions,reach,engagement,saved'
        return self._request(f"{media_id}/insights?metric={metrics}")

class ContentScheduler:
    """Планировщик с 'человеческим' поведением"""
    
    def __init__(self, poster: InstagramPoster):
        self.poster = poster
        self.posted_today = 0
        self.max_posts_per_day = 1
        self.max_stories_per_day = 2
        
    def should_post_now(self, market='us_east'):
        """Проверить, подходящее ли время для публикации"""
        now = datetime.utcnow()
        market_info = MARKETS.get(market, MARKETS['us_east'])
        
        # Местное время
        local_hour = (now.hour + market_info['tz']) % 24
        start_hour, end_hour = market_info['hours']
        
        # Только в рабочие часы
        if not (start_hour <= local_hour <= end_hour):
            return False
        
        # Не публиковать в обед (12:00-13:00) — люди обедают
        if 12 <= local_hour <= 13:
            return False
        
        # Не публиковать рано утром (до 10) и поздно вечером (после 16)
        if local_hour < 10 or local_hour > 16:
            return False
        
        return True
    
    def get_random_posting_time(self, market='us_east'):
        """Получить случайное время публикации с 'человеческими' колебаниями"""
        market_info = MARKETS.get(market, MARKETS['us_east'])
        start_hour, end_hour = market_info['hours']
        
        # Базовое время + случайное отклонение ±30 минут
        base_hour = random.randint(start_hour + 1, end_hour - 2)
        base_minute = random.randint(0, 59)
        
        # Добавляем "человеческую" нерегулярность
        jitter = random.randint(-30, 30)
        
        return base_hour, base_minute, jitter
    
    def human_delay(self):
        """"Человеческая" задержка между действиями"""
        # 30 секунд - 2 минуты (не мгновенно)
        delay = random.uniform(30, 120)
        time.sleep(delay)

# Шаблоны постов для разных рынков
POST_TEMPLATES = {
    'en': {
        'product_showcase': [
            "🎲 {game_name} — {short_desc}\n\n"
            "Perfect for: {audience}\n"
            "Format: {format}\n"
            "Duration: {duration}\n\n"
            "💡 Real result: {result}\n\n"
            "📩 DM us for a demo or order: link in bio\n"
            "🌐 Available worldwide with Print&Play",
            
            "📦 New arrival: {game_name}\n\n"
            "{short_desc}\n\n"
            "✅ {feature1}\n"
            "✅ {feature2}\n"
            "✅ {feature3}\n\n"
            "🎯 Who needs this: {audience}\n\n"
            "📩 Request a quote: project@logistoria.com",
        ],
        'client_case': [
            "🏆 Case: {company} trained {num} employees with {game_name}\n\n"
            "Result: {result}\n\n"
            "💬 '{quote}'\n— {position}, {company}\n\n"
            "🎲 Ready to level up your team?\n"
            "📩 project@logistoria.com",
        ],
        'educational': [
            "💡 Did you know?\n\n"
            "{fact}\n\n"
            "🎲 Our game {game_name} helps teams understand this in {duration}\n\n"
            "🔗 Learn more: logistoria.com\n"
            "📩 Questions? project@logistoria.com",
        ],
    },
    'es': {
        'product_showcase': [
            "🎲 {game_name} — {short_desc}\n\n"
            "Perfecto para: {audience}\n"
            "Formato: {format}\n"
            "Duración: {duration}\n\n"
            "💡 Resultado real: {result}\n\n"
            "📩 Escríbenos para una demo\n"
            "🌐 Disponible worldwide con Print&Play",
        ],
    },
    'ru': {
        'product_showcase': [
            "🎲 {game_name} — {short_desc}\n\n"
            "Для кого: {audience}\n"
            "Формат: {format}\n"
            "Длительность: {duration}\n\n"
            "💡 Результат: {result}\n\n"
            "📩 Заявки: project@logistoria.com\n"
            "🌐 Доставка в СНГ и worldwide (Print&Play)",
        ],
    }
}

# Данные об играх
GAMES = {
    'krossdok': {
        'name_en': 'Krossdok',
        'name_es': 'Krossdok',
        'name_ru': 'Krossdok',
        'short_desc_en': 'The best supply chain simulation game',
        'short_desc_es': 'La mejor simulación de cadena de suministro',
        'short_desc_ru': 'Лучшая игра-симуляция цепочки поставок',
        'audience_en': 'logistics teams, universities, supply chain managers',
        'audience_es': 'equipos de logística, universidades',
        'audience_ru': 'логисты, ВУЗы, руководители цепочек поставок',
        'format': 'Board Game / Online',
        'duration': '2-4 hours',
        'result_en': '950+ copies sold, used by TOP-20 companies',
        'result_es': '950+ copias vendidas',
        'result_ru': '950+ проданных копий, ТОП-20 компаний',
    },
    'kadena': {
        'name_en': 'Kadena',
        'name_es': 'Kadena',
        'name_ru': 'Kadena',
        'short_desc_en': 'The most famous logistics game',
        'short_desc_es': 'El juego de logística más famoso',
        'short_desc_ru': 'Самая известная логистическая игра',
        'audience_en': 'students, corporate training',
        'audience_es': 'estudiantes, formación corporativa',
        'audience_ru': 'студенты, корпоративное обучение',
        'format': 'Online',
        'duration': '1-2 hours',
        'result_en': '4000+ students trained',
        'result_es': '4000+ estudiantes formados',
        'result_ru': '4000+ обученных студентов',
    },
    'storewars': {
        'name_en': 'Storewars',
        'name_es': 'Storewars',
        'name_ru': 'Storewars',
        'short_desc_en': 'FMCG simulation: manufacturer vs retailer',
        'short_desc_es': 'Simulación FMCG: fabricante vs minorista',
        'short_desc_ru': 'FMCG симуляция: производитель vs ритейлер',
        'audience_en': 'FMCG companies, retail chains',
        'audience_es': 'empresas FMCG, cadenas minoristas',
        'audience_ru': 'FMCG компании, ритейл',
        'format': 'Online + Debrief',
        'duration': '2-3 hours',
        'result_en': 'Improved negotiation skills',
        'result_es': 'Mejora en habilidades de negociación',
        'result_ru': 'Улучшение навыков переговоров',
    },
    'beer_game': {
        'name_en': 'The Beer Game',
        'name_es': 'El Juego de la Cerveza',
        'name_ru': 'Игра Пивная',
        'short_desc_en': 'The legendary supply chain classic',
        'short_desc_es': 'El clásico legendario de la cadena de suministro',
        'short_desc_ru': 'Легендарная классика цепочки поставок',
        'audience_en': 'executives, supply chain professionals',
        'audience_es': 'ejecutivos, profesionales de supply chain',
        'audience_ru': 'топ-менеджмент, специалисты по цепочкам поставок',
        'format': 'Board Game',
        'duration': '2-4 hours',
        'result_en': '110+ trainings conducted',
        'result_es': '110+ formaciones realizadas',
        'result_ru': '110+ проведённых тренингов',
    },
    'market_plays': {
        'name_en': 'Market Plays',
        'name_es': 'Market Plays',
        'name_ru': 'Market Plays',
        'short_desc_en': 'Learn to sell on marketplaces',
        'short_desc_es': 'Aprende a vender en marketplaces',
        'short_desc_ru': 'Учитесь продавать на маркетплейсах',
        'audience_en': 'e-commerce teams, marketplace sellers',
        'audience_es': 'equipos de e-commerce, vendedores',
        'audience_ru': 'e-commerce команды, селлеры',
        'format': 'Board Game',
        'duration': '1-2 hours',
        'result_en': 'Learn marketplace mechanics',
        'result_es': 'Aprende mecánicas de marketplaces',
        'result_ru': 'Изучение механик маркетплейсов',
    },
    'heroes_rack': {
        'name_en': 'Heroes of the Rack',
        'name_es': 'Héroes del Rack',
        'name_ru': 'Герои Стеллажа',
        'short_desc_en': 'First warehouse logistics game',
        'short_desc_es': 'Primer juego de logística de almacén',
        'short_desc_ru': 'Первая игра по складской логистике',
        'audience_en': 'warehouse managers, 3PL operators',
        'audience_es': 'gerentes de almacén, operadores 3PL',
        'audience_ru': 'складские менеджеры, 3PL-операторы',
        'format': 'Board Game',
        'duration': '2-3 hours',
        'result_en': 'Master warehouse operations',
        'result_es': 'Domina operaciones de almacén',
        'result_ru': 'Освоение складских операций',
    },
}

# Хештеги по рынкам
HASHTAGS = {
    'en': ['seriousgames', 'logistics', 'supplychain', 'gamification', 'corporatetraining', 
           'boardgames', 'logisticsgame', 'supplychainmanagement', 'elearning', 'businessgame'],
    'es': ['juegosserios', 'logistica', 'cadenadesuministro', 'gamificacion', 'formacion',
           'juegosdemesa', 'logistica', 'supplychain', 'capacitacion', 'negocios'],
    'ru': ['серьезныеигры', 'логистика', 'цепочкипоставок', 'геймификация', 'обучение',
           'настольныеигры', 'логистическаяигра', 'supplychain', 'корпоративноеобучение'],
}

def generate_post(game_key, market='en', post_type='product_showcase'):
    """Сгенерировать пост для конкретной игры и рынка"""
    game = GAMES.get(game_key)
    if not game:
        return None
    
    templates = POST_TEMPLATES.get(market, POST_TEMPLATES['en']).get(post_type, [])
    if not templates:
        templates = POST_TEMPLATES['en'][post_type]
    
    template = random.choice(templates)
    
    # Форматируем шаблон
    post = template.format(
        game_name=game[f'name_{market}'],
        short_desc=game[f'short_desc_{market}'],
        audience=game[f'audience_{market}'],
        format=game['format'],
        duration=game['duration'],
        result=game[f'result_{market}'],
        feature1='Hands-on learning experience',
        feature2='Real supply chain scenarios',
        feature3='Immediate skill application',
    )
    
    hashtags = HASHTAGS.get(market, HASHTAGS['en'])
    
    return post, hashtags

if __name__ == '__main__':
    # Тест
    poster = InstagramPoster()
    scheduler = ContentScheduler(poster)
    
    print("📊 Информация об аккаунте:")
    info = poster.get_account_info()
    print(info)
    
    print("\n📝 Пример поста (EN):")
    post, tags = generate_post('krossdok', 'en')
    print(post)
    print(f"\n🏷️ Хештеги: {' '.join(['#' + t for t in tags])}")
