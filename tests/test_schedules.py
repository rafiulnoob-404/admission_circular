"""Regression checks for the 11 and 14 November schedule updates (stdlib only)."""
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
        self.assertIn('গুচ্ছ (GST) — ২০ বিশ্ববিদ্যালয়', CALENDAR)

    def test_unverified_eligibility_is_not_automatically_judged(self):
        entries = json.loads(re.search(r'var UNIS = (\[.*?\]);', ELIGIBILITY).group(1))
        for short in ['RU', 'MIST']:
            self.assertEqual(UNIS[short]['elig_rules'], [])
            self.assertEqual(next(e for e in entries if e['short'] == short)['rules'], [])

    def test_all_cards_remain_and_new_ones_are_mirrored(self):
        self.assertEqual(len(UNIS), 22)
        self.assertEqual(len(re.findall(r'<article\b[^>]*data-file=', INDEX)), 22)
        order = re.findall(r'<article\b[^>]*data-file="([^"]+)"', INDEX)
        self.assertEqual(order, [u['short'] for u in DATA['universities']])
        checker = json.loads(re.search(r'var UNIS = (\[.*?\]);', ELIGIBILITY).group(1))
        self.assertEqual([e['short'] for e in checker], order)
        switch = json.loads(re.search(r'var SWITCH = (\{.*?\});', ELIGIBILITY).group(1))
        for short in ['AGRI', 'HSTU', 'AAUB']:
            with self.subTest(short=short):
                self.assertEqual(UNIS[short]['elig_rules'], [])
                self.assertEqual(next(e for e in checker if e['short'] == short)['rules'], [])
                self.assertIn(short, switch)
                self.assertIn('class="refpill"', card(short))
                self.assertNotIn('hero-date', card(short))
                self.assertIn(UNIS[short]['source_url']['url'], card(short))

    def test_new_universities_dates_reach_the_calendar(self):
        for date, university in [('2027-01-02', 'কৃষি গুচ্ছ (৯ বিশ্ববিদ্যালয়)'),
                                 ('2027-01-24', 'হাবিপ্রবি (HSTU)'),
                                 ('2027-01-30', 'অ্যাভিয়েশন অ্যান্ড অ্যারোস্পেস বিশ্ববিদ্যালয় (AAUB)')]:
            with self.subTest(university=university):
                self.assertRegex(CALENDAR, r'\{s:"' + date + r'"[^\n]*u:"' + re.escape(university) + r'"')

    def test_14_november_corrections(self):
        self.assertEqual(DATA['updated'], '১৪ নভেম্বর ২০২৬')
        self.assertEqual(UNIS['AAUB']['source_url']['kind'], 'official')
        self.assertEqual(UNIS['KhU']['apply_start'], '৫ জানুয়ারি ২০২৭')
        self.assertIn('৫ জানুয়ারি ২০২৭', card('KhU'))
        self.assertIn('১৬,০৯৩', card('GST'))
        self.assertIn('১,২০০', card('DU'))
        for page in [INDEX, CALENDAR, ELIGIBILITY]:
            self.assertIn('সর্বশেষ আপডেট: <span class="bd">১৪ নভেম্বর ২০২৬</span>', page)
            self.assertIn('সর্বশেষ (১৪ নভেম্বর ২০২৬):', page)


if __name__ == '__main__':
    unittest.main()
