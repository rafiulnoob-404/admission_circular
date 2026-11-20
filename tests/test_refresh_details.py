"""Coverage for sources, detail links, and partial eligibility checks."""
import json
import re
import subprocess
import unittest
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / 'index.html').read_text()
ELIG = (ROOT / 'eligibility.html').read_text()
DATA = json.loads(re.search(r'<script type="application/json" id="card-data">(.*?)</script>', INDEX, re.S).group(1))
UNIS = {u['short']: u for u in DATA['universities']}
CHECKER = {u['short']: u for u in json.loads(re.search(r'var UNIS = (\[.*?\]);', ELIG).group(1))}

class Refresh(unittest.TestCase):
    def test_all_card_detail_links_resolve(self):
        for u in DATA['universities']:
            card = re.search(r'<article\b[^>]*data-file="' + u['short'] + r'"[^>]*>.*?</article>', INDEX, re.S).group()
            links = re.search(r'<div class="notice-links">(.*?)</div></div>', card, re.S).group(1)
            paths = re.findall(r'href="([^"]+\.html)"', links)
            self.assertTrue(paths, u['short'])
            for path in paths:
                self.assertTrue((ROOT / path).is_file(), path)
                page = (ROOT / path).read_text()
                self.assertIn('href="notice.css"', page)
                self.assertIn('href="index.html"', page)
            if u['short'] != 'DU':
                self.assertIn(u['details_page'], paths)

    def test_ru_official_rules_and_actual_checker(self):
        ru = UNIS['RU']['elig_rules']
        self.assertEqual(ru, CHECKER['RU']['rules'])
        self.assertEqual(UNIS['RU']['source_url']['url'], 'https://admission.ru.ac.bd/')
        check = re.search(r'function check\(rule,d\)\{.*?\n\}', ELIG, re.S).group()
        script = 'function bn(v){return String(v)}; function fmt(v){return v.toFixed(2)};\n' + check + '\nconst r=' + json.dumps(ru, ensure_ascii=False) + ''';
function d(group,yr,s,h){return {ssc:{year:2024,gpa:s},hsc:{year:yr,group:group,gpa:h},subj:{}}}
for(const [i,g,y,s,h,expected] of [[0,'বিজ্ঞান',2025,3.5,4,'pass'],[0,'বিজ্ঞান',2024,4,4,'fail'],[0,'বিজ্ঞান',2026,3.49,4.1,'fail'],[0,'বিজ্ঞান',2026,3.5,3.99,'fail'],[1,'মানবিক',2026,3,3.5,'pass'],[1,'ব্যবসায়',2026,3,3.49,'fail'],[1,'বিজ্ঞান',2026,4,4,'fail']])
 if(check(r[i],d(g,y,s,h)).state!==expected)process.exit(1);
'''
        subprocess.run(['node', '-e', script], check=True, capture_output=True)

    def test_unconfirmed_ju_and_aaub_rules_are_not_judged(self):
        for name in ['JU', 'AAUB']:
            self.assertEqual(UNIS[name]['elig_rules'], [])
            self.assertEqual(CHECKER[name]['rules'], [])
        self.assertIn('PDF-এ শিক্ষাবর্ষ স্পষ্ট নেই', (ROOT / 'aaub-admission.html').read_text())
        self.assertIn('২০২৬–২৭ শিক্ষাবর্ষের ইউনিটভিত্তিক GPA', INDEX)

    def test_kuet_source_and_du_provided_notice(self):
        kuet = (ROOT / 'kuet-admission.html').read_text()
        self.assertIn('https://admission.kuet.ac.bd/notices/2.Prospectus-Ban.pdf', kuet)
        self.assertNotIn('/uploads/notices/', kuet)
        science = (ROOT / 'du-science.html').read_text()
        self.assertIn('মুক্তিযোদ্ধার সন্তান ৫%', science)
        self.assertIn('পদার্থবিজ্ঞান ১৩ এবং গণিত ১৩', science)
        for p in ('du-arts.html', 'du-business.html', 'du-fine-arts.html', 'du-iba.html'):
            self.assertIn('প্রবেশপত্র:', (ROOT / p).read_text())

if __name__ == '__main__':
    unittest.main()
