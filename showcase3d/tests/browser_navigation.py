"""P1.1 synthetic dual-view acceptance; test clock changes time, never vehicle position."""
from functools import partial
from http.server import ThreadingHTTPServer
import ctypes
import ctypes.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from playwright.sync_api import sync_playwright
import browser_showcase as harness

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'test-results/3d-p1.1'
harness.OUT = OUT  # Reuse capture/log helpers in this separate test process only.


class NavigationBrowserTests(unittest.TestCase):
    setUp = harness.ShowcaseBrowserTests.setUp
    tearDown = harness.ShowcaseBrowserTests.tearDown
    tearDownClass = classmethod(harness.ShowcaseBrowserTests.tearDownClass.__func__)
    new_page = harness.ShowcaseBrowserTests.new_page
    rendered = harness.ShowcaseBrowserTests.rendered
    snapshot = harness.ShowcaseBrowserTests.snapshot
    prepare_route = harness.ShowcaseBrowserTests.prepare_route
    key_hold = harness.ShowcaseBrowserTests.key_hold

    @classmethod
    def setUpClass(cls):
        OUT.mkdir(parents=True,exist_ok=True)
        subprocess.run(['node','showcase3d/tests/write-route.mjs'],cwd=ROOT,check=True)
        shutil.copyfile(ROOT/'test-results/3d-p1/control-route.json',OUT/'control-route.json')
        cls.temp=tempfile.TemporaryDirectory()
        served=Path(cls.temp.name)/'nested/course/dist'
        shutil.copytree(ROOT/'showcase3d/dist',served)
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),partial(harness.QuietHandler,directory=cls.temp.name))
        threading.Thread(target=cls.server.serve_forever,daemon=True).start()
        cls.url=f'http://127.0.0.1:{cls.server.server_port}/nested/course/dist/'
        cls.pw=sync_playwright().start()
        preferred=os.environ.get('EMI_3D_BROWSER_PATH') or cls.pw.chromium.executable_path
        executable=preferred if Path(preferred).is_file() else shutil.which('chromium') or shutil.which('chromium-browser')
        if not executable:raise RuntimeError('Install Chromium; navigation regressions may not silently skip')
        # A real window/tab activation model is required for the focus-budget test.
        # Linux CI supplies Xvfb; the original P1 suite remains headless/unchanged.
        cls.browser=cls.pw.chromium.launch(headless=False,executable_path=executable,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
        (OUT/'browser-version.json').write_text(json.dumps({'browser':cls.browser.version,'executable':executable,
            'renderer_policy':'Windowed Chromium under virtual X display; SwiftShader, no physical-device claim'},indent=2))
        cls.results=[]

    def capture(self,page,name):
        self.rendered(page)
        page.screenshot(path=str(OUT/f'{name}.png'))
        (OUT/f'{name}.json').write_text(json.dumps(self.snapshot(page),indent=2))

    def switch(self,page):
        before=self.snapshot(page)
        page.keyboard.press('v');self.rendered(page)
        after=self.snapshot(page)
        for key in ('x','y','heading','distance','walk'):
            self.assertEqual(after['game']['vehicle'][key],before['game']['vehicle'][key])
        self.assertEqual(after['game']['completed'],before['game']['completed'])
        self.assertEqual(after['game']['activations'],before['game']['activations'])
        self.assertEqual(after['maze'],before['maze']);self.assertEqual(after['rebuilds'],before['rebuilds'])
        self.assertEqual(after['game']['vehicle']['speed'],0);self.assertEqual(after['heldKeys'],[])
        self.assertNotEqual(after['drivingView'],before['drivingView'])
        return after

    def test_01_full_keyboard_route_3d_2d_q1_and_shared_exit(self):
        page=self.new_page(1280,800,1.5,video=True,clock=True)
        page.locator('#diagnostics summary').click()
        plan=self.prepare_route(page);held=set();activated=[];switched=False
        for index,step in enumerate(plan['steps']):
            if step['kind']=='drive':
                held,state=self.key_hold(page,held,step['keys'],step['seconds'])
                if index==3:  # Actual stationary turn at the first checkpoint/intersection.
                    for key in held:page.keyboard.up(key)
                    held=set();self.capture(page,'same-position-3d')
                    state=self.switch(page);self.assertEqual(state['drivingView'],'2d');switched=True
                    self.capture(page,'same-position-2d')
            else:
                for key in held:page.keyboard.up(key)
                held=set();state=self.snapshot(page)
                for key in ('x','y','heading','distance'):
                    self.assertAlmostEqual(state['game']['vehicle'][key],step['expected'][key],places=7)
                self.assertLessEqual(abs(state['game']['vehicle']['speed']),25)
                if step['id']=='Q1':
                    self.assertTrue(switched);self.assertEqual(state['drivingView'],'2d')
                    self.capture(page,'q1-incomplete-2d')
                if step['id']=='EXIT':
                    page.keyboard.press('m');self.capture(page,'full-map-exit-unlocked')
                    self.assertTrue(self.snapshot(page)['map2d']['markers'][-1]['unlocked']);page.keyboard.press('m')
                page.keyboard.press('e');page.wait_for_selector('#dialog-overlay:not([hidden])')
                before=self.snapshot(page);page.keyboard.press('v');page.keyboard.press('m')
                self.assertEqual(self.snapshot(page)['game'],before['game'],'Navigation discarded an interaction')
                activated.append(step['id'])
                if step['id']=='EXIT':break
                page.click('#dialog-close')
                if step['id']=='Q1':
                    self.capture(page,'q1-completed-2d')
                    marker=self.snapshot(page)['map2d']['markers'][0];self.assertTrue(marker['completed'])
                    page.keyboard.press('e');self.assertTrue(page.locator('#dialog-overlay').is_hidden())
                    self.assertEqual(self.snapshot(page)['game']['activations'],2)
                    page.keyboard.press('m');self.capture(page,'full-map-remaining-locked')
                    full=self.snapshot(page);self.assertEqual(len(full['map2d']['markers']),6)
                    self.assertFalse(full['map2d']['markers'][-1]['unlocked'])
                    page.keyboard.down('w');page.evaluate('window.showcase.advanceSimulation(2)');page.keyboard.up('w')
                    self.assertEqual(self.snapshot(page)['game']['vehicle'],full['game']['vehicle'])
                    page.keyboard.press('m');self.switch(page);self.capture(page,'returned-3d-q1-complete')
        self.assertEqual(set(activated),{'Q1','Q2','Q3','Q4','Q5','EXIT'})
        final=self.snapshot(page);self.assertEqual(final['game']['activations'],5);self.assertTrue(final['game']['finished'])
        self.capture(page,'dual-view-demonstration-complete')
        (OUT/'dual-view-route.json').write_text(json.dumps({'final':final,'activated':activated,'plan':plan,
            'video':Path(page.video.path()).name,'clock':'Accelerated simulation; real keyboard holds and V/M/E, no position setter'},indent=2))

    def test_02_identical_physics_and_resource_stability(self):
        page=self.new_page(clock=True);self.prepare_route(page)
        controls=[(['w'],1.2),(['s'],.6),(['d'],.35),(['w'],1.3),(['a','w'],.7),(['s'],.5),([],1)]
        trajectories=[]
        for presentation in ['3d','2d']:
            page.keyboard.press('r')
            if self.snapshot(page)['drivingView']!=presentation:self.switch(page)
            held=set();trajectory=[]
            for keys,seconds in controls:
                held,state=self.key_hold(page,held,keys,seconds);trajectory.append(state['game']['vehicle'])
            for key in held:page.keyboard.up(key)
            trajectories.append(trajectory)
        self.assertEqual(trajectories[0],trajectories[1])
        page.keyboard.down('w');page.evaluate('window.showcase.advanceSimulation(.7)')
        state=self.switch(page);page.keyboard.up('w')
        self.assertGreater(state['game']['vehicle']['distance'],0)
        saved=self.snapshot(page);self.switch(page);two=self.snapshot(page)
        page.wait_for_timeout(350);self.assertEqual(self.snapshot(page)['webglFrames'],two['webglFrames'])
        for _ in range(10):self.switch(page);self.switch(page)
        after=self.snapshot(page)
        self.assertEqual(after['map2d']['cacheBuilds'],two['map2d']['cacheBuilds'])
        self.assertEqual(after['rebuilds'],saved['rebuilds']);self.assertEqual(after['disposedScenes'],saved['disposedScenes'])
        for key in ('geometries','textures'):self.assertEqual(after['render'][key],saved['render'][key])
        (OUT/'dual-view-performance.json').write_text(json.dumps({'before':saved,'after':after,
            'trajectories_identical':True,'scope':'Software functional/resource observations; no Intel FPS claim'},indent=2))

    def test_03_cumulative_visible_map_budget_and_exhaustion(self):
        page=self.new_page(clock=True);page.locator('#view').focus()
        page.keyboard.press('m');page.wait_for_timeout(1100);page.keyboard.press('m')
        closed=self.snapshot(page)['game']['map']['remainingMs'];self.assertGreater(closed,26000);self.assertLess(closed,29500)
        page.wait_for_timeout(500);self.assertEqual(self.snapshot(page)['game']['map']['remainingMs'],closed)
        page.keyboard.press('m');page.wait_for_timeout(350)
        # Emulate the browser visibility event, without adding any production test setter.
        page.evaluate("Object.defineProperty(document,'hidden',{configurable:true,get:()=>true});document.dispatchEvent(new Event('visibilitychange'))")
        hidden=self.snapshot(page);page.wait_for_timeout(1100)
        self.assertEqual(self.snapshot(page)['game']['map'],hidden['game']['map'])
        page.evaluate("delete document.hidden;document.dispatchEvent(new Event('visibilitychange'))")
        page.wait_for_timeout(350)
        background=page.context.new_page()
        # Playwright forces every page to report focus by default, even windowed.
        # Disable that protocol emulation on both tabs and exercise native activation.
        for tab in (page,background):
            page.context.new_cdp_session(tab).send('Emulation.setFocusEmulationEnabled',{'enabled':False})
        page.bring_to_front();background.bring_to_front()
        page.wait_for_function('!document.hasFocus()',timeout=5000)
        unfocused=self.snapshot(page)['game']['map']['remainingMs'];page.wait_for_timeout(1000)
        self.assertEqual(self.snapshot(page)['game']['map']['remainingMs'],unfocused)
        page.bring_to_front();background.close();page.wait_for_timeout(350)
        page.keyboard.press('m');remaining=self.snapshot(page)['game']['map']['remainingMs']
        self.assertLess(remaining,closed);self.assertGreater(remaining,0)
        self.switch(page);self.assertEqual(self.snapshot(page)['game']['map']['remainingMs'],remaining)
        page.keyboard.press('m');page.wait_for_function('window.showcase.snapshot().game.map.remainingMs===0',timeout=40000)
        expired=self.snapshot(page);self.assertFalse(expired['game']['map']['open']);self.assertEqual(expired['drivingView'],'2d')
        page.keyboard.press('m');self.assertFalse(self.snapshot(page)['game']['map']['open'])
        self.assertTrue(page.locator('#toggle-map').is_disabled());page.keyboard.down('w')
        page.evaluate('window.showcase.advanceSimulation(1)');page.keyboard.up('w')
        self.assertNotEqual(self.snapshot(page)['game']['vehicle'],expired['game']['vehicle'])
        self.capture(page,'local-2d-after-map-exhausted')
        page.keyboard.press('r');self.assertEqual(self.snapshot(page)['game']['map'],{'remainingMs':30000,'open':False})
        (OUT/'map-timer-evidence.json').write_text(json.dumps({'closed':closed,'before_hidden':hidden['game']['map'],
            'unfocused':unfocused,'reopened':remaining,'expired':expired['game']['map'],
            'visibility':'DOM hidden-event emulation plus native tab activation with Playwright focus emulation disabled; actual wall-clock countdown'},indent=2))

    def test_04_all_sizes_seeds_zoom_dpr_and_projector(self):
        page=self.new_page(1280,800,1.5,clock=True);self.switch(page)
        for size in ['25x19','21x15','17x13','13x9']:
            for seed in ['1','20264049']:
                page.fill('#seed',seed);page.select_option('#maze',size);page.click('#generate');self.rendered(page)
                first=self.snapshot(page);page.click('#generate');self.rendered(page)
                self.assertEqual(self.snapshot(page)['map2d']['cacheBuilds'],first['map2d']['cacheBuilds'])
                self.assertEqual(self.snapshot(page)['maze'],first['maze'])
                for zoom in ['125','150','175']:
                    page.select_option('#zoom2d',zoom);self.rendered(page);s=self.snapshot(page);c=s['map2d']['camera']
                    self.assertEqual(s['zoom2d'],int(zoom));self.assertLess(c['width']/c['scale'],c['worldWidth']*.5)
                    self.assertLess(c['height']/c['scale'],c['worldHeight']*.5)
                    for i,m in enumerate(s['map2d']['markers'][:5]):self.assertEqual(m['position'],s['game']['checkpoints'][i]['position'])
                    self.assertEqual(s['map2d']['vehicle']['heading'],s['game']['vehicle']['heading'])
                page.keyboard.press('m');self.capture(page,f'map-{size}-seed-{seed}');page.keyboard.press('m')
                self.assertEqual(self.snapshot(page)['game']['completed'],[False]*5)
        for width,height in [(1280,800),(1366,768),(1920,1080)]:
            page.set_viewport_size({'width':width,'height':height});self.rendered(page)
            self.assertFalse(page.evaluate('document.documentElement.scrollHeight>innerHeight||document.documentElement.scrollWidth>innerWidth'))
            self.assertTrue(page.locator('#toggle-view').is_visible());self.assertTrue(page.locator('#zoom2d').is_visible())
            self.assertEqual(page.evaluate('document.querySelector("#map-view").width'),round(page.locator('#stage').bounding_box()['width']))
            self.capture(page,f'2d-{width}x{height}-dpr150')
        page.click('#fullscreen');page.wait_for_function('!!document.fullscreenElement');self.capture(page,'2d-fullscreen-projector')
        self.assertFalse(page.evaluate('document.documentElement.scrollHeight>innerHeight'))

    def test_05_overview_inspect_benchmark_and_context_recovery(self):
        page=self.new_page(clock=True);plan=self.prepare_route(page);held=set()
        for step in plan['steps']:
            if step['kind']=='drive':held,_=self.key_hold(page,held,step['keys'],step['seconds'])
            else:
                for key in held:page.keyboard.up(key)
                page.keyboard.press('e');page.click('#dialog-close');break
        self.switch(page);saved=self.snapshot(page)['game']
        for action in ['overview','inspection']:
            if action=='overview':page.click('#camera')
            else:page.select_option('#inspection','checkpoint')
            page.locator('#view').focus();page.keyboard.down('w');page.evaluate('window.showcase.advanceSimulation(2)');page.keyboard.up('w')
            self.assertEqual(self.snapshot(page)['game'],saved)
            page.click('#camera');self.rendered(page);self.assertEqual(self.snapshot(page)['drivingView'],'2d')
            self.assertEqual(self.snapshot(page)['game'],saved)
        page.evaluate('window.showcase.runBenchmark({warmupMs:200,durationMs:600})');self.rendered(page)
        self.assertEqual(self.snapshot(page)['game'],saved);self.assertEqual(self.snapshot(page)['drivingView'],'2d')
        page.evaluate("window.loss=document.querySelector('#view').getContext('webgl2').getExtension('WEBGL_lose_context');loss.loseContext()")
        page.wait_for_function('window.showcase.snapshot().contextLost');page.wait_for_timeout(300);page.evaluate('loss.restoreContext()')
        page.wait_for_function('window.showcase.snapshot().restoredContexts===1',timeout=120000)
        self.assertEqual(self.snapshot(page)['game'],saved);self.switch(page);self.rendered(page)
        self.assertEqual(page.locator('#message').inner_text(),'');self.assertEqual(self.snapshot(page)['drivingView'],'3d')
        page.fill('#seed','23');page.click('#generate');self.assertEqual(self.snapshot(page)['game']['completed'],[False]*5)
        self.assertEqual(self.snapshot(page)['game']['map'],{'open':False,'remainingMs':30000})


    def assert_fullscreen(self,page,active):
        page.wait_for_function('active => Boolean(document.fullscreenElement) === active',arg=active)
        label='Exit Fullscreen' if active else 'Fullscreen'
        aria='Exit Fullscreen' if active else 'Enter Fullscreen'
        page.wait_for_function('expected => document.querySelector("#fullscreen").textContent === expected',arg=label)
        self.assertEqual(page.locator('#fullscreen').get_attribute('aria-label'),aria)

    def press_escape(self,page):
        page.bring_to_front()
        if sys.platform!='linux':
            page.keyboard.press('Escape');return
        # CDP keyboard events reach the page but do not invoke Chromium's native
        # fullscreen exit. Send a real X11 Escape under the suite's Xvfb display.
        x11=ctypes.CDLL(ctypes.util.find_library('X11'))
        xtest=ctypes.CDLL(ctypes.util.find_library('Xtst'))
        x11.XOpenDisplay.argtypes=[ctypes.c_char_p];x11.XOpenDisplay.restype=ctypes.c_void_p
        x11.XKeysymToKeycode.argtypes=[ctypes.c_void_p,ctypes.c_ulong];x11.XKeysymToKeycode.restype=ctypes.c_ubyte
        x11.XSync.argtypes=[ctypes.c_void_p,ctypes.c_int]
        x11.XCloseDisplay.argtypes=[ctypes.c_void_p]
        xtest.XTestFakeKeyEvent.argtypes=[ctypes.c_void_p,ctypes.c_uint,ctypes.c_int,ctypes.c_ulong]
        display=x11.XOpenDisplay(None)
        self.assertTrue(display,'Native Escape requires the suite X display')
        try:
            key=x11.XKeysymToKeycode(display,0xff1b)
            self.assertTrue(key)
            self.assertTrue(xtest.XTestFakeKeyEvent(display,key,True,0))
            self.assertTrue(xtest.XTestFakeKeyEvent(display,key,False,0))
            x11.XSync(display,False)
        finally:x11.XCloseDisplay(display)

    def test_06_player_fullscreen_button_and_escape_preserve_earned_question_progress(self):
        # Publish only a synthetic fixture into this suite's disposable HTTP root.
        unit=json.loads((ROOT/'tests/fixtures/v2/S02.json').read_text())
        publication=Path(self.temp.name)/'nested/course/dist/assignments'
        (publication/'S02.json').write_text(json.dumps(unit))
        (publication/'manifest.json').write_text(json.dumps({'schemaVersion':1,'units':[
            {'unitId':'S02','title':unit['title'],'file':'S02.json'}]}))
        page=self.new_page(1280,800,1.5,clock=True,tools=False)
        harness.choose_quality(page,'Low')
        self.assertTrue(page.locator('#tools').is_hidden());self.assert_fullscreen(page,False)
        page.click('#assignment-mode');page.wait_for_function('document.querySelector("#unit-select").value === "S02"')
        page.click('#load-assignment');page.click('#confirm-assignment')
        page.wait_for_function('window.showcase.snapshot().assignment?.unitId === "S02"')
        before=self.snapshot(page)
        plan=json.loads(subprocess.check_output(['node','showcase3d/tests/write-education-route.mjs',
            '25','19',str(before['maze']['seed']),'5'],cwd=ROOT,text=True))
        held=set()
        for step in plan['steps']:
            if step['kind']=='drive':held,_=self.key_hold(page,held,step['keys'],step['seconds'])
            else:
                for key in held:page.keyboard.up(key)
                page.keyboard.press('e')
                question=unit['questions'][int(step['id'][1:])-1]
                page.click(f'[data-answer="{question["correctOptions"][-1]}"]')
                page.click('#dialog-close');break
        page.keyboard.press('m');page.wait_for_timeout(250);page.keyboard.press('m')
        saved=self.snapshot(page)
        self.assertEqual(sum(saved['game']['completed']),1)
        self.assertGreater(saved['game']['vehicle']['distance'],0)
        self.assertLess(saved['game']['map']['remainingMs'],30000)
        page.evaluate('''() => {
            window.fullscreenEvents=[];
            document.addEventListener('fullscreenchange',()=>fullscreenEvents.push(Boolean(document.fullscreenElement)));
        }''')
        for name,action,active in [
            ('entered',lambda:page.click('#fullscreen'),True),
            ('button-exit',lambda:page.click('#fullscreen'),False),
            ('entered-again',lambda:page.click('#fullscreen'),True),
            ('escape-exit',lambda:self.press_escape(page),False),
        ]:
            action();self.assert_fullscreen(page,active)
            current=self.snapshot(page)
            for field in ['game','maze','assignment','drivingView','rebuilds']:
                self.assertEqual(current[field],saved[field],field)
            self.capture(page,f'player-fullscreen-{name}')
        self.assertEqual(page.evaluate('fullscreenEvents'),[True,False,True,False])

    def test_07_player_fullscreen_request_and_exit_failures_keep_actual_label(self):
        page=self.new_page(1280,800,1.5,clock=True,tools=False)
        harness.choose_quality(page,'Low');saved=self.snapshot(page)
        self.assert_fullscreen(page,False)
        page.evaluate('''() => { document.documentElement.requestFullscreen = () => Promise.reject(
            new DOMException('Synthetic request rejection','NotAllowedError')); }''')
        page.click('#fullscreen');page.wait_for_function('document.querySelector("#status").textContent.includes("Fullscreen unavailable")')
        self.assert_fullscreen(page,False)
        page.evaluate('delete document.documentElement.requestFullscreen')
        page.click('#fullscreen');self.assert_fullscreen(page,True)
        page.evaluate('''() => { document.querySelector('#status').textContent='';
            document.exitFullscreen = () => Promise.reject(new DOMException('Synthetic exit rejection','InvalidStateError')); }''')
        page.click('#fullscreen');page.wait_for_function('document.querySelector("#status").textContent.includes("Fullscreen unavailable")')
        self.assert_fullscreen(page,True)
        page.evaluate('delete document.exitFullscreen')
        page.click('#fullscreen');self.assert_fullscreen(page,False)
        current=self.snapshot(page)
        for field in ['game','maze','assignment','drivingView','rebuilds']:
            self.assertEqual(current[field],saved[field],field)


if __name__=='__main__':unittest.main(verbosity=2)
