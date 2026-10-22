"""Isolated, synthetic-only WebGL 2 functionality/evidence; no Intel performance claim."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
from io import BytesIO
import shutil
import subprocess
import tempfile
import sys
import threading
import time
import traceback
import unittest
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
from PIL import Image, ImageChops, ImageStat

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'test-results/3d-p1'


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


class ShowcaseBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        OUT.mkdir(parents=True, exist_ok=True)
        subprocess.run(['node','showcase3d/tests/write-route.mjs'],cwd=ROOT,check=True)
        # A nested URL proves deployment under a university subdirectory.
        subprocess.run(['node','showcase3d/scripts/build-baseline.mjs'],cwd=ROOT,check=True)
        cls.temp = tempfile.TemporaryDirectory()
        served = Path(cls.temp.name)/'nested/course'
        shutil.copytree(ROOT/'showcase3d/dist',served/'dist')
        shutil.copytree(OUT/'p0-runtime',served/'p0')
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=cls.temp.name))
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.url = f'http://127.0.0.1:{cls.server.server_port}/nested/course/dist/'
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
        cls.browser.close(); cls.pw.stop(); cls.server.shutdown(); cls.server.server_close(); cls.temp.cleanup()
        (OUT / 'browser-results.json').write_text(json.dumps(cls.results, indent=2))

    def setUp(self):
        self.contexts = []; self.pages = []; self.errors = []; self.external = []; self.logs = []
        self.started = time.monotonic()

    def new_page(self, width=960, height=700, dpr=1, video=False, fallback=False, clock=False, baseline=False):
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
        page.goto((self.url.replace('/dist/','/p0/') if baseline else self.url) + ('?testClock=1' if clock else ''))
        if not fallback:
            page.wait_for_function('window.showcase?.snapshot().ready', timeout=120000)
            page.select_option('#scale', '0.5')
            self.rendered(page)
        return page

    def rendered(self, page):
        page.bring_to_front()
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
        for maze, seed in [('21x15',20262031),('17x13',20263040),('13x9',20264049),('25x19',20261022)]:
            page.fill('#seed',str(seed))
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
        page = self.new_page(); page.click('[data-quality="Low"]'); page.select_option('#inspection', 'driving')
        start = self.snapshot(page)['pose']; page.locator('#view').focus()
        page.keyboard.down('w'); page.wait_for_timeout(1800); page.keyboard.up('w'); self.rendered(page)
        after = self.snapshot(page); self.assertNotEqual(after['pose'], start); self.assertTrue(after['cameraWalkable'])
        page.keyboard.down('d'); page.wait_for_timeout(800); page.keyboard.up('d'); self.rendered(page)
        self.assertNotEqual(self.snapshot(page)['pose']['yaw'], after['pose']['yaw'])
        page.keyboard.down('w'); page.wait_for_timeout(3500); page.keyboard.up('w'); self.rendered(page)
        self.assertTrue(self.snapshot(page)['cameraWalkable']); self.assertEqual(self.snapshot(page)['camera'][1], 1.65)
        page.mouse.move(400, 400); page.mouse.down(); page.mouse.move(480, 425, steps=8); page.mouse.up(); self.rendered(page)
        self.assertNotEqual(self.snapshot(page)['pose']['pitch'], 0)
        page.keyboard.press('r'); self.rendered(page); reset = self.snapshot(page)
        self.assertAlmostEqual(reset['pose']['x'], 4.2)
        page.click('#camera'); self.rendered(page); self.assertEqual(self.snapshot(page)['mode'], 'overview')
        self.assertGreater(self.snapshot(page)['camera'][1], 3.6)
        preserved = self.snapshot(page)['game']
        page.click('#camera'); self.rendered(page); self.assertEqual(self.snapshot(page)['mode'], 'first-person')
        self.assertEqual(self.snapshot(page)['game'], preserved)

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
        before = Image.open(BytesIO(page.locator('#view').screenshot())).convert('RGB')
        page.evaluate("window.testLoss= document.querySelector('canvas').getContext('webgl2').getExtension('WEBGL_lose_context'); window.testLoss.loseContext()")
        page.wait_for_function('window.showcase.snapshot().contextLost')
        self.assertIn('context lost', page.locator('#message').inner_text())
        page.wait_for_timeout(500); page.evaluate('window.testLoss.restoreContext()')
        page.wait_for_function('window.showcase.snapshot().restoredContexts === 1', timeout=120000)
        self.rendered(page); self.assertTrue(self.snapshot(page)['ready']); self.assertEqual(page.locator('#message').inner_text(), '')
        after = Image.open(BytesIO(page.locator('#view').screenshot())).convert('RGB')
        # Central floor/wall crop excludes changing diagnostic text and controls.
        w, h = before.size; crop = (int(w * 0.42), int(h * 0.55), int(w * 0.62), int(h * 0.75))
        delta = ImageStat.Stat(ImageChops.difference(before.crop(crop), after.crop(crop))).rms
        self.assertLess(max(delta), 3, 'Restored environment/shadows changed the static scene')
        (OUT / 'context-restore-pixel-delta.json').write_text(json.dumps({'rgb_rms': delta, 'crop': crop}))

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
        page.select_option('#inspection', 'driving'); self.rendered(page)
        # Actual keyboard navigation, not generated frames or screenshots posing as video.
        before = self.snapshot(page)['pose']; page.locator('#view').focus(); page.keyboard.down('w'); page.wait_for_timeout(1600); page.keyboard.up('w')
        page.keyboard.down('a'); page.wait_for_timeout(900); page.keyboard.up('a')
        page.keyboard.down('w'); page.wait_for_timeout(2200); page.keyboard.up('w')
        page.click('[data-quality="Medium"]'); self.rendered(page)
        after = self.snapshot(page)['pose']; self.assertNotEqual(before, after)
        (OUT / 'navigation-evidence.json').write_text(json.dumps({'before': before, 'after': after,
            'video': Path(page.video.path()).name,
            'recording': 'Real Chromium keyboard navigation, software WebGL 2; footage is not an Intel performance benchmark.'}, indent=2))
        page.screenshot(path=str(OUT / 'navigation-final.png'))


    def prepare_route(self, page):
        page.click('[data-quality="Low"]'); page.select_option('#scale', '0.5')
        page.fill('#seed', '20264049'); page.select_option('#maze', '13x9')
        page.locator('#view').focus(); self.rendered(page)
        return json.loads((OUT/'control-route.json').read_text())

    def key_hold(self, page, held, keys, seconds):
        keys = set(keys)
        for key in held-keys: page.keyboard.up(key)
        for key in keys-held: page.keyboard.down(key)
        state = page.evaluate('seconds => window.showcase.advanceSimulation(seconds)', seconds)
        self.assertTrue(state['vehicleClear'])
        self.assertAlmostEqual(state['pose']['yaw'], state['game']['vehicle']['heading'])
        self.assertAlmostEqual(state['camera'][0], state['game']['vehicle']['x']*.7/14)
        self.assertAlmostEqual(state['camera'][2], state['game']['vehicle']['y']*.7/14)
        return keys, state

    def test_10_complete_control_driven_route_and_checkpoint_feedback(self):
        page = self.new_page(1280,800,video=True,clock=True)
        page.locator('#diagnostics summary').click()
        plan = self.prepare_route(page); held=set(); activated=[]; moving_rejected=False
        original=self.snapshot(page); geometry_rebuilds=original['rebuilds']
        page.keyboard.press('e'); self.assertTrue(page.locator('#dialog-overlay').is_hidden())
        page.select_option('#inspection','finish'); self.rendered(page)
        page.screenshot(path=str(OUT/'exit-locked.png')); page.click('#camera')
        page.screenshot(path=str(OUT/'driving-hud-laptop.png'))
        for index,step in enumerate(plan['steps']):
            if step['kind']=='drive':
                held,state=self.key_hold(page,held,step['keys'],step['seconds'])
                if not moving_rejected and state['game']['vehicle']['speed']>25 and page.locator('#interact').is_visible():
                    before=state['game']['completed']; page.keyboard.press('e')
                    self.assertTrue(page.locator('#dialog-overlay').is_hidden())
                    self.assertEqual(self.snapshot(page)['game']['completed'],before);moving_rejected=True
                    page.screenshot(path=str(OUT/'acceleration-before-braking.png'))
                if any(key in step['keys'] for key in ('a','d')) and index<12:
                    page.screenshot(path=str(OUT/'steering-near-wall.png'))
            else:
                for key in held: page.keyboard.up(key)
                held=set(); state=self.snapshot(page)
                for key in ('x','y','heading','distance'):
                    self.assertAlmostEqual(state['game']['vehicle'][key],step['expected'][key],places=7)
                self.assertLessEqual(abs(state['game']['vehicle']['speed']),25)
                self.assertIn(step['id'],page.locator('#nearby').inner_text())
                if step['id']=='Q1':
                    page.screenshot(path=str(OUT/'checkpoint-within-range.png'))
                    page.click('[data-quality="High"]');page.select_option('#scale','auto')
                    page.select_option('#inspection','checkpoint');self.rendered(page)
                    page.screenshot(path=str(OUT/'checkpoint-before.png'));page.click('#camera')
                if step['id']=='EXIT':
                    page.select_option('#inspection','finish');self.rendered(page)
                    page.screenshot(path=str(OUT/'exit-unlocked.png'));page.click('#camera')
                page.keyboard.press('e');page.wait_for_selector('#dialog-overlay:not([hidden])')
                activated.append(step['id'])
                page.screenshot(path=str(OUT/f'activated-{step["id"]}.png'))
                self.assertEqual(self.snapshot(page)['rebuilds'],geometry_rebuilds,'Progress rebuilt static geometry')
                if step['id']=='EXIT':
                    self.assertTrue(self.snapshot(page)['game']['finished'])
                    self.assertEqual(page.locator('#dialog-close').inner_text(),'Close completion')
                    self.assertIn('Reset',page.locator('#interaction-hint').inner_text())
                    break
                page.click('#dialog-close')
                if step['id']=='Q1':
                    page.select_option('#inspection','checkpoint');self.rendered(page)
                    page.screenshot(path=str(OUT/'checkpoint-after.png'));page.click('#camera')
                    before=self.snapshot(page)['game']['completed']
                    page.keyboard.press('e');self.assertTrue(page.locator('#dialog-overlay').is_hidden())
                    self.assertEqual(self.snapshot(page)['game']['completed'],before)
                    page.click('[data-quality="Low"]');page.select_option('#scale','0.5')
        self.assertEqual(set(activated),{'Q1','Q2','Q3','Q4','Q5','EXIT'})
        self.assertTrue(moving_rejected,'Accepted route must also exercise the high-speed interaction gate')
        final=self.snapshot(page);self.assertEqual(final['game']['activations'],5)
        self.assertTrue(all(final['game']['completed']))
        self.assertGreater(final['game']['vehicle']['distance'],20000)
        (OUT/'control-completion.json').write_text(json.dumps({'plan':plan,'final':final,'activated':activated,
            'video':Path(page.video.path()).name,'clock':'Explicit accelerated simulation clock; every move used real keyboard holds, no position setters.'},indent=2))
        # Reset also cancels the still-open completion dialog.
        page.keyboard.press('r');self.assertTrue(page.locator('#dialog-overlay').is_hidden())
        self.assertEqual(self.snapshot(page)['game']['completed'],[False]*5)
        self.assertFalse(self.snapshot(page)['game']['finished'])

    def test_11_reset_blur_new_seeds_modes_and_benchmark_preserve_state(self):
        page=self.new_page(clock=True);plan=self.prepare_route(page)
        page.keyboard.down('w');page.evaluate('window.showcase.advanceSimulation(1)')
        self.assertGreater(self.snapshot(page)['game']['vehicle']['speed'],0)
        page.evaluate('window.dispatchEvent(new Event("blur"))')
        paused=self.snapshot(page);self.assertEqual(paused['heldKeys'],[]);self.assertEqual(paused['game']['vehicle']['speed'],0)
        page.evaluate('window.showcase.advanceSimulation(1)');self.assertEqual(self.snapshot(page)['game']['vehicle'],paused['game']['vehicle'])
        page.keyboard.up('w');page.keyboard.down('w');page.evaluate('window.showcase.advanceSimulation(.5)');page.keyboard.press('r');page.keyboard.up('w')
        reset=self.snapshot(page);self.assertEqual(reset['heldKeys'],[]);self.assertEqual(reset['game']['vehicle']['speed'],0)
        self.assertAlmostEqual(reset['game']['vehicle']['x'],84)
        held=set()
        for step in plan['steps']:
            if step['kind']=='drive':held,_=self.key_hold(page,held,step['keys'],step['seconds'])
            else:
                for key in held:page.keyboard.up(key)
                page.keyboard.press('e');page.wait_for_selector('#dialog-overlay:not([hidden])');page.click('#dialog-close');break
        saved=self.snapshot(page)['game']
        page.click('#camera');page.locator('#view').focus();page.keyboard.down('w');page.evaluate('window.showcase.advanceSimulation(3)');page.keyboard.up('w')
        self.assertEqual(self.snapshot(page)['game'],saved)
        page.click('#camera');self.assertEqual(self.snapshot(page)['game'],saved)
        page.select_option('#inspection','four-way');page.keyboard.press('e');self.assertTrue(page.locator('#dialog-overlay').is_hidden())
        self.assertEqual(self.snapshot(page)['game'],saved);page.click('#camera')
        page.evaluate('window.showcase.runBenchmark({warmupMs:400,durationMs:1200})')
        self.assertEqual(self.snapshot(page)['game'],saved)
        page.click('[data-quality="High"]');self.assertEqual(self.snapshot(page)['game'],saved)
        page.click('[data-quality="Low"]')
        previous=self.snapshot(page);page.fill('#seed','invalid');page.click('#generate')
        self.assertEqual(self.snapshot(page)['game'],previous['game'])
        page.fill('#seed','');page.click('#generate');fresh=self.snapshot(page)
        self.assertNotEqual(fresh['maze']['seed'],previous['maze']['seed']);self.assertEqual(fresh['game']['completed'],[False]*5)
        self.assertEqual(fresh['heldKeys'],[]);self.assertIsNone(fresh['game']['interaction'])
        for seed in ['0','1','4294967295']:
            page.fill('#seed',seed);page.click('#generate');first=self.snapshot(page)
            page.click('#generate');second=self.snapshot(page)
            self.assertEqual(first['maze'],second['maze']);self.assertEqual(first['rebuilds'],second['rebuilds'])

    def test_12_approved_p0_wall_floor_and_lighting_visual_parity(self):
        current=self.new_page();baseline=self.new_page(baseline=True)
        style='''header,nav,footer,main>:not(canvas){display:none!important}main{position:fixed!important;inset:0!important;width:960px!important;height:520px!important;flex:none!important}canvas{width:960px!important;height:520px!important}'''
        for page in (current,baseline):page.add_style_tag(content=style)
        comparisons=[]
        for quality in ['Medium','High']:
            for scene in ['straight','wall','floor']:
                images=[]
                for name,page in [('p0',baseline),('p1',current)]:
                    page.bring_to_front()
                    page.locator(f'[data-quality="{quality}"]').evaluate('(b)=>b.click()')
                    page.locator('#scale').evaluate('(s)=>{s.value="auto";s.dispatchEvent(new Event("change"))}')
                    page.locator('#inspection').evaluate('(s,value)=>{s.value=value;s.dispatchEvent(new Event("change"))}',scene)
                    self.rendered(page)
                    data=page.locator('#view').screenshot(path=str(OUT/f'parity-{scene}-{quality.lower()}-{name}.png'))
                    images.append(Image.open(BytesIO(data)).convert('RGB'))
                w,h=images[0].size;crop=(int(w*.1),int(h*.2),int(w*.38),int(h*.8))
                delta=ImageStat.Stat(ImageChops.difference(images[0].crop(crop),images[1].crop(crop))).rms
                comparisons.append({'quality':quality,'scene':scene,'crop':crop,'rgb_rms':delta})
                self.assertLess(max(delta),.5,f'Approved static P0 art changed: {quality}/{scene}')
        (OUT/'p0-visual-parity.json').write_text(json.dumps(comparisons,indent=2))


if __name__ == '__main__':
    unittest.main(verbosity=2)
