#!/usr/bin/env python3
"""
Instagram Lead Monitor — отслеживание заявок из Instagram
Отправляет уведомления на email и в Telegram
"""

import os
import re
import json
import time
import smtplib
import requests
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

# Конфигурация
INSTAGRAM_BUSINESS_ID = os.getenv('INSTAGRAM_BUSINESS_ID', '17841439161166578')
ACCESS_TOKEN = os.getenv('INSTAGRAM_ACCESS_TOKEN', '')
API_VERSION = 'v18.0'
BASE_URL = f'https://graph.facebook.com/{API_VERSION}'

# Email для уведомлений
NOTIFICATION_EMAIL = 'project@logistoria.com'
SMTP_SERVER = os.getenv('SMTP_SERVER', '')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER = os.getenv('SMTP_USER', '')
SMTP_PASS = os.getenv('SMTP_PASS', '')

# Telegram для уведомлений (через OpenClaw)
TELEGRAM_USER_ID = '143946238'  # ID Артура

# Файл для хранения обработанных комментариев
STATE_FILE = Path(__file__).parent / '.lead_monitor_state.json'

# Ключевые слова заявок (на разных языках)
LEAD_KEYWORDS = {
    'buy': ['buy', 'purchase', 'order', 'how much', 'price', 'cost', 'quote', 'get one', 'interested'],
    'demo': ['demo', 'trial', 'test', 'try', 'sample', 'presentation'],
    'shipping': ['shipping', 'delivery', 'send to', 'available in', 'worldwide', 'print&play'],
    'ru': ['купить', 'заказать', 'сколько стоит', 'цена', 'стоимость', 'доставка', 'в наличии', 'хочу', 'заявка'],
    'es': ['comprar', 'pedir', 'cuánto cuesta', 'precio', 'costo', 'envío', 'disponible', 'quiero'],
    'fr': ['acheter', 'commander', 'combien', 'prix', 'coût', 'livraison', 'disponible'],
    'contact': ['email', 'contact', 'write to', 'reach out', 'connect', 'message'],
}

