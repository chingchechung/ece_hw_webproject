"""Synthetic Phase 5A visual review and paired Phase 4 rendering benchmarks."""
import hashlib
import json
from pathlib import Path
import re
import statistics
import unittest

from browser_student import StudentBrowserHarness, fixture, ROOT
from drive_reference import DRIVE_BRIDGE

ORIGINAL=(ROOT/'emi_maze_dualview_v1.2/index.html').read_text()
BASELINE_DRAW=ORIGINAL[ORIGINAL.index('  function roundedRect('):ORIGINAL.index('  function readMapBudget(')]
assert hashlib.sha256(BASELINE_DRAW.encode()).hexdigest()=='60f1b4b7a818b98c49fd0272901424cf1004ff3c7ac5d9ebe18908cef2149916'
BASELINE_SPRITE=re.search(r"  var CHARACTER_SHEET='[^']+';", ORIGINAL).group()
BRIDGE=(ROOT/'tests/visual_probe.js').read_text()



class VisualHarness(StudentBrowserHarness):
    artifact_directory=ROOT/'test-results/phase-5a'

    def open(self,hooks=True,index=False):
        def inject(route):
            source=route.fetch().text()
            if getattr(self,'baseline',False) and '  // BEGIN 2D VISUALS' in source:
                a=source.index('  // BEGIN 2D VISUALS');b=source.index('  // END 2D VISUALS',a)+len('  // END 2D VISUALS')
                source=source[:a]+BASELINE_SPRITE+"\n  var playerSheet=new Image();playerSheet.src=CHARACTER_SHEET;\n  var rpgVisuals=null;\n"+BASELINE_DRAW+source[b:]
            source=source.replace('var rpgVisuals=MazeRpgVisuals.create(TILE);','var __assetStart=performance.now();var rpgVisuals=MazeRpgVisuals.create(TILE);window.__assetMs=performance.now()-__assetStart;')
            source=source.replace('Date.now()+Math.floor(Math.random()*999999)','104729+250000')
            source=source.replace('  sizeCanvas();requestAnimationFrame(frame);loader.start();',getattr(self,'bridge',BRIDGE)+'  sizeCanvas();loader.start();')
            route.fulfill(body=source,content_type='application/javascript')
        self.page.route('**/js/game.js*',inject)
        self.page.goto(self.url)
        self.page.wait_for_function("!document.querySelector('#unitSelect').disabled")
        self.load('S02')
        self.settle_layout()
        self.page.evaluate('visualTest.ready()')
        self.page.evaluate('visualTest.overview()')

    def settle_layout(self):
        # A CDP viewport update can return before Chromium delivers its resize
        # event. Flush that event before snapshotting camera/viewport state;
        # otherwise it can land while V temporarily changes toolbar geometry.
        self.page.evaluate('''async () => {
            await document.fonts.ready;
            await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
        }''')

    def prepare(self):
        self.artifact_directory.mkdir(parents=True,exist_ok=True)
        self.publish(fixture(2,'S02'))
        self.open()

    def shot(self,name):
        self.page.screenshot(path=str(self.artifact_directory/name))


