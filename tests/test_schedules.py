"""Regression checks for the 11 and 14 November schedule updates (stdlib only)."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / 'index.html').read_text(encoding='utf-8')
CALENDAR = (ROOT / 'calendar.html').read_text(encoding='utf-8') + (ROOT / 'data/calendar.json').read_text(encoding='utf-8')
ELIGIBILITY = (ROOT / 'eligibility.html').read_text(encoding='utf-8')
DATA = json.loads((ROOT / 'data/universities.json').read_text())
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
        for short, text in {'RU': '৩০ নভেম্বর ২০২৬', 'CU': '১০ ডিসেম্বর ২০২৬ – ১০ জানুয়ারি ২০২৭',
                            'JnU': '২৫ নভেম্বর ২০২৬ দুপুর ১২টা – ১০ ডিসেম্বর ২০২৬ রাত ১১:৫৯', 'CoU': '১০–৩১ ডিসেম্বর ২০২৬',
                            'MIST': '২১ জানুয়ারি ২০২৭'}.items():
            with self.subTest(short=short):
                self.assertIn(text, card(short))
                self.assertIn(UNIS[short]['source_url']['url'], (ROOT / UNIS[short]['details_page']).read_text())

    def test_moved_events_and_removed_dates(self):
        for university, dates in {'রাজশাহী বিশ্ববিদ্যালয়': ['2027-02-12', '2027-02-13', '2027-02-20'],
                                  'খুলনা বিশ্ববিদ্যালয়': ['2027-02-04', '2027-02-05'],
                                  'মিস্ট (MIST)': ['2027-01-15', '2027-01-22', '2027-02-05', '2027-02-06']}.items():
            events = [e['s'] for e in json.loads((ROOT / 'data/calendar.json').read_text())['events'] if e['u'] == university]
            self.assertEqual(sorted(events), dates)
        self.assertFalse(any(e['s']=='2027-01-24' and e.get('e')=='2027-01-26' and e['u'].startswith('যশোর') for e in json.loads((ROOT / 'data/calendar.json').read_text())['events']))
        self.assertIn('গুচ্ছ (GST) — ২০ বিশ্ববিদ্যালয়', CALENDAR)

    def test_unverified_eligibility_is_not_automatically_judged(self):
        entries = [{'short':u['short'], 'name_bn':u.get('checker_name_bn',u['name_bn']), 'rules':u.get('elig_rules',[])} for u in json.loads((ROOT / 'data/universities.json').read_text())['universities']]
        for short in ['MIST', 'BUET']:
            self.assertEqual(UNIS[short]['elig_rules'], [])
            self.assertEqual(next(e for e in entries if e['short'] == short)['rules'], [])

    def test_all_cards_remain_and_new_ones_are_mirrored(self):
        self.assertEqual(len(UNIS), 22)
        self.assertEqual(len(re.findall(r'<article\b[^>]*data-file=', INDEX)), 22)
        order = re.findall(r'<article\b[^>]*data-file="([^"]+)"', INDEX)
        self.assertEqual(order, [u['short'] for u in DATA['universities']])
        checker = [{'short':u['short'], 'name_bn':u.get('checker_name_bn',u['name_bn']), 'rules':u.get('elig_rules',[])} for u in json.loads((ROOT / 'data/universities.json').read_text())['universities']]
        self.assertEqual([e['short'] for e in checker], order)
        switch = {u['short']:u.get('checker_switch_note') for u in DATA['universities'] if u.get('checker_switch_note')}
        for short in ['AGRI', 'HSTU', 'AAUB']:
            with self.subTest(short=short):
                self.assertEqual(UNIS[short]['elig_rules'], [])
                self.assertEqual(next(e for e in checker if e['short'] == short)['rules'], [])
                self.assertIn(short, switch)
                self.assertIn('class="refpill"', card(short))
                self.assertNotIn('hero-date', card(short))
                self.assertIn(UNIS[short]['source_url']['url'], (ROOT / UNIS[short]['details_page']).read_text())

    def test_new_universities_dates_reach_the_calendar(self):
        for date, university in [('2027-01-02', 'কৃষি গুচ্ছ (৯ বিশ্ববিদ্যালয়)'),
                                 ('2027-01-24', 'হাবিপ্রবি (HSTU)'),
                                 ('2027-01-30', 'অ্যাভিয়েশন অ্যান্ড অ্যারোস্পেস বিশ্ববিদ্যালয় (AAUB)')]:
            with self.subTest(university=university):
                self.assertTrue(any(e['s']==date and e['u']==university for e in json.loads((ROOT / 'data/calendar.json').read_text())['events']))

    def test_current_schedule_corrections(self):
        self.assertEqual(DATA['updated'], '১১ নভেম্বর ২০২৬')
        self.assertEqual(UNIS['AAUB']['source_url']['kind'], 'official')
        self.assertIsNone(UNIS['KhU']['apply_start'])
        self.assertIn('আবেদনের সময়সূচি পরে জানানো হবে', card('KhU'))
        self.assertIn('অংশগ্রহণ ইউজিসির অনুমোদনসাপেক্ষ', (ROOT / 'gst-admission.html').read_text())
        self.assertIn('১,২০০', (ROOT / 'du-admission.html').read_text())
        for page in [INDEX, CALENDAR, ELIGIBILITY]:
            self.assertNotIn('সাইটের আপডেট:', page)
            self.assertIn('সাম্প্রতিক সংশোধন:', page)
            self.assertIn('data-bd-today', page)


if __name__ == '__main__':
    unittest.main()
