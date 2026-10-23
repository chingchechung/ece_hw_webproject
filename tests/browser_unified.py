"""English UI and identical synthetic assignments in the extracted unified ZIP."""
from functools import partial
from http.server import ThreadingHTTPServer
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import unittest
from urllib.parse import urlsplit
from zipfile import ZipFile

from playwright.sync_api import sync_playwright
from browser_student import HOOK, StaticHandler, fixture
from browser_support import save_browser_artifacts

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'test-results/unified-release'


class UnifiedBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        OUT.mkdir(parents=True, exist_ok=True)
        subprocess.run(['python', 'release/package.py'], cwd=ROOT, check=True)
        cls.pw = sync_playwright().start()
        executable = (os.environ.get('EMI_3D_BROWSER_PATH') or
                      os.environ.get('EMI_BROWSER_EXECUTABLE') or cls.pw.chromium.executable_path)
        if not Path(executable).is_file():
            executable = shutil.which('chromium') or shutil.which('chromium-browser')
        cls.browser = cls.pw.chromium.launch(executable_path=executable, args=[
            '--no-sandbox', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'])

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        with ZipFile(OUT / 'Engineering-Maze-Lab-1.0.0.zip') as archive:
            archive.extractall(self.base / '~teacher/course')
        self.site = self.base / '~teacher/course/Engineering-Maze-Lab'
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), partial(StaticHandler, directory=self.base))
        self.server.delays = {}
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f'http://127.0.0.1:{self.server.server_port}/~teacher/course/Engineering-Maze-Lab/'
        self.contexts = []
        self.errors = []
        self.requests = []

    def tearDown(self):
        try:
            for index, (context, page) in enumerate(self.contexts):
                save_browser_artifacts(context, page, OUT,
                                       f'{self._testMethodName}-{index}', self.errors)
                context.close()
            (OUT / f'{self._testMethodName}-requests.json').write_text(
                json.dumps(self.requests, indent=2), encoding='utf-8')
        finally:
            self.server.shutdown()
            self.server.server_close()
            self.thread.join()
            self.temp.cleanup()
        self.assertEqual(self.errors, [])

    def page(self, edition, hooks=False, width=1366, height=768, dpr=1):
        context = self.browser.new_context(viewport={'width': width, 'height': height},
                                           device_scale_factor=dpr)
        context.tracing.start(screenshots=True, snapshots=True, sources=True)
        context.route('https://**/*', lambda route: route.abort())
        page = context.new_page()
        self.contexts.append((context, page))
        page.on('pageerror', lambda error: self.errors.append(str(error)))
        page.on('request', lambda request: self.requests.append(request.url))
        if hooks:
            def inject(route):
                response = route.fetch()
                body = response.text().replace('  sizeCanvas();requestAnimationFrame(frame);loader.start();',
                                              HOOK + '  sizeCanvas();requestAnimationFrame(frame);loader.start();')
                self.assertIn('window.studentTest', body)
                route.fulfill(response=response, body=body)
            context.route('**/js/game.js*', inject)
        page.goto(self.url + edition + '/')
        if edition == 'lite':
            page.wait_for_function("!document.querySelector('#assignmentStatus').textContent.startsWith('Reading')")
        else:
            page.wait_for_function('window.showcase?.snapshot().ready', timeout=120000)
            page.click('#settings')
            page.click('[data-quality="Low"]')
            page.click('#settings-close')
        return page

    def no_scroll(self, page):
        self.assertTrue(page.evaluate('document.documentElement.scrollHeight<=innerHeight && document.documentElement.scrollWidth<=innerWidth'))
        self.assertEqual(page.evaluate('[scrollX,scrollY]'), [0, 0])

    def english(self, page, instructor=None):
        self.assertEqual(page.locator('html').get_attribute('lang'), 'en')
        owned = page.evaluate("document.body.textContent + [...document.querySelectorAll('[aria-label],[title]')].map(e=>(e.getAttribute('aria-label')||'')+(e.title||'')).join('')")
        # Synthetic instructor values may intentionally contain Chinese. They
        # are asserted verbatim separately, never treated as application UI.
        def values(data):
            if isinstance(data, str):
                yield data
            elif isinstance(data, dict):
                for value in data.values():
                    yield from values(value)
            elif isinstance(data, list):
                for value in data:
                    yield from values(value)
        for value in sorted(values(instructor), key=len, reverse=True):
            owned = owned.replace(value, '')
        self.assertNotRegex(owned, r'[\u3400-\u9fff]')

    def publish(self, unit):
        data = json.dumps(unit, ensure_ascii=False).encode()
        manifest = json.dumps({'schemaVersion': 1, 'units': [
            {'unitId': unit['unitId'], 'title': unit['title'], 'file': unit['unitId'] + '.json'}]})
        for edition in ('lite', '3d'):
            directory = self.site / edition / 'assignments'
            (directory / (unit['unitId'] + '.json')).write_bytes(data)
            (directory / 'manifest.json').write_text(manifest, encoding='utf-8')
        return data

    def load_lite(self, page, unit):
        if page.locator('#assignmentPanel').is_hidden():
            page.click('#unitLabel')
        page.click('#refreshManifest')
        page.wait_for_function("!document.querySelector('#unitSelect').disabled")
        page.select_option('#unitSelect', unit['unitId'])
        page.click('#loadUnit')
        if page.locator('#switchWarning').is_visible():
            page.click('#confirmSwitch')
        page.wait_for_function("document.querySelector('#assignmentPanel').hidden")

    def load_three(self, page, unit):
        page.click('#assignment-mode')
        page.wait_for_function("!document.querySelector('#unit-select').disabled")
        page.select_option('#unit-select', unit['unitId'])
        page.click('#load-assignment')
        page.click('#confirm-assignment')
        page.wait_for_function("!document.querySelector('#assignment-picker').open")

    def test_empty_package_english_interfaces_and_nested_responsive_paths(self):
        for edition in ('lite', '3d'):
            page = self.page(edition)
            for width, height in ((1280, 800), (1366, 768), (1920, 1080)):
                page.set_viewport_size({'width': width, 'height': height})
                self.english(page)
                self.no_scroll(page)
            page.set_viewport_size({'width': 1366, 'height': 768})
            if edition == 'lite':
                self.assertEqual(page.locator('.top .tag').count(), 0)
                self.assertIn('No published units', page.inner_text('#assignmentStatus'))
                page.set_viewport_size({'width': 390, 'height': 844})
                self.no_scroll(page)
                page.set_viewport_size({'width': 1366, 'height': 768})
            page.screenshot(path=str(OUT / f'{edition}-english-interface.png'))
        self.assertFalse(any('/S01.json' in url for url in self.requests))
        self.assertTrue(all('/~teacher/course/Engineering-Maze-Lab/' in url
                            for url in self.requests if url.startswith('http:')))

    def test_same_published_v1_v2_four_five_question_json_and_verbatim_instructor_text(self):
        lite = self.page('lite', hooks=True)
        three = self.page('3d')
        evidence = []
        for version in (1, 2):
            for unit_id in ('S01', 'S02'):
                with self.subTest(version=version, unit=unit_id):
                    unit = fixture(version, unit_id)
                    unit['title'] = '測試課程 · Synthetic instructor title'
                    unit['questions'][0]['title'] = '題目 · Synthetic instructor question'
                    unit['questions'][0]['prompt'] = '保留原文 <b>literal</b>'
                    unit['questions'][0]['options'][0] = '選項原文'
                    data = self.publish(unit)
                    self.load_lite(lite, unit)
                    self.load_three(three, unit)
                    loaded = lite.evaluate('studentTest.state().assignment')
                    self.assertEqual(loaded, unit)
                    state = three.evaluate('showcase.snapshot()')
                    self.assertEqual(state['assignment'], {key: unit[key] for key in
                                     ('unitId', 'title', 'schemaVersion')} |
                                     {'questionCount': len(unit['questions'])})
                    self.assertEqual(state['game']['checkpoints'][0]['label'], unit['questions'][0]['title'])
                    self.assertEqual(len(state['game']['completed']), len(unit['questions']))
                    self.assertFalse(any(state['game']['completed']))
                    self.assertEqual(state['game']['map']['remainingMs'], 30000)
                    self.assertEqual(state['game']['vehicle']['distance'], 0)
                    for page, edition in ((lite, 'lite'), (three, '3d')):
                        response = page.request.get(self.url + edition + '/assignments/' + unit_id + '.json')
                        self.assertEqual(response.body(), data)
                        self.no_scroll(page)
                    evidence.append({'schemaVersion': version, 'unitId': unit_id,
                                     'questions': len(unit['questions']), 'identical_bytes': True})
        (OUT / 'cross-edition-json.json').write_text(json.dumps(evidence, indent=2))

    def test_lite_english_question_feedback_completion_and_mobile_controls(self):
        unit = fixture(2, 'S02')
        self.publish(unit)
        page = self.page('lite', hooks=True)
        self.load_lite(page, unit)
        self.english(page, unit)
        page.screenshot(path=str(OUT / 'lite-english-gameplay.png'))
        page.click('#panelToggle')
        self.assertIn('30 seconds per attempt', page.inner_text('#sidePanel'))
        self.english(page, unit)
        page.click('#panelClose')
        for width, height in ((1366, 768), (390, 844)):
            page.set_viewport_size({'width': width, 'height': height})
            self.no_scroll(page)
            self.english(page, unit)
        page.set_viewport_size({'width': 1366, 'height': 768})
        page.click('#modeToggle')
        self.assertIn('2D', page.inner_text('#modeToggle'))
        self.english(page, unit)
        page.screenshot(path=str(OUT / 'lite-english-driving.png'))
        page.click('#modeToggle')
        page.click('#mapToggle')
        self.assertIn('Close map', page.inner_text('#mapToggle'))
        page.evaluate('studentTest.tick(30001)')
        self.assertIn('used up', page.inner_text('#mapToggle'))
        page.click('#resetBtn')
        page.evaluate('studentTest.park(studentTest.state().current.stations[0])')
        page.locator('#maze').focus()
        page.keyboard.press('e')
        page.wait_for_selector('[data-answer]')
        wrong = next(label for label in 'ABCD'[:len(unit['questions'][0]['options'])]
                     if label not in unit['questions'][0]['correctOptions'])
        page.click(f'[data-answer="{wrong}"]')
        self.assertIn('Wrong answer', page.inner_text('#dialog'))
        self.assertEqual(page.evaluate('studentTest.state().remaining'), 30000)
        self.english(page, unit)
        page.click('#nextRound')
        for index, question in enumerate(unit['questions']):
            page.evaluate('i=>studentTest.park(studentTest.state().current.stations[i])', index)
            page.locator('#maze').focus()
            page.keyboard.press('e')
            page.wait_for_selector('[data-answer]')
            self.assertIn('choose one answer', page.inner_text('#dialog'))
            self.english(page, unit)
            page.click(f'[data-answer="{question["correctOptions"][-1]}"]')
            self.assertIn('Correct!', page.inner_text('#dialog'))
            self.english(page, unit)
            page.click('#continueMaze')
        page.evaluate('studentTest.park(studentTest.state().current.exit)')
        page.locator('#maze').focus()
        page.keyboard.press('e')
        page.wait_for_selector('#closeFinish')
        self.assertIn('Open Google Form', page.inner_text('#dialog'))
        self.english(page, unit)
        page.screenshot(path=str(OUT / 'lite-english-completion.png'))
        self.no_scroll(page)


if __name__ == '__main__':
    unittest.main(verbosity=2)
