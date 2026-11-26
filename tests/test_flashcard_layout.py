"""Contract for readable flash cards and their detail pages."""
import html
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / 'index.html').read_text()
DATA = json.loads((ROOT / 'data/universities.json').read_text())['universities']

class FlashCards(unittest.TestCase):
    def test_all_cards_have_short_sections_and_detail_link(self):
        for u in DATA:
            with self.subTest(university=u['short']):
                card = re.search(r'<article\b[^>]*data-file="' + re.escape(u['short']) + r'"[^>]*>.*?</article>', INDEX, re.S).group()
                for field in ['যোগ্যতা সংক্ষেপে', 'ফরম পূরণ / আবেদন', 'ভর্তি পরীক্ষা', 'ইউনিট / প্রোগ্রাম', 'বিস্তারিত বিজ্ঞপ্তি ও তথ্য']:
                    self.assertIn(field, card)
                self.assertLess(card.index('যোগ্যতা সংক্ষেপে'), card.index('ফরম পূরণ / আবেদন'))
                self.assertIn(u['exam_date'], html.unescape(card))
                self.assertIn('href="'+u['details_page']+'" target="_blank"', card)
                self.assertIn('class="dlbtn"', card)
                detail = html.unescape((ROOT / u['details_page']).read_text())
                self.assertIn(u['references']['official_url'], detail)
                self.assertIn('অফিসিয়াল বিজ্ঞপ্তি ও তথ্য', detail)
                self.assertIn('card-history', detail)
                if u['references'].get('news_url'):
                    self.assertIn(u['references']['news_url'], detail)

    def test_caveats_and_du_units_are_accessible(self):
        mist = re.search(r'<article\b[^>]*data-file="MIST"[^>]*>.*?</article>', INDEX, re.S).group()
        self.assertIn('সূচি নিয়ে মতভেদ', mist)
        self.assertIn('১৫/২২ জানুয়ারি', mist)
        agri = re.search(r'<article\b[^>]*data-file="AGRI"[^>]*>.*?</article>', INDEX, re.S).group()
        self.assertIn('সূত্রভেদে অমিল', agri)
        du = (ROOT / 'du-admission.html').read_text()
        for unit in ['du-science.html','du-arts.html','du-business.html','du-fine-arts.html','du-iba.html']:
            self.assertIn(unit, du)

    def test_14px_shared_styles_and_mobile_calendar(self):
        css = (ROOT / 'readable.css').read_text()
        self.assertGreaterEqual(css.count('font-size: 14px !important'), 2)
        self.assertIn('@media print', css)
        self.assertIn('.table-scroll', css)
        for page in list(ROOT.glob('*.html')):
            self.assertIn('href="readable.css"', page.read_text(), str(page))
        self.assertIn('class="table-scroll"', (ROOT / 'calendar.html').read_text())

if __name__ == '__main__':
    unittest.main()
