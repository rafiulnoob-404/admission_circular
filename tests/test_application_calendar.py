"""Admission windows must match the cards, and calendar controls work."""
import json
import re
import subprocess
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
CAL = (ROOT / 'calendar.html').read_text()
INDEX = (ROOT / 'index.html').read_text()
DATA = json.loads(re.search(r'<script type="application/json" id="card-data">(.*?)</script>', INDEX, re.S).group(1))
UNIS = {u['short']: u for u in DATA['universities']}
APPS = json.loads(re.search(r'var APPLICATIONS = (\[.*?\]);', CAL).group(1))

class ApplicationCalendar(unittest.TestCase):
    def test_windows_and_uncertain_dates(self):
        entries = {a['u']:a for a in APPS}
        for u,start,end in [('ঢাকা বিশ্ববিদ্যালয়','2026-11-11','2026-11-25'),('কুয়েট (KUET)','2026-11-10','2026-12-10'),('রাজশাহী বিশ্ববিদ্যালয়','2026-11-15','2026-11-30'),('জগন্নাথ বিশ্ববিদ্যালয়','2026-11-25','2026-12-10'),('চট্টগ্রাম বিশ্ববিদ্যালয়','2026-12-10','2027-01-10'),('কুমিল্লা বিশ্ববিদ্যালয়','2026-12-10','2026-12-31'),('মিস্ট (MIST)','2027-01-05','2027-01-21')]:
            self.assertEqual((entries[u]['s'],entries[u]['e']),(start,end))
        self.assertEqual(entries['বুয়েট (BUET)']['e'], '2027-01-07')
        self.assertEqual((entries['জাহাঙ্গীরনগর বিশ্ববিদ্যালয়']['s'], entries['জাহাঙ্গীরনগর বিশ্ববিদ্যালয়']['e']), ('2026-11-22', '2026-12-15'))
        self.assertIn('বিকাল ৫টা', entries['কুয়েট (KUET)']['end'])
        self.assertIn('বিকাল ৫টা', UNIS['KUET']['apply_end'])
        self.assertIn('দুপুর ১২টা', UNIS['JnU']['apply_window'])
        self.assertIsNone(UNIS['KhU']['apply_start'])
        self.assertIn('মতভেদ', UNIS['AGRI']['exam_date'])

    def test_render_filter_and_unknown_end(self):
        js = re.search(r'<script>\s*(var APPLICATIONS = .*?)</script>', CAL, re.S).group(1)
        stub = '''
const nodes={}; function node(id){return nodes[id] ||= {value:'',checked:false,innerHTML:'',children:[],appendChild(x){this.children.push(x)},addEventListener(){}}}
global.document={getElementById:node,createElement(){return {}}};
'''
        test = '''
if(!node('applications').innerHTML.includes('আবেদনের সময়সূচি'))throw Error('missing');
node('q').value='কুয়েট';render();if(!node('applications').innerHTML.includes('বিকাল ৫টা')||node('applications').innerHTML.includes('জগন্নাথ'))throw Error('search');
node('q').value='';node('uni').value='জগন্নাথ বিশ্ববিদ্যালয়';render();if(!node('applications').innerHTML.includes('দুপুর ১২টা')||node('applications').innerHTML.includes('কুয়েট'))throw Error('filter');
today=new Date(2028,0,1);node('uni').value='';node('hp').checked=true;render();if(node('applications').innerHTML.includes('বুয়েট')||node('applications').innerHTML.includes('কুয়েট'))throw Error('past');
'''
        subprocess.run(['node','-e',stub+js+test],check=True,capture_output=True,text=True)

if __name__=='__main__':unittest.main()
