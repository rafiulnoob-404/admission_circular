"""User-supplied November 2026 JnU and medical notice regressions."""
import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JNU = (ROOT / 'jnu-admission.html').read_text()
MED = (ROOT / 'medical-admission.html').read_text()
INDEX = (ROOT / 'index.html').read_text()
UNIS = {u['short']: u for u in json.loads((ROOT / 'data/universities.json').read_text())['universities']}
CAL = json.loads((ROOT / 'data/calendar.json').read_text())

class TableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables = {}
        self.label = self.row = self.cell = None
        self.current = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'div' and attrs.get('aria-label'):
            self.label = attrs['aria-label']
        elif tag == 'table':
            self.current = []
        elif tag == 'tr':
            self.row = []
        elif tag in ('th', 'td') and self.row is not None:
            self.cell = ''
    def handle_data(self, data):
        if self.cell is not None:
            self.cell += data
    def handle_endtag(self, tag):
        if tag in ('th', 'td') and self.cell is not None:
            self.row.append(self.cell.strip())
            self.cell = None
        elif tag == 'tr' and self.row is not None:
            self.current.append(self.row)
            self.row = None
        elif tag == 'table':
            self.tables[self.label] = self.current[1:]


def number(s):
    return int(s.translate(str.maketrans('০১২৩৪৫৬৭৮৯', '0123456789')))

class SuppliedCirculars(unittest.TestCase):
    def test_original_pages_linked_with_provenance(self):
        for page, prefix, start, stop in [(JNU, 'jnu-guideline-page', 2, 12), (MED, 'medical-notice-page', 1, 8)]:
            for i in range(start, stop + 1):
                name = f'notices/2026-27/{prefix}-{i}.jpg'
                self.assertIn('href="' + name + '"', page)
                self.assertGreater((ROOT / name).stat().st_size, 1000)
            self.assertIn('ব্যবহারকারীর দেওয়া', page)
        self.assertIn('প্রথম পৃষ্ঠা সরবরাহ করা হয়নি', JNU)
        self.assertIn('তৃতীয় পক্ষের উপস্থাপনা', MED)

    def test_jnu_eligibility_and_exam(self):
        parser = TableParser(); parser.feed(JNU)
        rules = {row[0]: row[2] for row in parser.tables['জবি যোগ্যতা']}
        self.assertEqual(rules, {'A': '৭.০০ / ৩.০০', 'B': '৬.০০ / ৩.০০', 'C': '৬.৫০ / ৩.০০', 'D': '৬.০০ / ৩.০০', 'E': '৫.৫০ / ২.৭৫'})
        self.assertIn('B ও D ৬/৩', UNIS['JnU']['elig_summary'])
        for fact in ('২০২৩ বা ২০২৪', '২০২৬ সালে উত্তীর্ণ', 'সর্বোচ্চ দুই বিষয়ে', 'চারটিতে B', 'তিনটিতে C',
                     '১,২১২', '১,৫১৫', 'MCQ ২৭', 'ব্যবহারিক ৪৫', '০.৭৫', '০.২৫', '৫০ নম্বরের ব্যবহারিক'):
            self.assertIn(fact, JNU)
        self.assertEqual(UNIS['JnU']['elig_rules'], [])
        self.assertNotIn('বি/ডি ৬ ও ২.৭৫', INDEX)

    def test_jnu_seats_and_group_breakdown(self):
        parser = TableParser(); parser.feed(JNU)
        tables = [('A বিভাগের শর্ত', 888), ('B বিভাগের শর্ত', 825), ('C বিভাগের আসন', 546),
                  ('D বিভাগের শর্ত', 635), ('E বিভাগের আসন', 63)]
        for label, total in tables:
            with self.subTest(label=label):
                rows = parser.tables[label]
                self.assertEqual(sum(number(row[1]) for row in rows), total)
                if label.startswith(('B ', 'C ', 'D ')):
                    for row in rows:
                        if 'উন্মুক্ত' not in row:
                            self.assertEqual(sum(number(x) if x != '—' else 0 for x in row[2:5]), number(row[1]))
        self.assertEqual(sum(total for _, total in tables), 2957)

    def test_medical_dates_and_application_sms(self):
        u = UNIS['MED']
        self.assertEqual((u['application_schedule']['start'], u['application_schedule']['end']),
                         ('2026-11-25T18:30:00+06:00', '2026-12-03T23:59:59+06:00'))
        app = next(x for x in CAL['applications'] if x['u'] == 'মেডিকেল ও ডেন্টাল (MBBS/BDS)')
        self.assertEqual((app['s'], app['e']), ('2026-11-25', '2026-12-03'))
        self.assertIn('৪ ডিসেম্বর', app['end'])
        event = next(x for x in CAL['events'] if x['u'] == app['u'])
        self.assertEqual(event['s'], '2026-12-18')
        for text in ('৩ ডিসেম্বর ২০২৬ রাত ১১:৫৯', '৪ ডিসেম্বর রাত ১১:৫৯', '১৪–১৭ ডিসেম্বর',
                     'কেন্দ্রপ্রধানের জন্য', 'MBBSBDS USERID', 'MBBSBDS YES PIN 11,12,13,14', '16222'):
            self.assertIn(text, MED)
        self.assertNotIn('১৫–১৮ নভেম্বর', MED)
        self.assertEqual(u['elig_rules'], [])

    def test_medical_eligibility_distribution_and_seats(self):
        for text in ('২০২৩ সালের আগে পাস নয়', '২০২৫ বা ২০২৬', 'মিলিয়ে GPA অন্তত ৮.৫০',
                     'জীববিজ্ঞানে GP অন্তত ৩.৫০', 'মোট GPA অন্তত ৮.০০', 'জীববিজ্ঞানে GP অন্তত ৩.০০',
                     '০.২৫', 'পাস ৪০', 'SSC GPA × ৮', 'HSC GPA × ১২', '৫,২৭০', '৫৪৫'):
            self.assertIn(text, MED)
        parser = TableParser(); parser.feed(MED)
        dist = parser.tables['মেডিকেল প্রশ্ন বণ্টন']
        self.assertEqual([number(row[1]) for row in dist], [30, 25, 15, 15, 15])
        self.assertEqual(sum(number(row[1]) for row in dist), 100)

if __name__ == '__main__': unittest.main()
