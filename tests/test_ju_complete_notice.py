"""Checks for the supplied JU 2026–27 circular and its detail page."""
import hashlib
import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DETAIL = (ROOT / 'ju-admission.html').read_text(encoding='utf-8')
INDEX = (ROOT / 'index.html').read_text(encoding='utf-8')
PDF = 'notices/2026-27/ju-admission-circular-2026-27.pdf'


class Tables(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables = []
        self.table = self.row = self.cell = None

    def handle_starttag(self, tag, attrs):
        if tag == 'table':
            self.table = []
        elif tag == 'tr' and self.table is not None:
            self.row = []
        elif tag in ('td', 'th') and self.row is not None:
            self.cell = []

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag):
        if tag in ('td', 'th') and self.cell is not None:
            self.row.append(''.join(self.cell).strip())
            self.cell = None
        elif tag == 'tr' and self.row is not None:
            self.table.append(self.row)
            self.row = None
        elif tag == 'table' and self.table is not None:
            self.tables.append(self.table)
            self.table = None


def section(title):
    return DETAIL.split('<h2>' + title + '</h2>', 1)[1].split('</section>', 1)[0]


def rows(title):
    parser = Tables()
    parser.feed(section(title))
    return parser.tables[0][1:]


def number(value):
    return int(value.translate(str.maketrans('০১২৩৪৫৬৭৮৯', '0123456789')))


class JuCompleteNotice(unittest.TestCase):
    def test_pdf_is_supplied_copy_with_official_sources(self):
        self.assertIn('href="' + PDF + '"', section('সম্পূর্ণ ভর্তি বিজ্ঞপ্তি'))
        self.assertIn('ব্যবহারকারীর দেওয়া', DETAIL)
        self.assertIn('https://www.juniv.edu/discussion/18670', DETAIL)
        self.assertIn('https://admission.juniv.edu/', DETAIL)
        self.assertEqual(hashlib.sha256((ROOT / PDF).read_bytes()).hexdigest(),
                         '943e841667ab7c7bafe55580f074ed51a5a019c96359d459f836b6578b235f11')

    def test_dates_fees_and_exam_rules(self):
        for fact in ('২২ নভেম্বর ২০২৬', '১৫ ডিসেম্বর', '২৫ ডিসেম্বর', '১০–২১ জানুয়ারি ২০২৭',
                     '৮০০', '৭০০', '৬০০', '১.২%'):
            self.assertIn(fact, section('সূচি ও ফি'))
        for fact in ('৮০টি MCQ', '৯০ নম্বর', '০.২০', '৫৫ মিনিট', '৫ মিনিট', '৪০ নম্বর', '১.১২৫'):
            self.assertIn(fact, section('পরীক্ষা ও আসন'))
        card = re.search(r'<article\b[^>]*data-file="JU"[^>]*>.*?</article>', INDEX, re.S).group()
        self.assertIn('২৫ ডিসেম্বর ২০২৬', card)
        self.assertIn('ju-admission.html', card)
        cal = json.loads((ROOT / 'data/calendar.json').read_text())
        app = next(a for a in cal['applications'] if a['u'] == 'জাহাঙ্গীরনগর বিশ্ববিদ্যালয়')
        self.assertEqual((app['s'], app['e']), ('2026-11-22', '2026-12-15'))
        event = next(a for a in cal['events'] if a['u'] == 'জাহাঙ্গীরনগর বিশ্ববিদ্যালয়')
        self.assertEqual((event['s'], event['e']), ('2027-01-10', '2027-01-21'))
        self.assertIn('সম্ভাব্য', event['n'])

    def test_question_distribution(self):
        expected = {
            'A': 'বাংলা ৩, ইংরেজি ৩, গণিত ২২, পদার্থ ২২, রসায়ন ২২, আইসিটি ৮',
            'B': 'বাংলা ২০, ইংরেজি ২০, সাধারণ গণিত ২০, সাধারণ জ্ঞান ১৫, যৌক্তিক বিশ্লেষণ ৫',
            'C': 'বাংলা ২০, ইংরেজি ২০, সাধারণ জ্ঞান ও বিভাগ-সংশ্লিষ্ট বিষয় ৪০',
            'C1': 'বাংলা ১০, ইংরেজি ১০, সাধারণ জ্ঞান ২০, বিভাগ-সংশ্লিষ্ট বিষয় ৪০',
            'D': 'বাংলা ৪, ইংরেজি ৪, বুদ্ধিমত্তা ৪, রসায়ন ২৪, জীববিজ্ঞান ৪৪ (উদ্ভিদ ২২, প্রাণী ২২)',
            'E — ব্যবসায় শিক্ষা': 'বাংলা ২০, ইংরেজি ২০, হিসাববিজ্ঞান ২০, ব্যবস্থাপনা ২০',
            'E — বিজ্ঞান/মানবিক/সমমান': 'বাংলা ২০, ইংরেজি ২০, গণিত ও বিশ্লেষণী দক্ষতা ২০, ব্যবসা-সম্পর্কিত সাধারণ জ্ঞান ২০',
            'IBA-JU': 'বাংলা ৫, ইংরেজি ৩০, Mathematical aptitude and IQ ৩০, সাম্প্রতিক ও বিশ্লেষণমূলক বিষয় ১৫',
        }
        self.assertEqual(dict(rows('ইউনিটভিত্তিক প্রশ্ন বণ্টন')), expected)

    def test_seat_breakdown_totals(self):
        seat_rows = rows('বিভাগ ও ছাত্র/ছাত্রীভিত্তিক আসন')
        self.assertEqual(len(seat_rows), 37)
        sums = {}
        for unit, department, male, female, total in seat_rows:
            male, female, total = map(number, (male, female, total))
            self.assertEqual(male + female, total, department)
            sums[unit] = sums.get(unit, 0) + total
        self.assertEqual(sums, {'A': 424, 'B': 396, 'C': 402, 'C1': 64, 'D': 316, 'E': 176, 'IBA-JU': 70})
        self.assertEqual(sum(sums.values()), 1848)

    def test_department_and_english_medium_conditions(self):
        subjects = section('বিভাগভিত্তিক যোগ্যতা')
        for fact in ('গণিতে B', 'পদার্থে পৃথক A−', 'রসায়ন ও জীববিজ্ঞানে পৃথক ৫০%',
                     'MCQ ও ব্যবহারিকে পৃথক পাস', 'ব্যবসায় সংগঠন ও ব্যবস্থাপনা', 'checker বিভাগভিত্তিক'):
            self.assertIn(fact, subjects)
        levels = section('O-Level ও A-Level')
        for fact in ('২০২১', '২০২৫ বা ২০২৬', 'চারটিতে অন্তত B', 'তিনটিতে অন্তত C',
                     'পদার্থ, রসায়ন ও গণিতে পৃথক B', 'O-Level অথবা A-Level', 'ট্রান্সক্রিপ্ট'):
            self.assertIn(fact, levels)
        rules = next(u for u in json.loads((ROOT / 'data/universities.json').read_text())['universities'] if u['short'] == 'JU')['elig_rules']
        self.assertTrue(all(rule['partial'] for rule in rules))

    def test_application_and_merit(self):
        text = section('আবেদনের ধাপ ও পরীক্ষার নিয়ম')
        for fact in ('৩০০×৩০০', '১০০ KB', '৩০০×৮০', '৬০ KB', '০.৭৫', '১.২৫',
                     'সর্বোচ্চ ১০ গুণ', '01348307028', 'admissionhelp@juniv.edu'):
            self.assertIn(fact, text)


if __name__ == '__main__':
    unittest.main()
