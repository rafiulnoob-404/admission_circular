"""Keep official corrections, consistent notice placement, and partial data honest."""
import json
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / 'index.html').read_text(encoding='utf-8')
ELIG = (ROOT / 'eligibility.html').read_text(encoding='utf-8')
CAL = (ROOT / 'calendar.html').read_text(encoding='utf-8')
DATA = json.loads(re.search(r'<script type="application/json" id="card-data">(.*?)</script>', INDEX, re.S).group(1))
UNIS = {u['short']: u for u in DATA['universities']}
CHECKER = {u['short']: u for u in json.loads(re.search(r'var UNIS = (\[.*?\]);', ELIG).group(1))}


class ExpandedNotices(unittest.TestCase):
    def test_all_cards_have_same_notice_position(self):
        cards = re.findall(r'<article\b[^>]*data-file="([^"]+)"[^>]*>.*?</article>', INDEX, re.S)
        self.assertEqual(set(cards), set(UNIS))
        for short in cards:
            card = re.search(r'<article\b[^>]*data-file="' + short + r'"[^>]*>.*?</article>', INDEX, re.S).group()
            self.assertEqual(card.count('class="notice-links"'), 1, short)
            self.assertRegex(card, r'(?s)<div class="notice-links">.*?</div></div>\s*<div class="foot">')
            self.assertIn('class="dlbtn"', card)

    def test_du_units_links_and_thresholds(self):
        card = re.search(r'<article\b[^>]*data-file="DU"[^>]*>.*?</article>', INDEX, re.S).group()
        for file in ['du-science.html', 'du-arts.html', 'du-business.html', 'du-fine-arts.html', 'du-iba.html']:
            self.assertIn('href="' + file + '"', card)
            self.assertTrue((ROOT / file).exists())
        self.assertEqual(UNIS['DU']['elig_rules'], CHECKER['DU']['rules'])
        rules = [r for r in CHECKER['DU']['rules'] if r['unit'] == 'ব্যবসায় শিক্ষা ইউনিট']
        self.assertEqual([(r['combined_min'], r['each_min']) for r in rules], [(8.0, 3.5), (7.5, 3.0)])
        check = re.search(r'function check\(rule,d\)\{.*?\n\}', ELIG, re.S).group()
        js = 'function bn(v){return String(v)}; function fmt(v){return v.toFixed(2)};\n' + check + '\nconst rules=' + json.dumps(rules, ensure_ascii=False) + ''';
function d(g,s,h){return {ssc:{year:2024,gpa:s},hsc:{year:2026,group:g,gpa:h},subj:{}}}
if(check(rules[0],d('বিজ্ঞান',3.5,4)).state!=='fail')process.exit(1);
if(check(rules[0],d('বিজ্ঞান',4,4)).state!=='pass')process.exit(2);
if(check(rules[1],d('ব্যবসায়',3.5,4)).state!=='pass')process.exit(3);
'''
        subprocess.run(['node', '-e', js], check=True, capture_output=True, text=True)

    def test_kuet_official_and_unverified_engineering(self):
        kuet = UNIS['KUET']
        self.assertEqual(kuet['source_url']['kind'], 'official')
        self.assertIn('Prospectus-Ban.pdf', kuet['source_url']['url'])
        self.assertEqual(kuet['elig_rules'], CHECKER['KUET']['rules'])
        self.assertEqual(kuet['elig_rules'][0]['ssc_years'], [2023, 2024])
        for short, date in [('RUET', '2027-01-14'), ('CUET', '2027-01-23'), ('BUTEX', '2027-01-29')]:
            self.assertEqual(UNIS[short]['elig_rules'], [])
            self.assertEqual(CHECKER[short]['rules'], [])
            self.assertIn(date, CAL)
            self.assertIn('পূর্ণাঙ্গ', (ROOT / UNIS[short]['details_page']).read_text())
        self.assertEqual(CHECKER['BUET']['rules'], [])
        for short in ['RUET', 'CUET']:
            self.assertIn('সম্ভাব্য', UNIS[short]['exam_date'])


if __name__ == '__main__':
    unittest.main()
