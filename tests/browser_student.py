"""Chromium Phase 3 regressions. Synthetic assignments exist only in temp test sites.

No test hooks or fixtures are shipped in student/. The first test serves its
unaltered production files; other tests inject hooks into the JS HTTP response.
"""
from copy import deepcopy
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import shutil
import tempfile
import threading
import time
import unittest
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
HOOK = """
window.studentTest = {
 state:()=>({assignment,current,done,failures,mode:gameMode,speed:driveSpeed,
   distance:driveDistance,turn:driveTurn,pressed,remaining:mapRemainingMs,
   showMap,modal:modalOpen,zoom:gameZoom,scale:DRIVE_SCALE}),
 generate:generateMaze,
 park(point){Object.assign(current.player,worldCenter(point.x,point.y));
   driveSpeed=0;pressed={};findNearby();},
 tick(ms){mapLastTick=performance.now();updateMapBudget(mapLastTick+ms);},
 map:setMapVisible
};
"""


def fixture(version, unit):
    folder = ROOT / 'tests/fixtures'
    if version == 2:
        folder /= 'v2'
    data = json.loads((folder / f'{unit}.json').read_text())
    # Distinct safe URLs prove the loader is using this unit rather than defaults.
    if unit == 'S02':
        data['googleFormUrl'] = 'https://forms.gle/SyntheticS02Only'
        data['questions'][0]['questionVideoUrl'] = 'https://youtu.be/ChtmE09BSy0'
        data['questions'][0]['explanationVideoUrl'] = 'https://youtu.be/xDARFvArIpc'
    return data


class StaticHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass

    def do_GET(self):
        delay = self.server.delays.get(urlsplit(self.path).path, 0)
        if delay:
            time.sleep(delay)
        try:
            super().do_GET()
        except (BrokenPipeError, ConnectionResetError):
            pass  # A superseded fetch is deliberately aborted by the loader.

    def end_headers(self):
        if self.path.endswith('.json'):
            self.send_header('Cache-Control', 'public, max-age=3600')
        super().end_headers()


class StudentBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch(executable_path='/usr/bin/chromium',
                                            headless=True, args=['--no-sandbox'])

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='emi-student-tests-')
        self.base = Path(self.temp.name)
        self.site = self.base / '~teacher/course/maze'
        shutil.copytree(ROOT / 'student', self.site)
        self.assignment_dir = self.site / 'assignments'
        self.server = ThreadingHTTPServer(('127.0.0.1', 0),
                                         partial(StaticHandler, directory=self.base))
        self.server.daemon_threads = True
        self.server.delays = {}
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.origin = f'http://127.0.0.1:{self.server.server_port}'
        self.prefix = '/~teacher/course/maze/'
        self.url = self.origin + self.prefix
        self.context = self.browser.new_context(viewport={'width': 1366, 'height': 768})
        self.context.route('https://**/*', lambda route: route.fulfill(
            status=200, content_type='text/html', body='<title>External test stub</title>'))
        self.page = self.context.new_page()
        self.errors = []
        self.requests = []
        self.page.on('pageerror', lambda error: self.errors.append(str(error)))
        self.page.on('request', lambda request: self.requests.append(request.url))

    def tearDown(self):
        self.context.close()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.temp.cleanup()
        self.assertEqual(self.errors, [])

    def write(self, file, data):
        (self.assignment_dir / file).write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')

    def publish(self, *units):
        for unit in units:
            self.write(unit['unitId'] + '.json', unit)
        self.write('manifest.json', {'schemaVersion': 1, 'units': [
            {'unitId': u['unitId'], 'title': u['title'], 'file': u['unitId'] + '.json'}
            for u in units]})

    def open(self, hooks=True, index=False):
        if hooks:
            def inject(route):
                response = route.fetch()
                source = response.text().replace('  sizeCanvas();requestAnimationFrame(frame);loader.start();',
                                                 HOOK + '  sizeCanvas();requestAnimationFrame(frame);loader.start();')
                self.assertIn('window.studentTest', source)
                route.fulfill(response=response, body=source)
            self.page.route('**/js/game.js', inject)
        self.page.goto(self.url + ('index.html' if index else ''))
        self.page.wait_for_function("!document.querySelector('#assignmentStatus').textContent.includes('正在讀取')")

    def load(self, unit='S01'):
        self.page.select_option('#unitSelect', unit)
        self.page.click('#loadUnit')
        self.page.wait_for_function("document.querySelector('#assignmentPanel').hidden")

    def state(self):
        return self.page.evaluate('studentTest.state()')

    def question(self, index):
        self.page.evaluate('i=>studentTest.park(studentTest.state().current.stations[i])', index)
        self.page.locator('#maze').focus()
        self.page.keyboard.press('e')
        self.page.wait_for_selector('[data-answer]')

    def assert_no_scroll(self):
        self.assertTrue(self.page.evaluate('document.documentElement.scrollHeight<=innerHeight && document.documentElement.scrollWidth<=innerWidth'))
        self.assertEqual(self.page.evaluate('[scrollX,scrollY]'), [0, 0])

    def test_empty_production_bundle_and_relative_assets_without_hooks(self):
        self.open(hooks=False)
        self.assertIn('沒有已發布', self.page.inner_text('#assignmentStatus'))
        self.assertTrue(self.page.is_disabled('#loadUnit'))
        self.page.keyboard.press('v')
        self.page.keyboard.press('e')
        for size in [(1366, 768), (1024, 768), (390, 844)]:
            self.page.set_viewport_size({'width': size[0], 'height': size[1]})
            self.assert_no_scroll()
        self.assertFalse(any('/S0' in u for u in self.requests))
        self.assertTrue(all(u.startswith(self.url) for u in self.requests))
        self.assertFalse(self.page.evaluate("'studentTest' in window"))

    def test_allowlist_only_and_no_guessed_requests(self):
        a, b = fixture(1, 'S01'), fixture(2, 'S02')
        self.publish(a, b)
        self.write('S03.json', dict(a, unitId='S03'))  # Physically present, unpublished.
        self.open()
        self.assertEqual(self.page.locator('#unitSelect option').evaluate_all('(xs)=>xs.map(x=>x.value)'), ['S01', 'S02'])
        self.assertFalse(any(u.endswith('/S01.json') or u.endswith('/S02.json') for u in self.requests))
        self.page.evaluate("document.querySelector('#unitSelect').add(new Option('Unlisted','S03'));document.querySelector('#unitSelect').value='S03'")
        self.page.click('#loadUnit')
        self.assertIsNone(self.state()['assignment'])
        self.assertFalse(any(u.endswith('/S03.json') for u in self.requests))
        self.load('S02')
        self.assertEqual(self.state()['assignment'], b)
        self.assertTrue(all(urlsplit(u).path.startswith(self.prefix) for u in self.requests))

    def test_v1_v2_four_five_questions_options_links_and_finish(self):
        self.open()
        for version in [1, 2]:
            for unit_id in ['S01', 'S02']:
                with self.subTest(version=version, unit=unit_id):
                    unit = fixture(version, unit_id)
                    self.publish(unit)
                    self.page.click('#refreshManifest')
                    self.page.wait_for_function("!document.querySelector('#unitSelect').disabled")
                    self.load(unit_id)
                    self.assertEqual(self.state()['assignment'], unit)
                    self.assertEqual(len(self.state()['current']['stations']), len(unit['questions']))
                    for index, question in enumerate(unit['questions']):
                        self.question(index)
                        self.assertEqual(self.page.locator('[data-answer]').count(), len(question['options']))
                        self.assertEqual(self.page.locator('[data-answer]').evaluate_all('(xs)=>xs.map(x=>x.dataset.answer)'), list('ABCD')[:len(question['options'])])
                        link = self.page.locator('#dialog a')
                        self.assertEqual(link.get_attribute('href'), question['questionVideoUrl'])
                        self.assertEqual(link.get_attribute('target'), '_blank')
                        self.assertEqual(link.get_attribute('rel'), 'noopener noreferrer')
                        if index == 0:
                            with self.page.expect_popup() as popup:
                                link.click()
                            popup.value.wait_for_load_state()
                            self.assertEqual(popup.value.url, question['questionVideoUrl'])
                            popup.value.close()
                        label = question.get('correctOption') or question['correctOptions'][-1]
                        self.page.click(f'[data-answer="{label}"]')
                        self.assertEqual(self.page.locator('#dialog a').get_attribute('href'), question['explanationVideoUrl'])
                        self.assertTrue(self.state()['done'][index])
                        self.page.click('#continueMaze')
                    self.page.evaluate('studentTest.park(studentTest.state().current.exit)')
                    self.page.locator('#maze').focus()
                    self.page.keyboard.press('e')
                    self.assertEqual(self.page.locator('#dialog a').get_attribute('href'), unit['googleFormUrl'])
                    self.page.click('#closeFinish')
                    self.page.click('#unitLabel')

    def test_every_v2_accepted_label_passes_one_click(self):
        unit = fixture(2, 'S01')
        self.publish(unit)
        self.open()
        self.load()
        for index, question in enumerate(unit['questions']):
            for label in question['correctOptions']:
                self.page.click('#resetBtn')
                self.question(index)
                self.page.click(f'[data-answer="{label}"]')
                self.assertTrue(self.state()['done'][index], (index, label))
                self.assertEqual(self.state()['assignment']['questions'][index]['correctOptions'], question['correctOptions'])
                self.page.click('#continueMaze')

    def test_switching_resets_attempt_player_drive_progress_and_map(self):
        self.publish(fixture(1, 'S01'), fixture(2, 'S02'))
        self.open()
        self.load()
        self.question(0)
        self.page.click('[data-answer="A"]')
        self.page.click('#continueMaze')
        self.question(1)
        self.page.click('[data-answer="A"]')  # v1 Q02 accepts B.
        self.assertEqual(self.state()['failures'], 1)
        self.assertEqual(self.state()['done'], [False]*4)
        self.assertEqual(self.state()['current']['width'], 21)
        self.page.click('#nextRound')
        self.page.keyboard.press('v')
        self.page.keyboard.down('w')
        self.page.wait_for_function('studentTest.state().speed>10')
        self.page.evaluate('studentTest.map(true);studentTest.tick(10000)')
        self.assertLess(self.state()['remaining'], 21000)
        self.page.click('#unitLabel')
        self.page.keyboard.up('w')
        self.assertIsNone(self.state()['current'])
        self.load('S02')
        state = self.state()
        self.assertEqual(state['assignment']['unitId'], 'S02')
        self.assertEqual(state['done'], [False]*5)
        self.assertEqual((state['failures'], state['current']['width']), (0, 25))
        self.assertEqual((state['speed'], state['distance'], state['turn']), (0, 0, 0))
        self.assertEqual(state['mode'], '2d')
        self.assertEqual(state['remaining'], 30000)
        self.assertFalse(state['showMap'])
        self.assertFalse(any(state['pressed'].values()))
        self.assertEqual((state['current']['player']['x'], state['current']['player']['y']), (84, 84))
        self.page.click('#unitLabel')
        self.load('S01')  # Earlier published unit remains available for review.
        self.assertEqual(self.state()['done'], [False]*4)

    def test_missing_malformed_unsupported_and_invalid_unit_retry(self):
        valid = fixture(2, 'S01')
        self.publish(valid)
        self.open()
        invalid = [None, '{bad', dict(valid, schemaVersion=99), dict(valid, unitId='S02')]
        broken = deepcopy(valid)
        broken['questions'][0]['correctOptions'] = []
        invalid.append(broken)
        for data in invalid:
            with self.subTest(data=str(data)[:60]):
                if data is None:
                    (self.assignment_dir / 'S01.json').unlink()
                elif isinstance(data, str):
                    (self.assignment_dir / 'S01.json').write_text(data)
                else:
                    self.write('S01.json', data)
                self.page.click('#loadUnit')
                self.page.wait_for_function("document.querySelector('#assignmentStatus').textContent.includes('可重試')")
                self.assertIsNone(self.state()['current'])
                self.assertIsNone(self.state()['assignment'])
                self.assertTrue(self.page.is_visible('#assignmentPanel'))
                self.write('S01.json', valid)
                self.load()
                self.page.click('#unitLabel')

    def test_bad_manifests_fail_closed_and_refresh_recovers(self):
        valid = fixture(1, 'S01')
        self.publish(valid)
        self.open()
        self.load()
        self.page.click('#unitLabel')
        invalid = [None, '{oops', {'schemaVersion': 2, 'units': []},
                   {'schemaVersion': 1, 'units': [{'unitId': 'S01', 'title': 'bad', 'file': '../S01.json'}]},
                   {'schemaVersion': 1, 'units': [{'unitId': 'S13', 'title': 'bad', 'file': 'S13.json'}]}]
        for data in invalid:
            with self.subTest(data=data):
                if data is None:
                    (self.assignment_dir / 'manifest.json').unlink()
                elif isinstance(data, str):
                    (self.assignment_dir / 'manifest.json').write_text(data)
                else:
                    self.write('manifest.json', data)
                self.page.click('#refreshManifest')
                self.page.wait_for_function("document.querySelector('#assignmentStatus').textContent.includes('請重新整理')")
                self.assertTrue(self.page.is_disabled('#loadUnit'))
                self.assertEqual(self.page.locator('#unitSelect option').count(), 0)
                self.assertIsNone(self.state()['assignment'])
        self.publish(valid)
        self.page.click('#refreshManifest')
        self.page.wait_for_function("!document.querySelector('#unitSelect').disabled")
        self.load()
        self.assertEqual(self.state()['assignment']['unitId'], 'S01')
        self.assertFalse(any('/../' in u or '/S13.json' in u for u in self.requests))

    def test_static_manifest_refresh_reload_and_root_hosting(self):
        a, b = fixture(1, 'S01'), fixture(2, 'S02')
        self.publish(a)
        # No Playwright routes: actual Chromium HTTP cache against cacheable static files.
        # Even a route for external HTTPS disables the context's HTTP cache.
        self.context.unroute('https://**/*')
        self.open(hooks=False, index=True)
        self.load()
        self.page.click('#unitLabel')
        self.publish(a, b)
        self.page.click('#refreshManifest')
        self.page.wait_for_function("document.querySelector('#unitSelect').options.length===2")
        self.load('S02')
        self.page.click('#unitLabel')
        b['title'] = 'TEST ONLY UPDATED S02'
        b['questions'][0]['title'] = 'TEST ONLY UPDATED Q01'
        self.publish(b)
        self.page.reload()
        self.page.wait_for_function("document.querySelector('#unitSelect').options.length===1")
        self.assertEqual(self.page.locator('#unitSelect').input_value(), 'S02')
        self.load('S02')
        self.assertIn(b['title'], self.page.get_attribute('#unitLabel', 'title'))
        self.assertIn(b['questions'][0]['title'], self.page.inner_text('#questlist'))
        self.page.click('#unitLabel')
        self.publish()
        self.page.click('#refreshManifest')
        self.page.wait_for_function("document.querySelector('#assignmentStatus').textContent.includes('沒有已發布')")
        # Same bundle also works from the server root.
        for child in self.site.iterdir():
            destination = self.base / child.name
            if child.is_dir():
                shutil.copytree(child, destination)
            else:
                shutil.copy2(child, destination)
        self.page.goto(self.origin + '/')
        self.page.wait_for_function("document.querySelector('#assignmentStatus').textContent.includes('沒有已發布')")
        self.assertTrue(self.page.is_disabled('#loadUnit'))

    def test_overlapping_loads_refresh_and_network_failure(self):
        self.publish(fixture(1, 'S01'), fixture(2, 'S02'))
        self.server.delays[self.prefix + 'assignments/S01.json'] = .6
        self.open()
        self.page.click('#loadUnit')
        self.page.select_option('#unitSelect', 'S02')
        self.page.click('#loadUnit')
        self.page.wait_for_function("studentTest.state().assignment?.unitId==='S02'")
        self.page.wait_for_timeout(750)
        self.assertEqual(self.state()['assignment']['unitId'], 'S02')
        self.page.click('#unitLabel')
        self.page.select_option('#unitSelect', 'S01')
        self.page.click('#loadUnit')
        self.publish(fixture(2, 'S02'))
        self.page.click('#refreshManifest')
        self.page.wait_for_function("document.querySelector('#unitSelect').value==='S02'")
        self.page.wait_for_timeout(750)
        self.assertIsNone(self.state()['assignment'])
        self.page.route('**/assignments/S02.json', lambda route: route.abort('failed'))
        self.page.click('#loadUnit')
        self.page.wait_for_function("document.querySelector('#assignmentStatus').textContent.includes('檢查連線')")
        self.assertIsNone(self.state()['current'])
        self.page.unroute('**/assignments/S02.json')
        self.load('S02')

    def test_modes_keyboard_touch_zoom_modal_blur_and_layout(self):
        unit = fixture(2, 'S02')
        self.publish(unit)
        self.open()
        self.load('S02')
        self.page.keyboard.down('ArrowDown')
        self.page.wait_for_function('studentTest.state().current.player.y>90')
        self.page.keyboard.up('ArrowDown')
        moved = self.state()['current']['player']
        self.page.keyboard.press('v')
        self.assertEqual(self.state()['mode'], 'drive')
        self.assertEqual(self.state()['current']['player']['y'], moved['y'])
        self.page.keyboard.down('w')
        self.page.wait_for_function('studentTest.state().speed>15')
        self.page.evaluate("window.dispatchEvent(new Event('blur'))")
        self.assertEqual(self.state()['speed'], 0)
        self.assertFalse(any(self.state()['pressed'].values()))
        self.page.keyboard.up('w')
        self.question(0)
        self.assertEqual(self.state()['speed'], 0)
        self.assertFalse(any(self.state()['pressed'].values()))
        self.page.click('[data-answer="A"]')
        self.page.click('#continueMaze')
        self.page.keyboard.press('v')
        self.assertTrue(self.state()['done'][0])
        self.page.select_option('#zoomSelect', '1.75')
        self.assertEqual(self.state()['zoom'], 1.75)
        self.page.select_option('#zoomSelect', '1.5')
        self.assertEqual(self.state()['zoom'], 1.5)
        self.page.click('#panelToggle')
        self.page.keyboard.press('Escape')
        self.assertEqual(self.page.get_attribute('#sidePanel', 'aria-hidden'), 'true')
        for width, height in [(1366, 768), (1024, 768), (390, 844)]:
            self.page.set_viewport_size({'width': width, 'height': height})
            self.assert_no_scroll()
            for control in ['#unitLabel', '#modeToggle', '#panelToggle', '#zoomSelect', '#progressStrip']:
                box = self.page.locator(control).bounding_box()
                self.assertIsNotNone(box, control)
                self.assertGreaterEqual(box['x'], 0, control)
                self.assertLessEqual(box['x'] + box['width'], width, control)
            (ROOT / 'test-results').mkdir(exist_ok=True)
            self.page.screenshot(path=str(ROOT / f'test-results/phase-3-2d-{width}.png'))
            self.page.keyboard.press('v')
            self.assert_no_scroll()
            if width == 1366:
                self.page.screenshot(path=str(ROOT / 'test-results/phase-3-drive.png'))
            self.page.keyboard.press('v')
        self.page.evaluate('studentTest.park(studentTest.state().current.stations[1])')
        self.page.click('#touchInteract')
        self.assertEqual(self.page.locator('[data-answer]').count(), 4)
        self.page.click('#dialogClose')
        self.page.set_viewport_size({'width': 1366, 'height': 768})
        self.page.click('#unitLabel')
        self.page.locator('#unitSelect').focus()
        self.page.keyboard.press('v')
        self.assertEqual(self.state()['mode'], '2d')
        self.assert_no_scroll()

    def test_dynamic_stations_reachable_unique_all_sizes_and_map_budget(self):
        self.open()
        total = 0
        for version in [1, 2]:
            for unit_id in ['S01', 'S02']:
                unit = fixture(version, unit_id)
                self.publish(unit)
                self.page.click('#refreshManifest')
                self.page.wait_for_function("!document.querySelector('#unitSelect').disabled")
                self.load(unit_id)
                total += self.page.evaluate('''count=>{
                  let total=0;const oldNow=Date.now,oldRandom=Math.random;
                  try{for(const [w,h] of [[25,19],[21,15],[17,13],[13,9]]){
                    for(let seed=1;seed<=100;seed++){
                      Date.now=()=>seed*104729;Math.random=()=>.25;
                      const m=studentTest.generate(w,h),keys=m.stations.map(p=>`${p.x},${p.y}`);
                      if(keys.length!==count||new Set(keys).size!==count)throw Error('station count/overlap');
                      const seen=new Set(['2,2']),queue=[[2,2]];
                      for(let i=0;i<queue.length;i++){
                        const [x,y]=queue[i];
                        for(const [dx,dy] of [[1,0],[-1,0],[0,1],[0,-1]]){
                          const nx=x+dx,ny=y+dy,key=`${nx},${ny}`;
                          if(m.grid[ny]?.[nx]===0&&!seen.has(key)){seen.add(key);queue.push([nx,ny]);}
                        }
                      }
                      for(const p of [...m.stations,m.exit])if(!seen.has(`${p.x*2},${p.y*2}`))throw Error('unreachable');
                      if(keys.includes('1,1')||keys.includes(`${m.exit.x},${m.exit.y}`))throw Error('start/exit overlap');
                      total++;
                    }
                  }}finally{Date.now=oldNow;Math.random=oldRandom;}return total;
                }''', len(unit['questions']))
                self.page.evaluate('studentTest.map(true);studentTest.tick(10000);studentTest.map(false)')
                remaining = self.state()['remaining']
                self.page.evaluate('studentTest.tick(5000)')
                self.assertAlmostEqual(self.state()['remaining'], remaining, delta=80)
                self.page.evaluate('studentTest.map(true);studentTest.tick(40000)')
                self.assertEqual(self.state()['remaining'], 0)
                self.assertFalse(self.state()['showMap'])
                self.page.click('#resetBtn')
                self.assertEqual(self.state()['remaining'], 30000)
                self.assertEqual(self.state()['current']['width'], 25)
                self.page.click('#unitLabel')
        self.assertEqual(total, 1600)

    def test_untrusted_text_is_literal_and_all_valid_units_S01_to_S12(self):
        unit = fixture(2, 'S01')
        text = '<img src=x onerror="window.injected=true">中文 & "quoted"'
        unit['title'] = text
        for question in unit['questions']:
            question['title'] = question['prompt'] = question['explanationText'] = text
            question['options'][0] = text
        self.publish(unit)
        self.open()
        self.assertIn(text, self.page.inner_text('#unitSelect'))
        self.load()
        self.question(0)
        self.assertEqual(self.page.inner_text('#dialog h2'), text)
        self.assertEqual(self.page.locator('#dialog img').count(), 0)
        self.page.click('[data-answer="A"]')
        self.assertEqual(self.page.inner_text('#dialog .question'), text)
        self.assertFalse(self.page.evaluate('Boolean(window.injected)'))
        self.page.click('#continueMaze')
        self.page.click('#unitLabel')
        all_units = [dict(fixture(1, 'S01'), unitId=f'S{i:02d}', title=f'TEST ONLY S{i:02d}') for i in range(1, 13)]
        self.publish(*all_units)
        self.page.click('#refreshManifest')
        self.page.wait_for_function("document.querySelector('#unitSelect').options.length===12")
        self.load('S12')
        self.assertEqual(self.state()['assignment']['unitId'], 'S12')


if __name__ == '__main__':
    unittest.main(verbosity=2)
