#!/usr/bin/env python3
"""Утилита для проверки заявок"""
import sys
sys.path.insert(0, '..')
from lead_monitor import LeadMonitor
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--today', action='store_true')
args = parser.parse_args()

monitor = LeadMonitor()
count = monitor.process_leads()

if count > 0:
    print(f"\n🎯 Found {count} new leads!")
else:
    print("\n📭 No new leads")