class VisualTests(VisualHarness):
    def test_character_directions_idle_and_walk_artifacts(self):
        self.prepare()
        self.page.set_viewport_size({'width':1366,'height':900})
        hashes=self.page.evaluate('visualTest.characterSheet()')
        self.assertEqual(len({row[0] for row in hashes}),4)
        for row in hashes:
            self.assertNotEqual(row[0],row[1])
            self.assertGreaterEqual(len(set(row[2:])),3)
        self.page.locator('#visualSheet').screenshot(path=str(self.artifact_directory/'character-directions-walk.png'))
        self.page.evaluate('visualTest.closeup()')
        self.page.locator('#visualSheet').screenshot(path=str(self.artifact_directory/'character-closeup.png'))
        self.page.evaluate('visualTest.removeSheet()')

    def test_station_finish_states_and_intersection_artifacts(self):
        self.prepare()
        self.page.set_viewport_size({'width':1366,'height':900})
        result=self.page.evaluate('visualTest.objectSheet()')
        self.assertNotEqual(result['hashes'][0],result['hashes'][1])
        self.assertNotEqual(result['hashes'][2],result['hashes'][3])
        self.assertNotEqual(result['hashes'][4],result['hashes'][5])
        self.assertEqual(result['labelBefore'],result['labelAfter'])
        self.assertTrue(any(result['labelBefore']))
        self.assertNotEqual(result['nearHash'],result['farHash'])
        self.page.locator('#visualSheet').screenshot(path=str(self.artifact_directory/'stations-finish-states.png'))
        self.page.evaluate('visualTest.removeSheet()')
        self.page.set_viewport_size({'width':1366,'height':768})
        self.page.evaluate('visualTest.approach()');self.shot('station-before.png')
        self.assertTrue(self.page.is_visible('#interactTip.show'))
        self.page.evaluate('visualTest.passFirst()');self.shot('station-after.png')
        self.page.evaluate('visualTest.parkExit()');self.shot('finish-locked.png')
        self.page.evaluate('visualTest.passAll()');self.shot('finish-unlocked.png')
        junction=self.page.evaluate('visualTest.intersection()')
        self.assertGreaterEqual(junction['degree'],3);self.shot('intersection.png')

    def test_rendering_preserves_state_zoom_facing_and_viewport(self):
        self.prepare()
        original=self.page.evaluate('visualTest.state()')
        self.page.evaluate('for(let i=0;i<12;i++)visualTest.draw(i*.5)')
        self.assertEqual(self.page.evaluate('visualTest.state()'),original)
        self.page.keyboard.down('ArrowLeft');self.page.evaluate('visualTest.step(8)');self.page.keyboard.up('ArrowLeft')
        self.page.evaluate('visualTest.step(1)')
        stopped=json.loads(self.page.evaluate('visualTest.state()'))['player']
        self.assertEqual(stopped['dir'],'left');self.assertFalse(stopped['moving'])
        for zoom in ['1.5','1.75']:
            self.page.select_option('#zoomSelect',zoom)
            for width,height in [(1366,768),(1024,768),(390,844)]:
                self.page.set_viewport_size({'width':width,'height':height})
                self.settle_layout()
                self.page.evaluate('visualTest.overview()');self.assert_no_scroll()
                state=self.page.evaluate('visualTest.state()')
                self.page.keyboard.press('v');self.page.evaluate('visualTest.draw(1)')
                self.page.keyboard.press('v');self.page.evaluate('visualTest.draw(1)')
                before=json.loads(state);after=json.loads(self.page.evaluate('visualTest.state()'))
                # The preserved driving code can choose a safe heading at a wall.
                before['player']['dir']=after['player']['dir']
                self.assertEqual(after,before)
        self.shot('small-screen-175.png')

    def test_driving_art_changes_without_writing_shared_state(self):
        self.bridge=BRIDGE+DRIVE_BRIDGE
        self.prepare();self.page.keyboard.press('v')
        state=self.page.evaluate('visualTest.state()')
        self.page.evaluate('approvedDriveRender(1)');before=self.page.evaluate('visualTest.pixels()')
        self.shot('drive-before.png');self.assertEqual(self.page.evaluate('visualTest.state()'),state)
        self.page.evaluate('visualTest.draw(1)');after=self.page.evaluate('visualTest.pixels()')
        self.shot('drive-phase5b.png')
        self.assertNotEqual(before,after);self.assertEqual(self.page.evaluate('visualTest.state()'),state)

    def test_paired_performance_and_before_after_views(self):
        self.artifact_directory.mkdir(parents=True,exist_ok=True)
        self.publish(fixture(2,'S02'))
        results=[]
        for baseline in [True,False]:
            self.baseline=baseline
            self.open()
            for width,height in [(1366,768),(1024,768),(390,844)]:
                self.page.set_viewport_size({'width':width,'height':height})
                self.page.evaluate('visualTest.overview()')
                trials=[self.page.evaluate('visualTest.benchmark()') for _ in range(3)]
                result=dict(trials[0])
                for key in ['meanRenderMs','p95RenderMs','observedFps']:
                    result[key]=statistics.median(trial[key] for trial in trials)
                result['trials']=trials
                result.update(renderer='phase4' if baseline else 'phase5a',browser=self.browser.version)
                results.append(result)
                self.shot(f"{'before' if baseline else 'after'}-{width}.png")
                self.assert_no_scroll()
        (self.artifact_directory/'performance.json').write_text(json.dumps(results,indent=2))


if __name__=='__main__':
    unittest.main(verbosity=2)
