"""Science-unit information must stay consistent across card and checker."""
import json
import re
import subprocess
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / 'index.html').read_text(encoding='utf-8')
ELIG = (ROOT / 'eligibility.html').read_text(encoding='utf-8')
DETAILS = (ROOT / 'du-science.html').read_text(encoding='utf-8')
DATA = json.loads(re.search(r'<script type="application/json" id="card-data">(.*?)</script>', INDEX, re.S).group(1))
DU = next(u for u in DATA['universities'] if u['short'] == 'DU')
CHECKER = json.loads(re.search(r'var UNIS = (\[.*?\]);', ELIG).group(1))
DU_CHECKER = next(u for u in CHECKER if u['short'] == 'DU')
CARD = re.search(r'<article\b[^>]*data-file="DU"[^>]*>.*?</article>', INDEX, re.S).group()


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.hrefs.append(dict(attrs).get('href'))


class DhakaScience(unittest.TestCase):
    def test_links_and_attribution(self):
        for page in (CARD, ELIG):
            parser = Links()
            parser.feed(page)
            self.assertIn('du-science.html', parser.hrefs)
        self.assertIn('পৃষ্ঠা ৪–৯', DETAILS)
        self.assertIn(DU['science_unit_details']['notice_url'], DETAILS)
        self.assertIn('বিশ্ববিদ্যালয়ের নিজস্ব সাইট নয়', DETAILS)

    def test_schedule_and_exam_rules(self):
        for text in ('২ ডিসেম্বর ২০২৬', '১২ ডিসেম্বর ২০২৬', '২৪/৬০', '১২/৪০', '৪০/১০০', '০.২৫', '৫ গুণ'):
            with self.subTest(text=text):
                self.assertIn(text, DETAILS)
        for text in ('২ ডিসেম্বর ২০২৬', '২৪/৬০', '১২/৪০', '৪০/১০০', '০.২৫', '৫ গুণ'):
            self.assertIn(text, CARD)
        self.assertEqual(DU['science_unit_details']['details_page'], 'du-science.html')
        self.assertIn('২০২৫–২৬ শিক্ষাবর্ষে আবেদনকারীরা', DU['science_unit_details']['eligibility_warning'])

    def test_science_rules_match_checker_and_cover_groups(self):
        card_rules = [r for r in DU['elig_rules'] if r['unit'].startswith('বিজ্ঞান ইউনিট')]
        check_rules = [r for r in DU_CHECKER['rules'] if r['unit'].startswith('বিজ্ঞান ইউনিট')]
        self.assertEqual(card_rules, check_rules)
        self.assertEqual(card_rules[0]['groups'], ['বিজ্ঞান', 'কৃষিশিক্ষা'])
        self.assertEqual((card_rules[0]['each_min'], card_rules[0]['combined_min']), (3.5, 8.0))
        self.assertEqual(card_rules[1]['groups'], ['মানবিক', 'ব্যবসায়'])
        self.assertEqual((card_rules[1]['each_min'], card_rules[1]['combined_min']), (3.0, 7.5))
        self.assertTrue(all('বিভাগভিত্তিক শর্ত' in r['extra'] for r in card_rules))
        self.assertIn('✔ প্রাথমিক যোগ্য', ELIG)

    def test_checker_thresholds_using_real_check_function(self):
        check = re.search(r'function check\(rule,d\)\{.*?\n\}', ELIG, re.S).group()
        rules = [r for r in DU_CHECKER['rules'] if r['unit'].startswith('বিজ্ঞান ইউনিট')]
        js = '''function bn(v){return String(v)}; function fmt(v){return v.toFixed(2)};\n''' + check + '''
const rules = ''' + json.dumps(rules, ensure_ascii=False) + ''';
function data(group, ssc, hsc){return {ssc:{year:2024,gpa:ssc},hsc:{year:2026,group:group,gpa:hsc},subj:{}}}
const cases = [[0,'বিজ্ঞান',4,4,'pass'],[0,'বিজ্ঞান',3.49,4.51,'fail'],
[1,'মানবিক',3.5,4,'pass'],[1,'ব্যবসায়',3,4.49,'fail'],[1,'বিজ্ঞান',4,4,'fail']];
for (const [r,g,s,h,expected] of cases) {let result=check(rules[r],data(g,s,h));
if(result.state!==expected || !result.extra.includes('২০২৫–২৬')) process.exit(1);}
'''
        subprocess.run(['node', '-e', js], check=True, capture_output=True, text=True)

    def test_department_table_is_not_omitted(self):
        self.assertEqual(DETAILS.count('<tr><td>'), 34)
        for text in ('কম্পিউটার সায়েন্স এন্ড ইঞ্জিনিয়ারিং', 'পদার্থবিজ্ঞান ১৩ এবং গণিত ১৩',
                     'ফার্মেসী', 'মুক্তিযোদ্ধার সন্তান ৫%', 'প্রতিবন্ধী ও হিজড়া ১%'):
            self.assertIn(text, DETAILS)


if __name__ == '__main__':
    unittest.main()
