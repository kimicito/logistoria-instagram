#!/usr/bin/env python3
"""Утилита для публикации поста прямо сейчас"""
import sys
sys.path.insert(0, '..')
from instagram_poster import InstagramPoster, generate_post
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--game', default='krossdok')
parser.add_argument('--market', default='en')
parser.add_argument('--type', default='product_showcase')
parser.add_argument('--test', action='store_true', help='Test mode (no actual posting)')
args = parser.parse_args()

poster = InstagramPoster()
post, tags = generate_post(args.game, args.market, args.type)

print("="*60)
print(f"🎲 POST PREVIEW ({args.market.upper()})")
print("="*60)
print(post)
print(f"\n🏷️ Tags: {' '.join(['#'+t for t in tags])}")
print("="*60)

if args.test:
    print("\n✅ Test mode — not posted")
else:
    # Для реальной публикации нужен публичный URL фото
    print("\n⚠️  To post: provide --image-url with publicly accessible URL")
