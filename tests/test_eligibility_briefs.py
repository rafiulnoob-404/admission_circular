import html
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / 'index.html').read_text()
DATA = json.loads(re.search(r'<script type="application/json" id="card-data">(.*?)</script>', INDEX, re.S).group(1))
ELIG = (ROOT / 'eligibility.html').read_text()
CHECKER = json.loads(re.search(r'var UNIS = (\[.*?\]);', ELIG, re.S).group(1))

class EligibilityBriefs(unittest.TestCase):
    def test_brief_first_and_mirrored_on_every_card(self):
        self.assertEqual(len(DATA['universities']), 22)
        for uni in DATA['universities']:
            with self.subTest(uni=uni['short']):
                card = re.search(r'<article\b[^>]*data-file="' + uni['short'] + r'"[^>]*>.*?</article>', INDEX, re.S).group()
                briefs = re.findall(r'<div class="elig-brief"><b>যোগ্যতা সংক্ষেপে</b><p>(.*?)</p></div>', card)
                self.assertEqual(len(briefs), 1)
                self.assertEqual(html.unescape(briefs[0]), uni['elig_summary'])
                self.assertLess(len(briefs[0]), 220)
                for section in ('class="dstrip"', 'class="hero-date', 'class="unit-table', 'class="lists', 'class="grid"'):
                    if section in card:
                        self.assertLess(card.index('class="elig-brief"'), card.index(section))

    def test_medical_current_rules_are_not_guessed(self):
        med = next(u for u in DATA['universities'] if u['short'] == 'MED')
        check = next(u for u in CHECKER if u['short'] == 'MED')
        card = re.search(r'<article\b[^>]*data-file="MED"[^>]*>.*?</article>', INDEX, re.S).group()
        page = (ROOT / 'medical-admission.html').read_text()
        self.assertEqual(med['elig_rules'], [])
        self.assertEqual(check['rules'], [])
        self.assertIsNone(med['exam_time'])
        self.assertIsNone(med['subjects'])
        self.assertEqual(card.count('href="medical-admission.html"'), 1)
        self.assertIn('বিজ্ঞপ্তি অপেক্ষমাণ', page)
        self.assertIn('২০২৫–২৬ শিক্ষাবর্ষের তথ্য', page)
        self.assertNotIn('পদার্থবিজ্ঞান ২০', card)
        self.assertNotIn('পুনঃপরীক্ষার শিক্ষার্থীরাও আবেদন করতে পারবেন', card)

if __name__ == '__main__':
    unittest.main()
