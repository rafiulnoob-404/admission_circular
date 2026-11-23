"""JSON loading and failure behaviour of the static site."""
import json
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class JsonLoading(unittest.TestCase):
    def test_shared_university_data_and_calendar_structure(self):
        data = json.loads((ROOT / 'data/universities.json').read_text())
        cal = json.loads((ROOT / 'data/calendar.json').read_text())
        self.assertEqual(len(data['universities']), 22)
        self.assertEqual(len({u['short'] for u in data['universities']}), 22)
        self.assertGreater(len(cal['events']), 30)
        self.assertGreater(len(cal['applications']), 5)
        self.assertNotIn('id="card-data"', (ROOT / 'index.html').read_text())
        self.assertIn("fetch('data/universities.json')", (ROOT / 'home.js').read_text())
        self.assertIn("fetch('data/universities.json')", (ROOT / 'eligibility.html').read_text())
        self.assertIn("fetch('data/calendar.json')", (ROOT / 'calendar.html').read_text())

    def test_home_stays_searchable_if_json_fails(self):
        js = (ROOT / 'home.js').read_text()
        stub = r'''
const options=[{disabled:false},{disabled:false}];
const controls={cardSearch:{value:'',addEventListener(n,fn){this.fn=fn}},cardSort:{value:'application',addEventListener(n,fn){this.fn=fn},querySelectorAll(){return options}},cardCount:{},noCards:{},homeDataStatus:{}};
const cards=['DU','BUTEX'].map(id=>({dataset:{file:id,uni:id},textContent:id,hidden:false,badge:null,querySelector(q){return q==='.chips'?{appendChild:x=>this.badge=x}:this.badge;}}));
const grid={children:cards.slice(),querySelectorAll(){return this.children.slice()},appendChild(x){this.children.splice(this.children.indexOf(x),1);this.children.push(x)}};
global.document={querySelector(){return grid},getElementById(id){return controls[id]},createElement(){return {dataset:{},setAttribute(){}}}};
global.window={};global.setInterval=()=>{};global.fetch=()=>Promise.reject(Error('offline'));console.error=()=>{};
'''
        test = r'''
setImmediate(()=>{
 if(!controls.homeDataStatus.textContent.includes('লোড করা যায়নি'))throw Error('missing error');
 if(!options.every(o=>o.disabled)||controls.cardSort.value!=='original')throw Error('unsafe date sort');
 if(cards.some(c=>c.badge.textContent!=='তথ্য লোড হয়নি'))throw Error('status');
 controls.cardSearch.value='BUTEX';controls.cardSearch.fn();
 if(!cards[0].hidden||cards[1].hidden)throw Error('search unavailable');
});
'''
        subprocess.run(['node', '-e', stub + js + test], check=True, capture_output=True, text=True)

    def test_calendar_failure_reports_error(self):
        html = (ROOT / 'calendar.html').read_text()
        js = re.search(r'<script>\s*(var APPLICATIONS = .*?)</script>', html, re.S).group(1)
        stub = r'''
const nodes={};function node(id){return nodes[id] ||= {value:'',checked:false,innerHTML:'',textContent:'',appendChild(){},addEventListener(){}}}
global.document={getElementById:node,createElement(){return {}}};global.fetch=()=>Promise.reject(Error('offline'));console.error=()=>{};
'''
        test = "setImmediate(()=>{if(!node('calendarDataStatus').textContent.includes('লোড করা যায়নি'))throw Error('missing error')});"
        subprocess.run(['node', '-e', stub + js + test], check=True, capture_output=True, text=True)

if __name__ == '__main__':
    unittest.main()
