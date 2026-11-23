"""Regression coverage for the supplied MIST, JU and BUET notices."""
import json
import os
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / 'index.html').read_text()
ELIG = (ROOT / 'eligibility.html').read_text()
CAL = (ROOT / 'calendar.html').read_text() + (ROOT / 'data/calendar.json').read_text()
DATA = json.loads((ROOT / 'data/universities.json').read_text())
UNIS = {u['short']: u for u in DATA['universities']}
CHECKER = {u['short']: u for u in [{'short':u['short'], 'name_bn':u.get('checker_name_bn',u['name_bn']), 'rules':u.get('elig_rules',[])} for u in json.loads((ROOT / 'data/universities.json').read_text())['universities']]}
APPS = {a['u']: a for a in json.loads((ROOT / 'data/calendar.json').read_text())['applications']}

def card(k):
    return re.search(r'<article\b[^>]*data-file="' + k + r'"[^>]*>.*?</article>', INDEX, re.S).group()

class ProvidedNotices(unittest.TestCase):
    def test_buet_revised_dates_and_deadlines(self):
        u = UNIS['BUET']
        self.assertEqual(u['exam_sort_date'], '2027-02-01')
        self.assertEqual((APPS['বুয়েট (BUET)']['s'], APPS['বুয়েট (BUET)']['e']), ('2026-12-01', '2027-01-07'))
        self.assertEqual(u['application_schedule']['new_application_cutoff'], '2027-01-07T15:00:00+06:00')
        self.assertEqual(u['application_schedule']['end'], '2027-01-07T17:00:00+06:00')
        self.assertIn('নতুন আবেদন শুরু শেষ বিকাল ৩টা', card('BUET'))
        self.assertIn('৭ জানুয়ারি বিকাল ৫টা', card('BUET'))
        self.assertNotIn('সূচি পেছানো হয়নি', card('BUET'))
        self.assertFalse(any(e['s']=='2027-01-16' and e['u']=='বুয়েট (BUET)' for e in json.loads((ROOT / 'data/calendar.json').read_text())['events']))
        self.assertTrue(any(e['s']=='2027-02-01' and e['u']=='বুয়েট (BUET)' for e in json.loads((ROOT / 'data/calendar.json').read_text())['events']))
        self.assertIn('২ ডিসেম্বর ২০২৫-এর পরে', (ROOT / 'buet-admission.html').read_text())
        self.assertEqual(CHECKER['BUET']['rules'], [])  # Cannot model exceptions safely.

    def test_mist_notice_data_in_all_surfaces(self):
        u = UNIS['MIST']
        self.assertIsNone(u['seats'])
        self.assertEqual([x['exam_time'] for x in u['unit_list']], ['সকাল ১০টা–১১টা', 'সকাল ৯টা–১২টা', 'বিকাল ২টা–৪টা'])
        self.assertIsNone(u['application_schedule'])  # Disputed; do not compute misleading application status.
        for item in ('১,৩০০', '১,৫০০', '১,১০০', 'গণিত ২৫', 'প্রতিটিতে ৩.৫০'):
            self.assertIn(item, (ROOT / 'mist-admission.html').read_text())
        self.assertIn('MIST ওয়েব নোটিশে ২২ জানুয়ারি', CAL)
        self.assertIn('SSC-র চতুর্থ বিষয় বাদে', (ROOT / 'mist-admission.html').read_text())
        self.assertEqual(CHECKER['MIST']['rules'], [])

    def test_ju_rules_mirror_and_thresholds(self):
        rules = UNIS['JU']['elig_rules']
        self.assertEqual(rules, CHECKER['JU']['rules'])
        self.assertTrue(all(r['partial'] for r in rules))
        self.assertEqual((APPS['জাহাঙ্গীরনগর বিশ্ববিদ্যালয়']['s'], APPS['জাহাঙ্গীরনগর বিশ্ববিদ্যালয়']['e']), ('2026-11-22', '2026-12-15'))
        self.assertEqual(UNIS['JU']['seats'], '১,৮৪৮টি')
        self.assertIn('সম্ভাব্য', UNIS['JU']['exam_date'])
        self.assertIn('row.rule.partial', ELIG)
        check = re.search(r'function check\(rule,d\)\{.*?\n\}', ELIG, re.S).group()
        script = 'function bn(v){return String(v)};function fmt(v){return v.toFixed(2)};\n' + check + '\nconst rules=' + json.dumps(rules, ensure_ascii=False) + r''';
function d(g,s,h,sy=2024,hy=2026){return {ssc:{year:sy,gpa:s},hsc:{year:hy,group:g,gpa:h},subj:{}}}
function rule(n){return rules.find(x=>x.unit===n)}
for(const [n,x,expected] of [
 ['A ইউনিট',d('বিজ্ঞান',3.5,4),'pass'],['A ইউনিট',d('বিজ্ঞান',3.49,4.5),'fail'],
 ['B ইউনিট (বিজ্ঞান)',d('বিজ্ঞান',3.5,4),'pass'],['B ইউনিট (মানবিক/ব্যবসায়)',d('মানবিক',3,3.5),'pass'],
 ['C ইউনিট (বিজ্ঞান/ব্যবসায়)',d('ব্যবসায়',3,4.5),'fail'],['C ইউনিট (মানবিক)',d('মানবিক',3,3.5),'pass'],
 ['D ইউনিট',d('বিজ্ঞান',4,4),'pass'],['D ইউনিট',d('বিজ্ঞান',4,3.99),'fail'],
 ['C1 ইউনিট',d('মানবিক',4,4,2022),'fail'],['E ইউনিট (বিজ্ঞান)',d('বিজ্ঞান',4,4,2024,2024),'fail']])
 if(check(rule(n),x).state!==expected)throw Error(n);
'''
        subprocess.run(['node', '-e', script], check=True, capture_output=True, text=True)

    def test_supplied_copies_are_accessible_from_details(self):
        for prefix, count in [('mist', 3), ('ju', 5)]:
            page = (ROOT / (prefix + '-admission.html')).read_text()
            for i in range(1, count + 1):
                f = 'notices/2026-27/' + prefix + '-' + str(i) + '.jpg'
                self.assertIn(f, page)
                self.assertTrue((ROOT / f).is_file())
        for i in (1, 2):
            self.assertTrue((ROOT / ('notices/2026-27/ju-seats-' + str(i) + '.jpg')).is_file())
        self.assertIn('অফিসিয়াল ডোমেইনে হোস্ট করা নয়', (ROOT / 'buet-admission.html').read_text())

if __name__ == '__main__':
    unittest.main()
