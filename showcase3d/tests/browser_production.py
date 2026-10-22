"""P2.1 production UI and release-package checks, using synthetic assignments only."""
import json
from pathlib import Path
import shutil
import subprocess
import unittest
from zipfile import ZipFile
import browser_education as education

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'test-results/3d-p2.1'
education.OUT=OUT
education.harness.OUT=OUT
Base=education.EducationBrowserTests


class ProductionUiTests(unittest.TestCase):
    setUp=Base.setUp
    tearDown=Base.tearDown
    tearDownClass=classmethod(Base.tearDownClass.__func__)
    new_page=Base.new_page
    rendered=Base.rendered
    snapshot=Base.snapshot
    key_hold=Base.key_hold
    capture=Base.capture
    open_picker=Base.open_picker
    load=Base.load

    @classmethod
    def setUpClass(cls):
        education.EducationBrowserTests.setUpClass.__func__(cls)
        subprocess.run(['python','showcase3d/scripts/package.py'],cwd=ROOT,check=True)
        archive=OUT/'showcase3d-1.0.0-rc1-static.zip'
        with ZipFile(archive) as zipped:
            assert len(zipped.namelist())==11
            assert all(name.startswith('showcase3d/') for name in zipped.namelist())
            assert json.loads(zipped.read('showcase3d/dist/assignments/manifest.json'))=={'schemaVersion':1,'units':[]}
            info=json.loads(zipped.read('showcase3d/dist/build-info.json'))
            assert info['version']=='1.0.0-rc1'
            for name in info['files']:
                assert zipped.read('showcase3d/dist/'+name)==(ROOT/'showcase3d/dist'/name).read_bytes()
            zipped.extractall(Path(cls.temp.name)/'nested/release')
        cls.package_url=cls.url.split('/nested/')[0]+'/nested/release/showcase3d/dist/'
        for name in ['before-1280x800-3d.png','before-1280x800-2d.png']:
            shutil.copyfile(ROOT/'docs/images/3d-p2.1'/name,OUT/name)

    def no_scroll_or_clipped_controls(self,page):
        self.assertFalse(page.evaluate('document.documentElement.scrollWidth>innerWidth||document.documentElement.scrollHeight>innerHeight'))
        for control in page.locator('button:visible,select:visible,input:visible').all():
            box=control.bounding_box()
            self.assertGreaterEqual(box['x'],0);self.assertGreaterEqual(box['y'],0)
            self.assertLessEqual(box['x']+box['width'],page.viewport_size['width']+.5)
            self.assertLessEqual(box['y']+box['height'],page.viewport_size['height']+.5)

    def reload_tools(self,page,query):
        # Reuse one tab so background software WebGL contexts do not compete.
        page.goto(self.url+'?'+(query+'&' if query else '')+'testClock=1')
        page.wait_for_function('window.showcase?.snapshot().ready',timeout=120000)
        if query and 'debug=1' in query:page.select_option('#scale','0.5')
        education.harness.choose_quality(page,'Low')
        if page.locator('#diagnostics').is_visible():page.locator('#diagnostics summary').click()
        page.locator('#view').focus()

    def test_01_clean_default_layout_settings_keyboard_and_larger_game_area(self):
        page=self.new_page(quality=None);baseline=json.loads((ROOT/'showcase3d/tests/fixtures/p2-ui-layout.json').read_text())
        self.assertEqual(self.snapshot(page)['quality'],'Medium');self.assertEqual(self.snapshot(page)['targetFps'],30)
        self.assertEqual(self.snapshot(page)['scaleOverride'],None)
        self.assertEqual(page.locator('#device').count(),0)
        for control in ['#tools','#diagnostics','#camera','#benchmark','#scale','#fps','#seed','#maze','#generate','#inspection','#scene-info']:
            self.assertTrue(page.locator(control).is_hidden(),control)
        body=page.locator('body').inner_text()
        for term in ['topology','P2','Device','benchmark','FPS','GPU','seed']:
            self.assertNotIn(term,body)
        comparisons=[]
        for old in baseline['viewports']:
            w,h=old['width'],old['height'];page.set_viewport_size({'width':w,'height':h});self.rendered(page)
            self.capture(page,f'default-{w}x{h}-3d');stage=page.locator('#stage').bounding_box()
            controls=page.locator('button:visible,select:visible,input:visible').count()
            self.assertGreaterEqual(stage['height']-old['stage']['height'],50)
            self.assertLessEqual(controls,8);self.no_scroll_or_clipped_controls(page)
            comparisons.append({'viewport':[w,h],'dpr':1.5,'before':old,'after':{'stage':stage,'visible_controls':controls},
                'added_game_height':stage['height']-old['stage']['height']})
            page.locator('#view').focus();before=self.snapshot(page)['game'];page.keyboard.press('v')
            self.assertEqual(self.snapshot(page)['game'],before)
            self.capture(page,f'default-{w}x{h}-2d');self.no_scroll_or_clipped_controls(page);page.keyboard.press('v')
        (OUT/'layout-comparison.json').write_text(json.dumps(comparisons,indent=2))
        page.set_viewport_size({'width':1280,'height':800})
        page.locator('#settings').focus();page.keyboard.press('Enter')
        self.assertTrue(page.locator('#graphics-dialog').is_visible());self.capture(page,'compact-graphics-settings')
        paused=self.snapshot(page)['game']
        for _ in range(8):
            page.keyboard.press('Tab');self.assertTrue(page.evaluate('document.querySelector("#graphics-dialog").contains(document.activeElement)'))
        page.keyboard.press('Escape');self.assertEqual(self.snapshot(page)['game'],paused)
        self.assertIn(page.evaluate('document.activeElement.id'),['view','map-view'])
        self.open_picker(page);self.capture(page,'production-published-unit-selector');page.click('#cancel-assignment')

    def test_02_presenter_debug_entry_exit_and_retained_benchmark(self):
        page=None
        for query in ['presenter=1','debug=1','presenter=1&debug=1']:
            if page is None:page=self.new_page(tools=query)
            else:self.reload_tools(page,query)
            presenter='presenter=1' in query;debug='debug=1' in query
            self.assertEqual(self.snapshot(page)['ui']['allowed'],{'presenter':presenter,'debug':debug})
            self.assertEqual(page.locator('#device').count(),0)
            self.assertEqual(page.locator('#presenter-tools').is_visible(),presenter)
            self.assertEqual(page.locator('#developer-tools').is_visible(),debug)
            original=self.snapshot(page)['game']
            if presenter:
                page.click('#camera');self.assertEqual(self.snapshot(page)['view'],'overview')
                self.assertEqual(self.snapshot(page)['game'],original)
                page.select_option('#inspection','checkpoint');self.assertEqual(self.snapshot(page)['view'],'inspection')
                self.capture(page,'presenter-controls' if not debug else 'combined-tools')
            if debug and not presenter:
                results=page.evaluate('window.showcase.runBenchmark({warmupMs:200,durationMs:600})')
                self.assertEqual(len(results),6);self.assertEqual(self.snapshot(page)['game'],original)
                page.locator('#diagnostics summary').click();self.rendered(page)
                self.assertIn(self.snapshot(page)['metrics']['identity']['renderer'],page.locator('#stats').inner_text())
                self.capture(page,'debug-controls-and-reported-renderer')
            before=self.snapshot(page)['game'];page.click('#exit-tools');self.rendered(page)
            state=self.snapshot(page);self.assertEqual(state['game'],before);self.assertEqual(state['view'],'driving')
            self.assertEqual(state['ui']['requested'],{'presenter':False,'debug':False})
            self.assertNotIn('presenter=',page.url);self.assertNotIn('debug=',page.url)
            self.assertIn('testClock=1',page.url);self.assertTrue(page.locator('#tools').is_hidden())
            self.assertTrue(page.locator('#diagnostics').is_hidden());self.no_scroll_or_clipped_controls(page)
            self.assertNotIn('benchmark',page.locator('body').inner_text().lower())

    def test_03_education_restrictions_in_all_tool_modes_and_settings_map_pause(self):
        page=None
        for query in [False,'presenter=1','debug=1','presenter=1&debug=1']:
            if page is None:page=self.new_page(tools=query)
            else:self.reload_tools(page,query)
            self.load(page,'S01')
            page.locator('#view').focus();page.keyboard.down('w');page.evaluate('window.showcase.advanceSimulation(.8)');page.keyboard.up('w');page.keyboard.press('v')
            before=self.snapshot(page)
            self.assertEqual(before['ui']['allowed'],{'presenter':False,'debug':False})
            page.evaluate('''() => {
                for(const id of ['camera','generate','benchmark','export']){const el=document.getElementById(id);el.disabled=false;el.click();}
                for(const [id,value] of [['inspection','finish'],['maze','13x9'],['scale','1.25'],['fps','60']]){
                    const el=document.getElementById(id);el.disabled=false;el.value=value;el.dispatchEvent(new Event('change'));
                }
            }''')
            page.evaluate('window.showcase.runBenchmark({warmupMs:200,durationMs:600})');after=self.snapshot(page)
            for key in ['game','maze','pose','scaleOverride','targetFps','rebuilds']:self.assertEqual(after[key],before[key],key)
            self.assertTrue(page.locator('#tools').is_hidden());self.assertTrue(page.locator('#diagnostics').is_hidden())
            page.keyboard.press('m');page.wait_for_timeout(250);page.click('#settings');paused=self.snapshot(page)
            self.assertTrue(paused['game']['map']['open']);self.assertLess(paused['game']['map']['remainingMs'],30000)
            self.assertEqual(page.locator('#map-view').evaluate('c=>getComputedStyle(c).visibility'),'hidden')
            page.wait_for_timeout(400);page.keyboard.press('v');page.keyboard.press('m')
            self.assertEqual(self.snapshot(page)['game'],paused['game'])
            for quality in ['High','Low','Medium']:
                page.click(f'[data-quality="{quality}"]');self.assertEqual(self.snapshot(page)['game'],paused['game'])
            page.click('#settings-close');page.keyboard.press('m')
            self.assertGreater(self.snapshot(page)['game']['map']['remainingMs'],0)
            self.assertLessEqual(self.snapshot(page)['game']['map']['remainingMs'],paused['game']['map']['remainingMs'])
            self.assertEqual(self.snapshot(page)['assignment']['unitId'],'S01');self.no_scroll_or_clipped_controls(page)

    def test_04_extracted_offline_zip_nested_paths_and_absent_optional_dom(self):
        init="""document.addEventListener('DOMContentLoaded',()=>{for(const id of ['tools','diagnostics','scene-info'])document.getElementById(id)?.remove();});"""
        page=self.new_page(tools='debug=1',quality=None,init_script=init)
        page.goto(self.package_url+'?debug=1&testClock=1');page.wait_for_function('window.showcase?.snapshot().ready',timeout=120000)
        self.assertEqual(page.locator('#device,#tools,#diagnostics,#scene-info').count(),0)
        self.assertEqual(self.snapshot(page)['targetFps'],30)
        results=page.evaluate('window.showcase.runBenchmark({warmupMs:200,durationMs:600})');self.assertEqual(len(results),6)
        self.open_picker(page);self.assertIn('No educational units',page.locator('#assignment-status').inner_text());page.click('#cancel-assignment')
        page.context.set_offline(True);page.keyboard.press('v');page.locator('#map-view').focus()
        page.keyboard.down('w');page.evaluate('window.showcase.advanceSimulation(.8)');page.keyboard.up('w')
        self.assertGreater(self.snapshot(page)['game']['vehicle']['distance'],0);page.keyboard.press('r')
        self.assertEqual(self.snapshot(page)['game']['map']['remainingMs'],30000)
        self.capture(page,'extracted-package-offline');self.no_scroll_or_clipped_controls(page)


del Base  # unittest must discover only this suite, not the imported helper class.
if __name__=='__main__':unittest.main(verbosity=2)
