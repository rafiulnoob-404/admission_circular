"""Detail pages, discovery, sources and disputed schedules."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / 'index.html').read_text(encoding='utf-8')
CALENDAR = (ROOT / 'calendar.html').read_text(encoding='utf-8')
ELIG = (ROOT / 'eligibility.html').read_text(encoding='utf-8')
DATA = json.loads(re.search(r'<script type="application/json" id="card-data">(.*?)</script>', INDEX, re.S).group(1))


class Notices(unittest.TestCase):
    def test_discovery_and_shared_layout(self):
        for short, path in [('KUET', 'kuet-admission.html'), ('JnU', 'jnu-admission.html')]:
            with self.subTest(short=short):
                card = re.search(r'<article\b[^>]*data-file="' + short + r'"[^>]*>.*?</article>', INDEX, re.S).group()
                self.assertIn('href="' + path + '"', card)
                self.assertIn('href="' + path + '"', ELIG)
                self.assertEqual(next(u for u in DATA['universities'] if u['short'] == short)['details_page'], path)
        for path in ['du-science.html', 'kuet-admission.html', 'jnu-admission.html']:
            page = (ROOT / path).read_text(encoding='utf-8')
            self.assertIn('href="notice.css"', page)
            for href in ['index.html', 'eligibility.html', 'calendar.html']:
                self.assertIn('href="' + href + '"', page)

    def test_kuet_disagreement_and_seat_table(self):
        page = (ROOT / 'kuet-admission.html').read_text(encoding='utf-8')
        for phrase in ['৮ জানুয়ারি', '৯ জানুয়ারি', 'বিকাল ৫টা', 'রাত ৯টা', '২১ জানুয়ারি', '২২ জানুয়ারি',
                       'https://thedailycampus.com/admission-updates/281355', 'https://admission.kuet.ac.bd/',
                       'https://students.bd/en/notice/kuet-admission-circular-2026-2027']:
            self.assertIn(phrase, page)
        table = page.split('aria-label="বিভাগ ও আসন সারণি"')[1].split('</table>')[0]
        rows = re.findall(r'<tr><td>(.*?)</tr>', table)
        self.assertEqual(len(rows), 17)
        nums = [int(re.findall(r'<td>(.*?)</td>', row)[-1].translate(str.maketrans('০১২৩৪৫৬৭৮৯', '0123456789'))) for row in rows]
        self.assertEqual(sum(nums), 1100)
        self.assertIn('সংরক্ষিত', page)
        self.assertIn('সংবাদে ৯ জানুয়ারি', CALENDAR)
        self.assertNotIn('"কুয়েট (KUET)"', re.search(r'var VER=\[(.*?)\]', CALENDAR).group(1))

    def test_jnu_notice_versus_older_gpa_report(self):
        page = (ROOT / 'jnu-admission.html').read_text(encoding='utf-8')
        for phrase in ['২৫ নভেম্বর ২০২৬', '১০ ডিসেম্বর ২০২৬', '১,২০০ টাকা', '১,৫০০ টাকা',
                       'সর্বোচ্চ দুই বিষয়ে', 'আগে প্রকাশিত', 'পূর্ণ শর্ত', '১১:৩০',
                       'https://admission.jnu.ac.bd/']:
            self.assertIn(phrase, page)
        for date in ['১ জানুয়ারি', '৮ জানুয়ারি', '১৫ জানুয়ারি', '২২ জানুয়ারি', '২৩ জানুয়ারি']:
            self.assertIn(date, page)
        self.assertIn('ইউনিট E · সকাল ১০:০০–১১:৩০', CALENDAR)


if __name__ == '__main__':
    unittest.main()
