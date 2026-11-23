import json
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / 'index.html').read_text()
ELIG = (ROOT / 'eligibility.html').read_text()
CAL = (ROOT / 'calendar.html').read_text()
UNIS = {u['short']: u for u in json.loads(re.search(r'<script type="application/json" id="card-data">(.*?)</script>', INDEX, re.S)[1])['universities']}
CHECK = {u['short']: u for u in json.loads(re.search(r'var UNIS = (\[.*?\]);', ELIG)[1])}

class NewNotices(unittest.TestCase):
    def test_butex_rules_and_application(self):
        uni = UNIS['BUTEX']
        self.assertEqual(uni['elig_rules'], CHECK['BUTEX']['rules'])
        self.assertEqual(uni['exam_sort_date'], '2027-01-29')
        self.assertEqual(uni['application_schedule']['end'], '2027-01-10T23:59:59+06:00')
        self.assertEqual(uni['seats'], '৬৩০টি')
        self.assertIn('2027-01-29', CAL)
        for n in range(1, 4): self.assertTrue((ROOT / f'notices/2026-27/butex-{n}.jpg').exists())
        check = re.search(r'function check\(rule,d\)\{.*?\n\}', ELIG, re.S)[0]
        js = 'function bn(x){return String(x)};function fmt(x){return x.toFixed(2)};' + check + '\nconst rule=' + json.dumps(uni['elig_rules'][0], ensure_ascii=False) + ''';
const d={ssc:{year:2024,gpa:4},hsc:{year:2026,group:'বিজ্ঞান',gpa:4},subj:{'গণিত':4.5,'পদার্থবিজ্ঞান':4.5,'রসায়ন':4,'ইংরেজি':4}};
if(check(rule,d).state!=='pass')process.exit(1);
d.subj['ইংরেজি']=3.49; if(check(rule,d).state!=='fail')process.exit(2);
d.subj['ইংরেজি']=NaN; if(check(rule,d).state!=='unknown')process.exit(3);
d.subj['ইংরেজি']=3.5;d.subj['গণিত']=3.5; if(check(rule,d).state!=='fail')process.exit(4);
'''
        subprocess.run(['node', '-e', js], check=True, capture_output=True, text=True)

    def test_bup_and_ruet_calendar(self):
        self.assertEqual(UNIS['BUP']['application_schedule']['end'][:10], '2027-01-05')
        for day in ['2027-01-16', '2027-01-22', '2027-01-23', '2027-01-28']:
            self.assertIn(day, CAL)
        self.assertNotIn('2027-01-14', CAL)
        self.assertEqual(UNIS['RUET']['exam_sort_date'], '2027-01-28')
        self.assertIn('FMS', (ROOT / 'bup-admission.html').read_text())

    def test_conflicts_and_date_semantics(self):
        self.assertIsNone(UNIS['AGRI']['exam_sort_date'])
        self.assertIn('মতভেদ', UNIS['AGRI']['exam_date'])
        self.assertIn('দিন অনিশ্চিত', CAL)
        self.assertIsNone(UNIS['MIST']['application_schedule'])
        self.assertIsNone(UNIS['MIST']['exam_sort_date'])
        self.assertIn('MIST ওয়েব নোটিশে ২২ জানুয়ারি', CAL)
        for name in ['index.html', 'calendar.html', 'eligibility.html']:
            page = (ROOT / name).read_text()
            self.assertIn('data-bd-today', page)
            self.assertIn('সাইটের আপডেট:', page)
            self.assertIn('today.js', page)
        self.assertIn("timeZone: 'Asia/Dhaka'", (ROOT / 'today.js').read_text())

if __name__ == '__main__': unittest.main()
