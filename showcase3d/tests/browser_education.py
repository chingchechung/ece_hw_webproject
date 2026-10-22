"""Synthetic-only P2 acceptance: actual keyboard driving, never vehicle setters."""
from functools import partial
from http.server import ThreadingHTTPServer
from io import BytesIO
import json
import base64
import math
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import unittest
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
from PIL import Image
import browser_showcase as harness

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'test-results/3d-p2'
harness.OUT=OUT
FIXTURES={name:json.loads((ROOT/path).read_text()) for name,path in {
    'S01.json':'tests/fixtures/S01.json','S02.json':'tests/fixtures/v2/S02.json'}.items()}
MANIFEST={'schemaVersion':1,'units':[{'unitId':name[:-5],'title':unit['title'],'file':name} for name,unit in FIXTURES.items()]}


class EducationBrowserTests(unittest.TestCase):
    setUp=harness.ShowcaseBrowserTests.setUp
    tearDownClass=classmethod(harness.ShowcaseBrowserTests.tearDownClass.__func__)
    rendered=harness.ShowcaseBrowserTests.rendered
    snapshot=harness.ShowcaseBrowserTests.snapshot
    key_hold=harness.ShowcaseBrowserTests.key_hold

    @classmethod
    def setUpClass(cls):
        OUT.mkdir(parents=True,exist_ok=True);cls.delays={};cls.started_requests={}
        class Handler(harness.QuietHandler):
            def do_GET(self):
                name=urlparse(self.path).path.rsplit('/',1)[-1]
                if name in cls.delays:
                    cls.started_requests[name].set();cls.delays[name].wait(15)
                try:super().do_GET()
                except (BrokenPipeError,ConnectionResetError):pass
        cls.temp=tempfile.TemporaryDirectory();served=Path(cls.temp.name)/'nested/course/dist'
        shutil.copytree(ROOT/'showcase3d/dist',served)
        # Fixtures are copied only into the disposable HTTP root, never production dist.
        cls.fixture_dir=served/'assignments'
        for name,unit in FIXTURES.items():(cls.fixture_dir/name).write_text(json.dumps(unit))
        (cls.fixture_dir/'manifest.json').write_text(json.dumps(MANIFEST))
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),partial(Handler,directory=cls.temp.name))
        threading.Thread(target=cls.server.serve_forever,daemon=True).start()
        cls.url=f'http://127.0.0.1:{cls.server.server_port}/nested/course/dist/'
        cls.pw=sync_playwright().start();preferred=os.environ.get('EMI_3D_BROWSER_PATH') or cls.pw.chromium.executable_path
        executable=preferred if Path(preferred).is_file() else shutil.which('chromium') or shutil.which('chromium-browser')
        if not executable:raise RuntimeError('Install Chromium; P2 tests cannot silently skip')
        cls.browser=cls.pw.chromium.launch(executable_path=executable,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
        (OUT/'browser-version.json').write_text(json.dumps({'browser':cls.browser.version,'executable':executable,'renderer_policy':'SwiftShader functional tests, not Intel FPS'},indent=2));cls.results=[]

    def new_page(self,width=1280,height=800,dpr=1.5,video=False,overrides=None,tools=False,quality='Low',init_script=None):
        page=harness.ShowcaseBrowserTests.new_page(self,width,height,dpr,video=video,clock=True,tools=tools,init_script=init_script)
        if not hasattr(self,'overrides'):self.overrides={};self.requests=[];self.links=[];self.expected_http=False
        changes=overrides if overrides is not None else {};self.overrides[page]=changes
        def assignments(route):
            name=urlparse(route.request.url).path.rsplit('/',1)[-1];self.requests.append(route.request.url)
            if name in changes:
                value=changes[name]
                route.fulfill(status=404 if value==404 else 200,content_type='application/json',body='missing' if value==404 else value if isinstance(value,str) else json.dumps(value))
            else:route.fallback()
        page.context.route('**/assignments/**',assignments)
        def external(route):
            host=urlparse(route.request.url).hostname
            if host in ('www.youtube.com','youtu.be','forms.gle','docs.google.com'):
                self.links.append({'url':route.request.url,'method':route.request.method});route.fulfill(content_type='text/html',body='<title>Synthetic external destination</title>TEST ONLY — no actual submission')
            else:route.fallback()
        page.context.route('https://**/*',external)
        if quality:harness.choose_quality(page,quality)
        if page.locator('#diagnostics').is_visible():page.locator('#diagnostics summary').click()
        page.locator('#view').focus();return page

    def tearDown(self):
        for event in self.delays.values():event.set()
        self.delays.clear();self.started_requests.clear()
        # Controlled negative HTTP cases still retain their browser log as evidence.
        if getattr(self,'expected_http',False):
            expected=[m for m in self.logs if m.get('type')=='error' and 'Failed to load resource: the server responded with a status of 404' in m.get('text','')]
            (OUT/f'{self._testMethodName}-expected-http-errors.json').write_text(json.dumps(expected,indent=2))
            self.logs=[m for m in self.logs if m not in expected]
        (OUT/f'{self._testMethodName}-requests.json').write_text(json.dumps({'local':getattr(self,'requests',[]),'intercepted_external':getattr(self,'links',[])},indent=2))
        harness.ShowcaseBrowserTests.tearDown(self)

    def capture(self,page,name):
        self.rendered(page);page.screenshot(path=str(OUT/f'{name}.png'))
        (OUT/f'{name}.json').write_text(json.dumps(self.snapshot(page),indent=2))

    def open_picker(self,page):
        page.click('#assignment-mode');page.wait_for_function("!document.querySelector('#assignment-status').textContent.startsWith('Reading')")

    def load(self,page,unit_id):
        self.open_picker(page);page.select_option('#unit-select',unit_id);page.click('#load-assignment')
        self.assertTrue(page.locator('#assignment-warning').is_visible());page.click('#confirm-assignment')
        page.wait_for_function('!document.querySelector("#assignment-picker").open')
        state=self.snapshot(page);self.assertEqual(state['assignment']['unitId'],unit_id)
        self.assertEqual(state['maze']['id'],'25x19');self.assertEqual(state['game']['map']['remainingMs'],30000)
        self.assertEqual(state['game']['failures'],0);return state

    def plan(self,page,exit_only=False):
        s=self.snapshot(page);w,h=s['maze']['id'].split('x')
        args=['node','showcase3d/tests/write-education-route.mjs',w,h,str(s['maze']['seed']),str(s['assignment']['questionCount'])]
        if exit_only:args.append('exit')
        return json.loads(subprocess.check_output(args,cwd=ROOT,text=True))

    def route(self,page,unit,wrong_at=None,exit_only=False,name='route'):
        plan=self.plan(page,exit_only);held=set();activations=0;switched=False
        geometry=self.snapshot(page)['rebuilds']
        for step in plan['steps']:
            if step['kind']=='drive':
                held,state=self.key_hold(page,held,step['keys'],step['seconds'])
                if not switched and not exit_only and state['game']['vehicle']['speed']==0:
                    for key in held:page.keyboard.up(key)
                    held=set()
                    # Apply released keys while stopped before comparing view state.
                    page.evaluate('window.showcase.advanceSimulation(1/60)')
                    before=self.snapshot(page);self.capture(page,f'{name}-before-v-3d')
                    page.keyboard.press('v');self.rendered(page);after=self.snapshot(page)
                    self.assertEqual(before['game'],after['game']);self.assertEqual(before['maze'],after['maze']);switched=True
                    self.capture(page,f'{name}-same-position-2d')
            else:
                for key in held:page.keyboard.up(key)
                held=set();before=self.snapshot(page)
                for key in ('x','y','heading','distance'):self.assertAlmostEqual(before['game']['vehicle'][key],step['expected'][key],places=7)
                page.keyboard.press('e')
                if exit_only:
                    self.assertTrue(page.locator('#dialog-overlay').is_hidden());self.assertFalse(self.snapshot(page)['game']['finished'])
                    self.assertIn('Exit locked',page.locator('#status').inner_text());self.capture(page,'exit-locked-at-real-vehicle');return
                page.wait_for_selector('#dialog-overlay:not([hidden])')
                if step['id']=='EXIT':
                    self.assertTrue(self.snapshot(page)['game']['finished']);self.assertIn(unit['unitId'],page.locator('#dialog-extra').inner_text())
                    link=page.locator('#dialog-extra a');self.assertEqual(link.get_attribute('href'),unit['googleFormUrl'])
                    self.assertEqual(link.get_attribute('rel'),'noopener noreferrer');self.capture(page,f'{name}-google-form-completion')
                    with page.expect_popup() as popup:link.click()
                    popup.value.wait_for_load_state();popup.value.close();break
                index=int(step['id'][1:])-1;q=unit['questions'][index]
                self.assertEqual(page.locator('[data-answer]').count(),len(q['options']))
                self.assertEqual(page.locator('input[type=checkbox]').count(),0)
                self.assertEqual(page.locator('#dialog-extra a').get_attribute('href'),q['questionVideoUrl'])
                self.assertEqual(self.snapshot(page)['game']['completed'],before['game']['completed'])
                self.capture(page,f'{name}-{q["id"]}-question-{len(q["options"])}-options')
                if activations==0:
                    page.click('#dialog-close');self.assertEqual(self.snapshot(page)['rebuilds'],geometry)
                    self.assertEqual(self.snapshot(page)['game']['completed'],before['game']['completed']);page.keyboard.press('e')
                    with page.expect_popup() as popup:page.locator('#dialog-extra a').click()
                    popup.value.wait_for_load_state();popup.value.close()
                labels=q.get('correctOptions',[q.get('correctOption')])
                label=next(c for c in 'ABCD'[:len(q['options'])] if c not in labels) if wrong_at==activations else labels[-1]
                page.click(f'[data-answer="{label}"]')
                if wrong_at==activations:
                    self.assertIn('Wrong answer',page.locator('#dialog-title').inner_text());self.capture(page,f'{name}-wrong-smaller-maze')
                    page.click('#dialog-close');return
                self.assertIn('Correct answer',page.locator('#dialog-title').inner_text())
                self.assertEqual(page.locator('#dialog-extra a').get_attribute('href'),q['explanationVideoUrl'])
                self.assertEqual(self.snapshot(page)['rebuilds'],geometry,'Correct answer rebuilt all maze geometry')
                self.capture(page,f'{name}-{q["id"]}-correct')
                if activations==0:
                    with page.expect_popup() as popup:page.locator('#dialog-extra a').click()
                    popup.value.wait_for_load_state();popup.value.close()
                page.click('#dialog-close');activations+=1
                if activations==1:
                    if name=='v1-four-complete':
                        # A failed switch after real earned progress must retain that progress.
                        saved=self.snapshot(page)['game'];self.expected_http=True;self.overrides[page]['S02.json']=404
                        self.open_picker(page);page.select_option('#unit-select','S02');page.click('#load-assignment');page.click('#confirm-assignment')
                        page.wait_for_function("document.querySelector('#assignment-status').textContent.includes('HTTP 404')")
                        page.click('#cancel-assignment');self.assertEqual(self.snapshot(page)['game'],saved)
                        self.overrides[page].clear()
                    page.keyboard.press('m');self.capture(page,f'{name}-full-map-remaining');page.keyboard.press('m')
                    page.keyboard.press('v');self.capture(page,f'{name}-return-3d-progress')
        final=self.snapshot(page)
        self.assertEqual(final['game']['completed'],[True]*len(unit['questions']));self.assertEqual(final['game']['activations'],len(unit['questions']))
        self.assertTrue(final['game']['finished'])
        (OUT/f'{name}-control-completion.json').write_text(json.dumps({'plan':plan,'final':final,'video':Path(page.video.path()).name if page.video else None,
            'method':'Real W/S/A/D/V/M/E and answer clicks; explicitly accelerated physics clock, no vehicle setters'},indent=2))

    def test_01_manifest_loading_errors_cancellation_and_stale_fetch(self):
        page=self.new_page(overrides={'manifest.json':{'schemaVersion':1,'units':[]}})
        page.keyboard.down('w');page.evaluate('window.showcase.advanceSimulation(.8)');page.keyboard.up('w')
        self.open_picker(page);paused=self.snapshot(page)['game'];self.assertIn('No educational units',page.locator('#assignment-status').inner_text())
        page.wait_for_timeout(300);self.assertEqual(self.snapshot(page)['game'],paused)
        page.click('#cancel-assignment');self.assertEqual(self.snapshot(page)['challengeMode'],'demo')
        self.overrides[page].clear();self.load(page,'S01');old=self.snapshot(page)['game']
        self.open_picker(page);self.capture(page,'published-unit-selector')
        self.assertEqual(page.locator('#unit-select option').count(),2)
        page.locator('#unit-select').evaluate("s=>s.add(new Option('Unlisted','S12'))")
        page.select_option('#unit-select','S12');count=len(self.requests);page.click('#load-assignment');self.assertEqual(len(self.requests),count)
        self.delays['S02.json']=threading.Event();self.started_requests['S02.json']=threading.Event()
        page.select_option('#unit-select','S02');page.click('#load-assignment');page.click('#confirm-assignment')
        self.assertTrue(self.started_requests['S02.json'].wait(5));page.click('#cancel-assignment');self.delays['S02.json'].set();page.wait_for_timeout(250)
        self.assertEqual(self.snapshot(page)['game'],old);self.assertEqual(self.snapshot(page)['assignment']['unitId'],'S01')
        del self.delays['S02.json'];self.expected_http=True
        for value in [404,'{broken',{'schemaVersion':99}]:
            self.overrides[page]['S02.json']=value;self.open_picker(page);page.select_option('#unit-select','S02');page.click('#load-assignment');page.click('#confirm-assignment')
            page.wait_for_function("!document.querySelector('#assignment-status').textContent.startsWith('Loading')")
            self.assertTrue(page.locator('#assignment-picker').is_visible());self.assertEqual(self.snapshot(page)['game'],old);page.click('#cancel-assignment')
        self.overrides[page].clear();self.overrides[page]['manifest.json']={'schemaVersion':1,'units':[MANIFEST['units'][0],MANIFEST['units'][0]]}
        self.open_picker(page);self.assertTrue(page.locator('#load-assignment').is_disabled());self.assertIn('more than once',page.locator('#assignment-status').inner_text().lower())
        self.overrides[page].clear();page.click('#refresh-assignments');page.wait_for_function('document.querySelectorAll("#unit-select option").length===2')
        page.click('#cancel-assignment');self.load(page,'S02');self.load(page,'S01');self.open_picker(page)
        page.click('#choose-demo');page.click('#confirm-assignment');self.assertEqual(self.snapshot(page)['challengeMode'],'demo')
        self.assertFalse(any(url.endswith('S12.json') for url in self.requests))

    def test_02_v1_four_questions_wrong_answer_then_complete_smaller_challenge(self):
        page=self.new_page(video=True);unit=FIXTURES['S01.json'];self.load(page,'S01')
        self.route(page,unit,exit_only=True);page.keyboard.press('r')
        self.route(page,unit,wrong_at=1,name='v1-first-attempt')
        smaller=self.snapshot(page);self.assertEqual(smaller['maze']['id'],'21x15');self.assertEqual(smaller['game']['failures'],1)
        self.assertEqual(smaller['game']['completed'],[False]*4);self.assertEqual(smaller['game']['map']['remainingMs'],30000);self.assertEqual(smaller['game']['vehicle']['distance'],0)
        self.route(page,unit,name='v1-four-complete')
        self.assertTrue(all(link['method']=='GET' for link in self.links));self.assertEqual(len(self.snapshot(page)['game']['checkpoints']),4)
        page.keyboard.press('r');fresh=self.snapshot(page);self.assertEqual(fresh['maze']['id'],'25x19');self.assertEqual(fresh['game']['failures'],0)
        self.assertEqual(fresh['game']['map']['remainingMs'],30000);self.assertTrue(page.locator('#dialog-overlay').is_hidden())

    def test_03_v2_five_multiple_accepted_answers_complete_real_route(self):
        page=self.new_page(video=True);unit=FIXTURES['S02.json'];self.load(page,'S02')
        self.route(page,unit,name='v2-five-complete')
        self.assertEqual(len(self.snapshot(page)['game']['checkpoints']),5)
        self.assertEqual(self.snapshot(page)['game']['completed'],[True]*5)
        self.assertTrue(all(link['method']=='GET' for link in self.links))

    def test_04_wrong_answer_progression_and_presentation_bypass_guards(self):
        page=self.new_page();unit=FIXTURES['S01.json'];self.load(page,'S01')
        for size in ['21x15','17x13','13x9','13x9']:
            self.route(page,unit,wrong_at=0,name=f'failure-{size}')
            self.assertEqual(self.snapshot(page)['maze']['id'],size);self.assertEqual(self.snapshot(page)['game']['completed'],[False]*4)
        before=self.snapshot(page)
        self.assertTrue(page.locator('#camera').is_hidden());self.assertTrue(page.locator('#inspection').is_disabled());self.assertTrue(page.locator('#benchmark').is_hidden())
        page.evaluate("document.querySelector('#camera').click();document.querySelector('#inspection').value='straight';document.querySelector('#inspection').dispatchEvent(new Event('change'));document.querySelector('#maze').value='13x9';document.querySelector('#maze').dispatchEvent(new Event('change'))")
        page.evaluate('window.showcase.runBenchmark({warmupMs:200,durationMs:600})');after=self.snapshot(page)
        self.assertEqual(after['game'],before['game']);self.assertEqual(after['maze'],before['maze']);self.assertEqual(after['pose'],before['pose'])
        page.keyboard.press('r');self.assertEqual(self.snapshot(page)['maze']['id'],'25x19');self.assertEqual(self.snapshot(page)['game']['failures'],0)

    def test_05_vehicle_headings_zoom_and_viewports(self):
        page=self.new_page();page.keyboard.press('v');page.locator('#map-view').focus()
        angle=self.snapshot(page)['game']['vehicle']['heading']
        page.keyboard.down('a');page.evaluate('seconds=>window.showcase.advanceSimulation(seconds)',abs(angle)/2.8);page.keyboard.up('a')
        for i in range(4):
            self.capture(page,f'car-heading-{i*90}');s=self.snapshot(page);v=s['map2d']['vehicle'];self.assertEqual(v['artwork'],'procedural-car-v1')
            self.assertAlmostEqual(v['heading'],i*math.pi/2,places=7)
            # Read the canvas pixels directly; screenshots can resample at fractional DPR.
            png=page.locator('#map-view').evaluate("c=>c.toDataURL().split(',')[1]")
            image=Image.open(BytesIO(base64.b64decode(png))).convert('RGB');ratio=image.width/s['map2d']['camera']['width']
            def patch(x,y):
                a=v['heading'];px=v['screen']['x']+(x*math.cos(a)-y*math.sin(a))*46/72;py=v['screen']['y']+(x*math.sin(a)+y*math.cos(a))*46/72
                return [image.getpixel((round(px*ratio)+dx,round(py*ratio)+dy)) for dx in [-1,0,1] for dy in [-1,0,1]]
            front=patch(26.5,-8);rear=patch(-27.5,-8)
            self.assertTrue(any(r>200 and g>190 and b<220 for r,g,b in front),'Expected pale yellow headlights')
            self.assertTrue(any(r-g>70 and r>190 for r,g,b in rear),'Expected red rear lamps, not a direction triangle')
            page.keyboard.down('d');page.evaluate('seconds=>window.showcase.advanceSimulation(seconds)',math.pi/2/2.8);page.keyboard.up('d')
        for width,height in [(1280,800),(1366,768),(1920,1080)]:
            page.set_viewport_size({'width':width,'height':height})
            for zoom in ['125','150','175']:page.select_option('#zoom2d',zoom);self.rendered(page)
            self.assertFalse(page.evaluate('document.documentElement.scrollHeight>innerHeight||document.documentElement.scrollWidth>innerWidth'))
            self.capture(page,f'car-{width}x{height}')
        page.keyboard.press('m');self.capture(page,'car-full-maze-map');s=self.snapshot(page)
        self.assertEqual(s['map2d']['vehicle']['x'],s['game']['vehicle']['x']);self.assertEqual(s['map2d']['vehicle']['y'],s['game']['vehicle']['y'])

    def test_06_safe_text_offline_notice_and_selector_map_pause(self):
        unit=json.loads(json.dumps(FIXTURES['S01.json']));unit['title']='<img src=x onerror="window.pwned=1"> TEST ONLY'
        for question in unit['questions']:question['prompt']='<script>window.pwned=1</script>'
        page=self.new_page(overrides={'S01.json':unit});self.load(page,'S01')
        self.assertEqual(page.locator('#unit-status img').count(),0);self.assertFalse(page.evaluate('!!window.pwned'))
        page.keyboard.press('m');page.wait_for_timeout(250);self.open_picker(page);paused=self.snapshot(page)['game']['map'];page.wait_for_timeout(650)
        self.assertEqual(self.snapshot(page)['game']['map'],paused);page.click('#cancel-assignment');page.keyboard.press('m')
        # The scene and already-loaded unit continue locally without any network.
        page.context.set_offline(True)
        plan=self.plan(page);held=set()
        for step in plan['steps']:
            if step['kind']=='drive':held,_=self.key_hold(page,held,step['keys'],step['seconds'])
            else:
                for key in held:page.keyboard.up(key)
                page.keyboard.press('e');break
        self.assertEqual(page.locator('#dialog-extra img,#dialog-extra script').count(),0)
        page.evaluate("Object.defineProperty(navigator,'onLine',{configurable:true,get:()=>false});window.dispatchEvent(new Event('offline'))")
        self.assertTrue(page.locator('#offline-note').is_visible());count=len(self.links);page.locator('#dialog-extra a').click()
        self.assertEqual(len(self.links),count);self.assertIn('Offline',page.locator('#dialog-extra .link-notice').first.inner_text())
        self.capture(page,'offline-local-assignment-question')


if __name__=='__main__':unittest.main(verbosity=2)