class LeadMonitor:
    def __init__(self):
        self.token = ACCESS_TOKEN
        self.account_id = INSTAGRAM_BUSINESS_ID
        self.processed_ids = self._load_state()
        
    def _load_state(self):
        """Загрузить список обработанных комментариев"""
        if STATE_FILE.exists():
            with open(STATE_FILE, 'r') as f:
                return set(json.load(f))
        return set()
    
    def _save_state(self):
        """Сохранить список обработанных комментариев"""
        with open(STATE_FILE, 'w') as f:
            json.dump(list(self.processed_ids), f)
    
    def _api_request(self, endpoint):
        """Запрос к Graph API"""
        url = f"{BASE_URL}/{endpoint}"
        params = {'access_token': self.token}
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ API Error: {e}")
            return None
    
    def is_lead(self, text):
        """
        Определить, является ли комментарий заявкой
        
        Returns: (is_lead, lead_type, confidence)
        """
        text_lower = text.lower()
        
        # Проверяем ключевые слова
        for category, keywords in LEAD_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    return True, category, 'high'
        
        # Проверяем паттерны
        patterns = [
            r'\b\d+\s*(?:people|persons|participants|players|employees)',
            r'(?:need|want|looking for)\s+(?:game|training|simulation)',
            r'(?:company|university|college|organization)\s+(?:training|course)',
        ]
        
        for pattern in patterns:
            if re.search(pattern, text_lower):
                return True, 'custom', 'medium'
        
        return False, None, 'low'
    
    def get_recent_media(self, hours=24):
        """Получить недавние публикации"""
        since = int((datetime.now() - timedelta(hours=hours)).timestamp())
        result = self._api_request(
            f"{self.account_id}/media?fields=id,caption,permalink,timestamp&since={since}"
        )
        return result.get('data', []) if result else []
    
    def get_comments(self, media_id):
        """Получить комментарии к публикации"""
        result = self._api_request(
            f"{media_id}/comments?fields=id,text,username,timestamp,replies"
        )
        return result.get('data', []) if result else []
    
    def reply_to_comment(self, comment_id, message):
        """Ответить на комментарий"""
        url = f"{BASE_URL}/{comment_id}/replies"
        data = {
            'message': message,
            'access_token': self.token
        }
        try:
            response = requests.post(url, data=data, timeout=10)
            return response.json()
        except Exception as e:
            print(f"❌ Error replying: {e}")
            return None
    
    def send_notification(self, lead_info):
        """
        Отправить уведомление о заявке
        
        lead_info: dict с информацией о заявке
        """
        # Формируем сообщение
        message = f"""
🎯 НОВАЯ ЗАЯВКА С INSTAGRAM

📱 Пост: {lead_info.get('post_url', 'N/A')}
👤 Пользователь: @{lead_info.get('username', 'unknown')}
💬 Комментарий: {lead_info.get('text', '')}
🏷️ Тип: {lead_info.get('lead_type', 'unknown')}
⏰ Время: {lead_info.get('timestamp', 'now')}

✅ Действия:
1. Ответить пользователю в Instagram
2. Запросить: страну, количество участников, формат
3. Отправить коммерческое предложение

📧 Email для связи: {NOTIFICATION_EMAIL}
"""
        
        # Отправляем в Telegram (через OpenClaw)
        self._notify_telegram(message)
        
        # Отправляем на email (если настроен SMTP)
        if SMTP_SERVER:
            self._notify_email(lead_info, message)
    
    def _notify_telegram(self, message):
        """Отправить уведомление в Telegram через OpenClaw"""
        # Это будет работать через OpenClaw message tool
        # Пока сохраняем в лог
        print(f"📨 Telegram notification:\n{message}")
        
        # В реальности здесь будет:
        # message(action="send", target=TELEGRAM_USER_ID, message=message)
    
    def _notify_email(self, lead_info, message):
        """Отправить уведомление на email"""
        try:
            msg = MIMEMultipart()
            msg['From'] = SMTP_USER
            msg['To'] = NOTIFICATION_EMAIL
            msg['Subject'] = f"🎯 Instagram Lead: @{lead_info.get('username', 'unknown')}"
            
            msg.attach(MIMEText(message, 'plain', 'utf-8'))
            
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
            server.quit()
            
            print(f"✅ Email sent to {NOTIFICATION_EMAIL}")
        except Exception as e:
            print(f"❌ Email error: {e}")
    
    def process_leads(self):
        """Основной процесс: проверить новые комментарии и найти заявки"""
        print(f"🔍 Checking for new leads... {datetime.now()}")
        
        # Получаем недавние публикации
        media_list = self.get_recent_media(hours=48)
        
        leads_found = 0
        
        for media in media_list:
            media_id = media['id']
            comments = self.get_comments(media_id)
            
            for comment in comments:
                comment_id = comment['id']
                
                # Пропускаем уже обработанные
                if comment_id in self.processed_ids:
                    continue
                
                # Проверяем, является ли заявкой
                is_lead, lead_type, confidence = self.is_lead(comment['text'])
                
                if is_lead and confidence in ('high', 'medium'):
                    lead_info = {
                        'post_url': media.get('permalink', ''),
                        'username': comment.get('username', 'unknown'),
                        'text': comment['text'],
                        'lead_type': lead_type,
                        'timestamp': comment.get('timestamp', 'now'),
                        'comment_id': comment_id,
                    }
                    
                    # Отправляем уведомление
                    self.send_notification(lead_info)
                    
                    # Отвечаем в Instagram (через 30-60 минут)
                    reply_text = self._generate_reply(lead_type)
                    # self.reply_to_comment(comment_id, reply_text)  # Раскомментировать для автоответа
                    
                    leads_found += 1
                    print(f"✅ Lead found: @{comment.get('username')} - {lead_type}")
                
                # Помечаем как обработанное
                self.processed_ids.add(comment_id)
        
        # Сохраняем состояние
        self._save_state()
        
        print(f"📊 Total leads found: {leads_found}")
        return leads_found
    
    def _generate_reply(self, lead_type):
        """Сгенерировать ответ на заявку"""
        replies = {
            'buy': "Thanks for your interest! 🎲\n\nTo prepare a quote, we need:\n1. Country for delivery\n2. Number of participants\n3. Format: physical box / Print&Play / online\n\nPlease email us: project@logistoria.com",
            'demo': "We'd love to show you a demo! 🎯\n\nWe can arrange:\n• Online demo session (30 min)\n• Pilot game for your team\n• Free Print&Play sample\n\nEmail us: project@logistoria.com",
            'shipping': "We ship worldwide! 🌍\n\nOptions:\n• Physical boxes: 3-14 days depending on country\n• Print&Play: PDF within 24 hours\n• Online: immediate access\n\nFor specific delivery options: project@logistoria.com",
            'ru': "Спасибо за интерес! 🎲\n\nДля расчёта стоимости нужно:\n1. Страна доставки\n2. Количество участников\n3. Формат: коробка / Print&Play / онлайн\n\nПишите: project@logistoria.com",
            'es': "¡Gracias por tu interés! 🎲\n\nPara preparar una cotización:\n1. País de entrega\n2. Número de participantes\n3. Formato: caja física / Print&Play / online\n\nEscríbenos: project@logistoria.com",
            'default': "Thanks for reaching out! 🎲\n\nFor pricing and availability:\n📧 project@logistoria.com\n\nWe typically respond within 24 hours.",
        }
        
        return replies.get(lead_type, replies['default'])

def main():
    """Запуск мониторинга"""
    monitor = LeadMonitor()
    
    # Проверяем каждые 2 часа
    while True:
        try:
            monitor.process_leads()
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Ждём 2 часа (с "человеческой" вариативностью)
        delay = 7200 + random.randint(-300, 300)  # 2 часа ± 5 минут
        print(f"⏳ Next check in {delay//60} minutes...")
        time.sleep(delay)

if __name__ == '__main__':
    # Для теста — однократный запуск
    monitor = LeadMonitor()
    monitor.process_leads()
