"""Regression checks for the 11 November schedule update (stdlib only)."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / 'index.html').read_text(encoding='utf-8')
CALENDAR = (ROOT / 'calendar.html').read_text(encoding='utf-8')
ELIGIBILITY = (ROOT / 'eligibility.html').read_text(encoding='utf-8')
DATA = json.loads(re.search(r'<script type="application/json" id="card-data">(.*?)</script>', INDEX, re.S).group(1))
UNIS = {u['short']: u for u in DATA['universities']}


def card(short):
    return re.search(r'<article\b[^>]*data-file="' + short + r'"[^>]*>.*?</article>', INDEX, re.S).group()


class Schedules(unittest.TestCase):
    def test_changed_exam_dates_in_card_and_mirror(self):
        for short, date in {'RU': '১২–২০ ফেব্রুয়ারি ২০২৭', 'KhU': '৪–৫ ফেব্রুয়ারি ২০২৭',
                            'MIST': '৫–৬ ফেব্রুয়ারি ২০২৭', 'JUST': '১৯–২৭ মার্চ ২০২৭ (জিএসটি সূচি)'}.items():
            with self.subTest(short=short):
                self.assertEqual(UNIS[short]['exam_date'], date)
                self.assertIn(date, card(short))

    def test_application_windows_and_sources(self):
        for short, text in {'RU': '১৫ – ৩০ নভেম্বর ২০২৬', 'CU': '১০ ডিসেম্বর ২০২৬ – ১০ জানুয়ারি ২০২৭',
                            'JnU': '২৫ নভেম্বর – ১০ ডিসেম্বর ২০২৬', 'CoU': '১০–৩১ ডিসেম্বর ২০২৬',
                            'MIST': '২১ জানুয়ারি ২০২৭'}.items():
            with self.subTest(short=short):
                self.assertIn(text, card(short))
                self.assertIn(UNIS[short]['source_url']['url'], card(short))

    def test_moved_events_and_removed_dates(self):
        for university, dates in {'রাজশাহী বিশ্ববিদ্যালয়': ['2027-02-12', '2027-02-13', '2027-02-20'],
                                  'খুলনা বিশ্ববিদ্যালয়': ['2027-02-04', '2027-02-05'],
                                  'মিস্ট (MIST)': ['2027-02-05', '2027-02-06']}.items():
            events = re.findall(r'\{s:"(\d{4}-\d\d-\d\d)"[^\n]*u:"' + re.escape(university) + r'"', CALENDAR)
            self.assertEqual(sorted(events), dates)
        self.assertNotIn('2027-01-24",e:"2027-01-26",u:"যশোর', CALENDAR)
        self.assertIn('গুচ্ছ (GST) — যবিপ্রবিসহ', CALENDAR)

    def test_unverified_eligibility_is_not_automatically_judged(self):
        entries = json.loads(re.search(r'var UNIS = (\[.*?\]);', ELIGIBILITY).group(1))
        for short in ['RU', 'MIST']:
            self.assertEqual(UNIS[short]['elig_rules'], [])
            self.assertEqual(next(e for e in entries if e['short'] == short)['rules'], [])

    def test_all_16_cards_remain(self):
        self.assertEqual(len(UNIS), 16)
        self.assertEqual(len(re.findall(r'<article\b[^>]*data-file=', INDEX)), 16)


if __name__ == '__main__':
    unittest.main()
