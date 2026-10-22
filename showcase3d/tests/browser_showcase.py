"""Isolated, synthetic-only WebGL 2 functionality/evidence; no Intel performance claim."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import shutil
import sys
import threading
import time
import traceback
import unittest
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'test-results/3d-p0'


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


class ShowcaseBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        OUT.mkdir(parents=True, exist_ok=True)
        # A nested URL proves deployment under a university subdirectory.
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(ROOT / 'showcase3d')))
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.url = f'http://127.0.0.1:{cls.server.server_port}/dist/'
        cls.pw = sync_playwright().start()
        preferred = os.environ.get('EMI_3D_BROWSER_PATH') or cls.pw.chromium.executable_path
        executable = preferred if Path(preferred).is_file() else shutil.which('chromium') or shutil.which('chromium-browser')
        if not executable:
            raise RuntimeError('Install Playwright Chromium; a WebGL 2 test may not silently skip')
        cls.browser = cls.pw.chromium.launch(executable_path=executable, args=[
            '--no-sandbox', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'])
        (OUT / 'browser-version.json').write_text(json.dumps({'browser': cls.browser.version,
            'renderer_policy': 'Cloud SwiftShader software rendering; functional tests only',
            'executable': executable}, indent=2))
        cls.results = []

    @classmethod
    def tearDownClass(cls):
        cls.browser.close(); cls.pw.stop(); cls.server.shutdown(); cls.server.server_close()
        (OUT / 'browser-results.json').write_text(json.dumps(cls.results, indent=2))

    def setUp(self):
        self.contexts = []; self.pages = []; self.errors = []; self.external = []; self.logs = []
        self.started = time.monotonic()

    def new_page(self, width=960, height=700, dpr=1, video=False, fallback=False):
        args = {'viewport': {'width': width, 'height': height}, 'device_scale_factor': dpr,
                'accept_downloads': True}
        if video:
            args.update(record_video_dir=str(OUT / 'video'), record_video_size={'width': width, 'height': height})
        context = self.browser.new_context(**args)
        context.tracing.start(screenshots=True, snapshots=True, sources=True)
        self.contexts.append(context)
        page = context.new_page(); self.pages.append(page)
        page.on('pageerror', lambda error: self.errors.append(str(error)))
        page.on('console', lambda message: self.logs.append({'type': message.type, 'text': message.text}))
        def route(request):
            host = urlparse(request.request.url).hostname
            if host and host != '127.0.0.1':
                self.external.append(request.request.url); request.abort()
            else:
                request.continue_()
        context.route('**/*', route)
        if fallback:
            page.add_init_script("""const get=HTMLCanvasElement.prototype.getContext;
                HTMLCanvasElement.prototype.getContext=function(type,...args){return type==='webgl2'?null:get.call(this,type,...args)};""")
        page.goto(self.url)
        if not fallback:
            page.wait_for_function('window.showcase?.snapshot().ready', timeout=120000)
            page.select_option('#scale', '0.5')
            self.rendered(page)
        return page

    def rendered(self, page):
        # Wait for an actual presentation after UI changes, even on slow software rendering.
        page.evaluate('() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))')

    def snapshot(self, page):
        return page.evaluate('window.showcase.snapshot()')

    def tearDown(self):
        failure = any(test is self and error for test, error in self._outcome.result.failures + self._outcome.result.errors)
        for index, page in enumerate(self.pages):
            try:
                page.screenshot(path=str(OUT / f'{self._testMethodName}-{index}-final.png'), timeout=60000)
                if page.evaluate('Boolean(window.showcase)'):
                    (OUT / f'{self._testMethodName}-{index}.json').write_text(json.dumps(self.snapshot(page), indent=2))
            except Exception as error:
                self.logs.append({'capture_error': str(error)})
        for index, context in enumerate(self.contexts):
            context.tracing.stop(path=str(OUT / f'{self._testMethodName}-{index}-trace.zip')); context.close()
        (OUT / f'{self._testMethodName}.log').write_text(json.dumps({'page_errors': self.errors,
            'external_requests': self.external, 'console': self.logs}, indent=2))
        self.results.append({'test': self._testMethodName, 'passed': not failure and not self.errors and not self.external and not any(m.get('type') == 'error' for m in self.logs),
                             'seconds': round(time.monotonic() - self.started, 2)})
        self.assertEqual(self.errors, [], 'Uncaught JavaScript errors')
        self.assertEqual(self.external, [], 'External runtime requests')
        self.assertEqual([m for m in self.logs if m.get('type') == 'error'], [], 'Browser console errors')

    def test_01_local_bundle_relative_paths_webgl2_and_diagnostics(self):
        page = self.new_page(); s = self.snapshot(page)
        self.assertTrue(s['webgl2']); self.assertEqual(s['three'], '180')
        self.assertGreater(s['render']['triangles'], 1000); self.assertLess(s['render']['calls'], 40)
        self.assertEqual(s['maze']['id'], '25x19'); self.assertTrue(s['cameraWalkable'])
        self.assertIn('WebGL 2', s['metrics']['identity']['version'])
        self.assertIn('Software', s['metrics']['identity']['classification'])
        self.assertGreater(s['coldStart']['readyMs'], s['coldStart']['moduleReadyMs'])
        self.assertGreater(s['coldStart']['shaderPreparationMs'], 0)
        self.assertEqual(page.evaluate('document.documentElement.scrollHeight > innerHeight'), False)
        self.assertEqual(page.evaluate('document.documentElement.scrollWidth > innerWidth'), False)

    def test_02_presets_all_sizes_disposal_resolution_and_topology(self):
        page = self.new_page(); original = self.snapshot(page)['maze']['topologyHash']; counts = {}
        for _ in range(2):
            for quality in ['Low', 'High', 'Medium']:
                page.click(f'[data-quality="{quality}"]'); self.rendered(page); s = self.snapshot(page)
                self.assertEqual(s['maze']['topologyHash'], original)
                if quality in counts:
                    self.assertEqual(s['render']['textures'], counts[quality]['textures'])
                    self.assertEqual(s['render']['geometries'], counts[quality]['geometries'])
                counts[quality] = s['render']
                self.assertEqual(s['quality'], quality)
                self.assertLessEqual(s['render']['textures'], 14)
                self.assertLessEqual(s['render']['geometries'], 24)
        for maze in ['21x15', '17x13', '13x9', '25x19']:
            page.select_option('#maze', maze); self.rendered(page); s = self.snapshot(page)
            self.assertEqual(s['maze']['id'], maze); self.assertTrue(s['cameraWalkable'])
            self.assertLessEqual(s['render']['geometries'], 24)
            self.assertLessEqual(s['render']['textures'], 14)
        self.assertEqual(self.snapshot(page)['maze']['topologyHash'], original)
        page.select_option('#scale', '1.25'); self.rendered(page)
        s = self.snapshot(page); self.assertLessEqual(s['buffer']['width'], 1600)
        page.select_option('#fps', '60'); self.assertEqual(self.snapshot(page)['targetFps'], 60)
        self.assertEqual(s['disposedScenes'], s['rebuilds'] - 1)

    def test_03_keyboard_mouse_collision_and_reset(self):
        page = self.new_page(); page.click('[data-quality="Low"]'); page.select_option('#inspection', 'straight')
        start = self.snapshot(page)['pose']; page.locator('#view').focus()
        page.keyboard.down('w'); page.wait_for_timeout(1800); page.keyboard.up('w'); self.rendered(page)
        after = self.snapshot(page); self.assertNotEqual(after['pose'], start); self.assertTrue(after['cameraWalkable'])
        page.keyboard.down('d'); page.wait_for_timeout(800); page.keyboard.up('d'); self.rendered(page)
        self.assertNotEqual(self.snapshot(page)['pose']['yaw'], after['pose']['yaw'])
        page.keyboard.down('w'); page.wait_for_timeout(3500); page.keyboard.up('w'); self.rendered(page)
        self.assertTrue(self.snapshot(page)['cameraWalkable']); self.assertEqual(self.snapshot(page)['camera'][1], 1.65)
        page.mouse.move(400, 400); page.mouse.down(); page.mouse.move(480, 425, steps=8); page.mouse.up()
        self.assertNotEqual(self.snapshot(page)['pose']['pitch'], 0)
        page.keyboard.press('r'); self.rendered(page); reset = self.snapshot(page)
        self.assertEqual(reset['pose']['x'], 4.199999999999999)
        page.click('#camera'); self.rendered(page); self.assertEqual(self.snapshot(page)['mode'], 'overview')
        self.assertGreater(self.snapshot(page)['camera'][1], 3.6)
        page.click('#camera'); self.rendered(page); self.assertEqual(self.snapshot(page)['mode'], 'first-person')

    def test_04_laptop_150_percent_projector_resize_and_fullscreen(self):
        page = self.new_page(1280, 800, 1.5)
        for quality, cap in [('Low', 1280), ('Medium', 1600), ('High', 1920)]:
            page.click(f'[data-quality="{quality}"]'); page.select_option('#scale', 'auto'); self.rendered(page)
            s = self.snapshot(page); self.assertEqual(s['devicePixelRatio'], 1.5); self.assertEqual(s['rendererPixelRatio'], 1)
            self.assertLessEqual(s['buffer']['width'], cap)
        page.click('#fullscreen'); page.wait_for_function('Boolean(document.fullscreenElement)'); self.rendered(page)
        self.assertFalse(page.evaluate('document.documentElement.scrollHeight > innerHeight'))
        page.click('#fullscreen'); page.wait_for_function('!document.fullscreenElement')
        page.set_viewport_size({'width': 1920, 'height': 1080}); self.rendered(page)
        self.assertLessEqual(self.snapshot(page)['buffer']['width'], 1920)
        self.assertFalse(page.evaluate('document.documentElement.scrollWidth > innerWidth'))
        page.screenshot(path=str(OUT / 'projector-1920x1080.png'))

    def test_05_context_loss_and_restore(self):
        page = self.new_page()
        page.evaluate("window.testLoss= document.querySelector('canvas').getContext('webgl2').getExtension('WEBGL_lose_context'); window.testLoss.loseContext()")
        page.wait_for_function('window.showcase.snapshot().contextLost')
        self.assertIn('context lost', page.locator('#message').inner_text())
        page.wait_for_timeout(500); page.evaluate('window.testLoss.restoreContext()')
        page.wait_for_function('window.showcase.snapshot().restoredContexts === 1', timeout=120000)
        self.rendered(page); self.assertTrue(self.snapshot(page)['ready']); self.assertEqual(page.locator('#message').inner_text(), '')

    def test_06_webgl2_unavailable_clear_fallback(self):
        page = self.new_page(fallback=True)
        page.wait_for_function('document.querySelector("#message").classList.contains("error")')
        self.assertIn('WebGL 2 could not start', page.locator('#message').inner_text())
        self.assertIn('Lite edition', page.locator('#message').inner_text())
        self.assertTrue(page.locator('#benchmark').is_disabled())

    def test_07_six_scenario_benchmark_and_local_json_export(self):
        page = self.new_page(); page.click('[data-quality="Low"]')
        results = page.evaluate('window.showcase.runBenchmark({warmupMs:400,durationMs:1200})')
        self.assertEqual(len(results), 6); self.assertEqual(results[0]['report']['maze']['id'], '25x19')
        self.assertEqual(results[1]['report']['maze']['id'], '13x9')
        for result in results:
            self.assertGreater(result['report']['metrics']['samples'], 0)
            self.assertIn('coldStart', result['report']); self.assertIn('gpuExecutionMs', result['report']['metrics'])
        with page.expect_download() as download:
            page.click('#export')
        download.value.save_as(OUT / 'cloud-benchmark.json')
        saved = json.loads((OUT / 'cloud-benchmark.json').read_text())
        self.assertEqual(len(saved['benchmarkResults']), 6); self.assertIn('Software', saved['metrics']['identity']['classification'])

    def test_08_visual_evidence_and_matched_presets(self):
        page = self.new_page(1280, 800); page.locator('#diagnostics summary').click()
        page.select_option('#scale', 'auto')
        for view in ['start', 'straight', 't-junction', 'four-way', 'wall', 'floor', 'checkpoint', 'finish']:
            page.select_option('#inspection', view); self.rendered(page)
            page.screenshot(path=str(OUT / f'{view}.png'))
        for quality in ['Low', 'Medium', 'High']:
            page.select_option('#inspection', 'four-way'); page.click(f'[data-quality="{quality}"]')
            self.rendered(page); page.screenshot(path=str(OUT / f'matched-{quality.lower()}.png'))
            (OUT / f'matched-{quality.lower()}.json').write_text(json.dumps(self.snapshot(page), indent=2))
        page.click('#camera'); self.rendered(page); page.screenshot(path=str(OUT / 'full-maze-overview.png'))
        page.select_option('#inspection', 'checkpoint'); self.rendered(page)
        page.screenshot(path=str(OUT / 'showcase-composition.png'))

    def test_09_real_browser_navigation_recording(self):
        page = self.new_page(1280, 800, video=True); page.locator('#diagnostics summary').click()
        page.click('[data-quality="Low"]'); page.select_option('#scale', '0.5')
        page.select_option('#inspection', 't-junction'); self.rendered(page)
        # Actual keyboard navigation, not generated frames or screenshots posing as video.
        before = self.snapshot(page)['pose']; page.keyboard.down('w'); page.wait_for_timeout(1600); page.keyboard.up('w')
        page.keyboard.down('a'); page.wait_for_timeout(900); page.keyboard.up('a')
        page.keyboard.down('w'); page.wait_for_timeout(2200); page.keyboard.up('w')
        page.click('[data-quality="Medium"]'); self.rendered(page)
        after = self.snapshot(page)['pose']; self.assertNotEqual(before, after)
        (OUT / 'navigation-evidence.json').write_text(json.dumps({'before': before, 'after': after,
            'video': Path(page.video.path()).name,
            'recording': 'Real Chromium keyboard navigation, software WebGL 2; footage is not an Intel performance benchmark.'}, indent=2))
        page.screenshot(path=str(OUT / 'navigation-final.png'))


if __name__ == '__main__':
    unittest.main(verbosity=2)
