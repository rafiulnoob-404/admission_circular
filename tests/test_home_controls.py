"""Home controls and source/print regressions, without network access."""
import json
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / 'index.html').read_text()
DATA = json.loads(re.search(r'<script type="application/json" id="card-data">(.*?)</script>', INDEX, re.S).group(1))
UNIS = {u['short']: u for u in DATA['universities']}

class HomeControls(unittest.TestCase):
    def test_sources_and_update_on_every_card(self):
        self.assertEqual(len(UNIS), 22)
        for short, uni in UNIS.items():
            with self.subTest(short=short):
                card = re.search(r'<article\b[^>]*data-file="' + short + r'"[^>]*>.*?</article>', INDEX, re.S).group()
                ref = uni['references']
                self.assertIn('কার্ড আপডেট: ১১ নভেম্বর ২০২৬', card)
                self.assertIn(ref['official_url'], card)
                if ref['news_url']:
                    self.assertIn(ref['news_url'], card)
                    self.assertLess(card.index(ref['official_url'], card.index('class="source-meta"')), card.index(ref['news_url'], card.index('class="source-meta"')))
        self.assertEqual(UNIS['CUET']['source_url']['url'], 'https://cuet.ac.bd/news/208')
        self.assertIsNone(UNIS['NU']['exam_sort_date'])
        self.assertTrue(all(unit['exam_time'] is None for unit in UNIS['GST']['unit_list']))
        self.assertNotIn('সি ইউনিট (বাণিজ্য) ১১:০০–১২:০০', (ROOT / 'calendar.html').read_text())
        for short in ['NU', 'GST', 'CU', 'JnU', 'BUP']:
            self.assertEqual(UNIS[short]['elig_rules'], [])
            checker = json.loads(re.search(r'var UNIS = (\[.*?\]);', (ROOT / 'eligibility.html').read_text()).group(1))
            self.assertEqual(next(item for item in checker if item['short'] == short)['rules'], [])

    def test_sort_filter_and_deadlines_in_actual_javascript(self):
        stub = r'''
const data = JSON.parse(process.env.DATA);
let now = Date.parse('2026-11-11T12:00:00+06:00'); Date.now = () => now;
const controls = {cardSearch:{value:'',addEventListener(n,fn){this.fn=fn}},cardSort:{value:'application',addEventListener(n,fn){this.fn=fn}},cardCount:{},noCards:{}};
const cards = data.universities.map(u=>({dataset:{file:u.short},textContent:u.name_bn+' '+u.short,hidden:false,badge:null,
  querySelector(q){return q==='.chips'?{appendChild:x=>this.badge=x}:this.badge;}}));
const grid={children:cards.slice(),querySelectorAll(){return this.children.slice()},appendChild(x){this.children.splice(this.children.indexOf(x),1);this.children.push(x)}};
global.document={querySelector(){return grid},getElementById(id){return id==='card-data'?{textContent:JSON.stringify(data)}:controls[id]},createElement(){return {dataset:{},setAttribute(){}}}};
global.window={}; global.setInterval=()=>{};
'''
        assertions = r'''
function visible(){return grid.children.filter(c=>!c.hidden).map(c=>c.dataset.file)}
function badge(id){return cards.find(c=>c.dataset.file===id).badge.textContent}
if(visible()[0]!=='DU'||visible()[1]!=='KUET'||badge('DU')!=='আবেদন চলছে')throw Error('open order');
controls.cardSort.value='exam';controls.cardSort.fn();if(visible()[0]!=='DU'||visible()[1]!=='MED')throw Error('exam order');
controls.cardSort.value='original';controls.cardSort.fn();if(visible()[0]!=='MED')throw Error('original order');
controls.cardSearch.value='KUET';controls.cardSearch.fn();if(visible().join()!=='KUET')throw Error('search');
controls.cardSearch.value='no-such-university';controls.cardSearch.fn();if(visible().length||controls.noCards.hidden)throw Error('empty');
controls.cardSearch.value='';now=Date.parse('2026-12-10T17:00:01+06:00');controls.cardSearch.fn();
if(badge('KUET')!=='আবেদনের সময় শেষ'||badge('BUET')!=='আবেদন চলছে'||badge('CU')!=='সূচি অনুযায়ী আবেদনকাল')throw Error('boundaries');
now=Date.parse('2027-01-07T15:00:01+06:00');controls.cardSearch.fn();if(badge('BUET')!=='নতুন আবেদন শুরু শেষ; জমা চলছে')throw Error('cutoff');
now=Date.parse('2027-01-07T17:00:01+06:00');controls.cardSearch.fn();if(badge('BUET')!=='আবেদনের সময় শেষ')throw Error('submission end');
'''
        import os
        env = dict(os.environ, DATA=json.dumps(DATA, ensure_ascii=False))
        subprocess.run(['node', '-e', stub + (ROOT / 'home.js').read_text() + assertions], env=env, check=True, capture_output=True, text=True)

    def test_print_has_fragmentable_layout_and_bounded_pdf_render(self):
        self.assertIn('.cards,body.cols2 .cards{display:block!important}', INDEX)
        self.assertIn('break-inside:auto;page-break-inside:auto;overflow:visible', INDEX)
        self.assertIn('return visible.reduce(function (chain, card)', INDEX)
        self.assertIn('window.print();', INDEX)
        self.assertNotIn('html2canvas(root, h2cOpts)', INDEX)
        self.assertIn("window.__libs = null;", INDEX)

if __name__ == '__main__':
    unittest.main()
