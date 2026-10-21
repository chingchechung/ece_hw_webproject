"""Phase 4 end-to-end controls, recovery, randomized layout and route regressions.

Run with Python Playwright and system Chromium. Deterministic simulation time
speeds up long routes; all positions/angles/speeds are changed by real gameplay
updates under keyboard events. No teleport hook is installed in this suite.
"""
import itertools
import json
from pathlib import Path
import unittest

from browser_student import StudentBrowserHarness as BrowserSupport, fixture, ROOT


class GameplayTests(BrowserSupport):
    artifact_directory = ROOT / 'test-results/phase-4'

    # Shared static-server harness; no test code enters the deployable bundle.
    def open(self, hooks=True, index=False):
        driver=(ROOT/'tests/gameplay_driver.js').read_text()+'\n'+(ROOT/'tests/placement_quality.js').read_text()
        def inject(route):
            response=route.fetch()
            source=response.text().replace('  sizeCanvas();requestAnimationFrame(frame);loader.start();',
                                          driver+'\n  sizeCanvas();loader.start();')
            source="window.__mazeSeed=104729;\n"+source.replace('Date.now()+Math.floor(Math.random()*999999)', 'window.__mazeSeed+250000')
            self.assertIn('window.gameplayTest',source)
            route.fulfill(response=response,body=source)
        self.page.route('**/js/game.js',inject)
        self.page.goto(self.url+('index.html' if index else ''))
        self.page.wait_for_function("!document.querySelector('#assignmentStatus').textContent.includes('正在讀取')")

    def tearDown(self):
        folder=ROOT/'test-results/phase-4'
        folder.mkdir(parents=True,exist_ok=True)
        try:
            if not self.page.is_closed():
                self.page.screenshot(path=str(folder/(self._testMethodName+'.png')))
                (folder/(self._testMethodName+'.json')).write_text(json.dumps({
                    'state':self.state(),'errors':self.errors},ensure_ascii=False,indent=2))
        finally:
            super().tearDown()

    def state(self):
        return self.page.evaluate('gameplayTest.state()')

    def travel(self,index):
        self.page.locator('#maze').focus()
        return self.page.evaluate('i=>gameplayTest.route(i)',index)

    def interact(self):
        self.page.locator('#maze').focus()
        self.page.keyboard.press('e')
        self.page.wait_for_function('!gameplayTest.state().pending')

    def popup(self,expected):
        anchor=self.page.locator('#dialog a')
        self.assertEqual(anchor.get_attribute('href'),expected)
        self.assertEqual(anchor.get_attribute('target'),'_blank')
        self.assertEqual(anchor.get_attribute('rel'),'noopener noreferrer')
        with self.page.expect_popup() as popup:
            anchor.click()
        popup.value.wait_for_load_state()
        self.assertEqual(popup.value.url,expected)
        popup.value.close()
        self.page.locator('#dialog').focus()

    def prepare(self,version=2,unit_id='S02',mode='2d'):
        unit=fixture(version,unit_id)
        self.publish(unit)
        self.open()
        self.load(unit_id)
        if mode=='drive':
            self.page.keyboard.press('v')
        return unit

    def complete(self,unit,mode):
        # First reach the actual finish while locked, then visit all stations.
        self.travel(None)
        self.interact()
        self.assertEqual(self.page.locator('#dialog a').count(),0)
        for index,q in enumerate(unit['questions']):
            metrics=self.travel(index)
            self.assertEqual(self.state()['mode'],mode)
            self.interact()
            self.assertEqual(self.page.locator('[data-answer]').count(),len(q['options']))
            if index==0:
                name=f"{mode}-v{unit['schemaVersion']}-{unit['unitId']}-question.png"
                self.page.screenshot(path=str(ROOT/'test-results/phase-4'/name))
                self.popup(q['questionVideoUrl'])
            # Last accepted label deliberately covers non-first v2 answers.
            label=q.get('correctOption') or q['correctOptions'][-1]
            self.page.click(f'[data-answer="{label}"]')
            self.assertTrue(self.state()['done'][index])
            if index==0:
                self.popup(q['explanationVideoUrl'])
            self.page.click('#continueMaze')
        self.travel(None)
        self.interact()
        self.popup(unit['googleFormUrl'])
        self.assertEqual(self.state()['done'],[True]*len(unit['questions']))
        self.assertGreater(metrics['frames'],1000)
        if mode=='drive':
            self.assertGreater(metrics['turns'],10)
            self.assertGreater(metrics['driveEdges'],50)
            self.assertTrue({'w','s','a','d'}<=set(metrics['keys']))
        else:
            self.assertGreater(metrics['walkEdges'],50)
            self.assertTrue({'w','s','a','d','ArrowUp','ArrowDown','ArrowLeft','ArrowRight'}<=set(metrics['keys']))
        return metrics

    def test_walking_four_five_v1_v2_complete_with_controls(self):
        self.open()
        results=[]
        for version,unit_id in itertools.product([1,2],['S01','S02']):
            with self.subTest(version=version,unit=unit_id):
                unit=fixture(version,unit_id)
                self.publish(unit)
                self.page.click('#refreshManifest')
                self.page.wait_for_function("!document.querySelector('#unitSelect').disabled")
                self.load(unit_id)
                results.append(self.complete(unit,'2d'))
                self.page.click('#closeFinish')
                self.page.click('#unitLabel')
        (ROOT/'test-results/phase-4/walking-routes.json').write_text(json.dumps(results,indent=2))

    def test_driving_four_five_v1_v2_complete_with_controls(self):
        self.open()
        results=[]
        for version,unit_id in itertools.product([1,2],['S01','S02']):
            with self.subTest(version=version,unit=unit_id):
                unit=fixture(version,unit_id)
                self.publish(unit)
                self.page.click('#refreshManifest')
                self.page.wait_for_function("!document.querySelector('#unitSelect').disabled")
                self.load(unit_id)
                self.page.keyboard.press('v')
                results.append(self.complete(unit,'drive'))
                self.page.click('#closeFinish')
                self.page.click('#unitLabel')
        (ROOT/'test-results/phase-4/driving-routes.json').write_text(json.dumps(results,indent=2))

    def test_cancel_switch_refresh_and_failed_switch_preserve_attempt(self):
        a,b=fixture(1,'S01'),fixture(2,'S02')
        self.publish(a,b)
        self.open()
        self.load()
        self.travel(0);self.interact()
        self.page.click('[data-answer="A"]');self.page.click('#continueMaze')
        self.page.keyboard.press('v')
        self.page.click('#mapToggle')
        self.page.evaluate('gameplayTest.step(600)')
        before=self.state()
        self.page.click('#unitLabel')
        paused=self.state()
        self.assertEqual(paused['done'],before['done'])
        self.assertEqual(paused['player'],before['player'])
        self.page.evaluate('gameplayTest.step(1200)')
        self.assertEqual(self.state()['remaining'],paused['remaining'])
        self.page.select_option('#unitSelect','S02')
        self.page.click('#loadUnit')
        self.assertTrue(self.page.is_visible('#switchWarning'))
        self.assertIn('重置',self.page.inner_text('#switchMessage'))
        self.assertFalse(any(u.endswith('/S02.json') for u in self.requests))
        self.page.click('#cancelSwitch')
        self.assertEqual(self.state()['player'],paused['player'])
        self.assertEqual(self.state()['done'],paused['done'])
        self.assertEqual(self.state()['remaining'],paused['remaining'])
        self.assertEqual(self.state()['mode'],'drive')
        self.assertFalse(self.state()['paused'])
        # Refresh can remove the active unit without destroying its loaded attempt.
        self.page.click('#unitLabel');self.publish(b)
        self.page.click('#refreshManifest')
        self.page.wait_for_function("document.querySelector('#assignmentStatus').textContent.includes('不在公開清單')")
        self.assertEqual(self.state()['unit'],a)
        self.page.click('#returnToMaze')
        self.assertTrue(self.state()['done'][0])
        self.page.click('#unitLabel')
        (self.assignment_dir/'S02.json').write_text('{bad')
        self.click_load()
        self.page.wait_for_function("document.querySelector('#assignmentStatus').textContent.includes('可重試')")
        self.assertEqual(self.state()['unit'],a)
        self.page.keyboard.press('Escape')
        self.assertTrue(self.state()['done'][0])
        # Successful retry commits the switch and resets all mutable attempt state.
        self.write('S02.json',b)
        self.page.click('#unitLabel');self.load('S02')
        fresh=self.state()
        self.assertEqual(fresh['done'],[False]*5)
        self.assertEqual((fresh['width'],fresh['failures'],fresh['speed'],fresh['distance']),(25,0,0,0))
        self.assertEqual((fresh['player']['x'],fresh['player']['y']),(84,84))
        self.assertEqual(fresh['remaining'],30000)
        self.assertEqual(fresh['mode'],'2d')

    def test_cancel_inflight_switch_and_manifest_refresh_keeps_current(self):
        a,b=fixture(1,'S01'),fixture(2,'S02')
        self.publish(a,b);self.open();self.load()
        original=self.state()
        self.server.delays[self.prefix+'assignments/S02.json']=.5
        self.page.click('#unitLabel');self.page.select_option('#unitSelect','S02')
        self.click_load();self.page.click('#returnToMaze')
        self.page.wait_for_timeout(650)
        self.assertEqual(self.state()['unit'],original['unit'])
        self.assertEqual(self.state()['player'],original['player'])
        self.page.click('#unitLabel')
        (self.assignment_dir/'manifest.json').write_text('{bad')
        self.page.click('#refreshManifest')
        self.page.wait_for_function("document.querySelector('#assignmentStatus').textContent.includes('請重新整理')")
        self.page.click('#returnToMaze')
        self.assertEqual(self.state()['unit'],original['unit'])

    def test_wrong_shrinking_minimum_and_driving_after_every_reset(self):
        unit=self.prepare(mode='drive')
        layouts=[]
        for width in [21,17,13,13]:
            self.travel(0);self.interact()
            self.page.click('[data-answer="A"]');self.page.click('#continueMaze')
            self.travel(1);self.interact()
            self.page.click('[data-answer="A"]')  # Q02 accepts B or C.
            state=self.state()
            self.assertEqual(state['width'],width)
            self.assertEqual(state['done'],[False]*5)
            self.assertEqual(state['unit'],unit)
            self.assertEqual(state['remaining'],30000)
            self.assertEqual(state['mode'],'drive')
            layouts.append(state['stations'])
            self.page.click('#nextRound')
        self.assertNotEqual(layouts[2],layouts[3])
        # Minimum maze is fully completable via real driving controls.
        self.complete(unit,'drive')
        self.page.click('#closeFinish');self.page.click('#resetBtn')
        self.assertEqual(self.state()['width'],25)
        self.assertEqual(self.state()['done'],[False]*5)
        self.assertEqual(self.state()['remaining'],30000)

    def test_selector_viewports_expired_map_and_background_controls(self):
        self.prepare(mode='drive')
        self.page.click('#mapToggle')
        self.page.evaluate('gameplayTest.step(3601)')
        self.assertEqual(self.state()['remaining'],0)
        self.assertTrue(self.page.is_disabled('#mapToggle'))
        for width,height in [(1366,768),(1024,768),(390,844)]:
            self.page.set_viewport_size({'width':width,'height':height})
            self.page.click('#unitLabel')
            original=self.state()
            self.page.click('#loadUnit')
            self.assertTrue(self.page.is_visible('#switchWarning'))
            self.assertTrue(self.page.locator('.shell').evaluate('e=>e.inert'))
            self.page.keyboard.down('w');self.page.evaluate('gameplayTest.step(120)');self.page.keyboard.up('w')
            self.assertEqual(self.state()['player'],original['player'])
            self.assertEqual(self.state()['remaining'],0)
            self.assert_no_scroll()
            self.page.locator('#cancelSwitch').scroll_into_view_if_needed()
            self.page.locator('#cancelSwitch').focus()
            self.page.keyboard.press('Space')
            self.assertFalse(self.state()['paused'])
            self.assertFalse(self.page.locator('.shell').evaluate('e=>e.inert'))
            self.assertEqual(self.state()['remaining'],0)
            self.assert_no_scroll()
        self.page.set_viewport_size({'width':1366,'height':768})
        self.page.click('#resetBtn')
        self.assertEqual(self.state()['remaining'],30000)
        self.assertFalse(self.page.is_disabled('#mapToggle'))

    def test_layout_quality_and_drive_clearance_across_2000_seeded_maps(self):
        self.open()
        results=[]
        for unit_id in ['S01','S02']:
            self.publish(fixture(2,unit_id))
            self.page.click('#refreshManifest')
            self.page.wait_for_function("!document.querySelector('#unitSelect').disabled")
            self.load(unit_id)
            results.extend(self.page.evaluate('gameplayTest.quality(250)'))
            self.page.click('#unitLabel')
        self.assertEqual(sum(row['seeds'] for row in results),2000)
        (ROOT/'test-results/phase-4/placement-quality.json').write_text(json.dumps(results,indent=2))

    def test_keyboard_wall_collision_reverse_steering_and_camera_follow(self):
        self.prepare(unit_id='S01')
        # Start is against the north perimeter; walking into it must stop at radius 10.
        self.page.keyboard.down('w');self.page.evaluate('gameplayTest.step(120)');self.page.keyboard.up('w')
        self.assertGreaterEqual(self.state()['player']['y'],66)
        position=self.state()['player']
        self.page.keyboard.down('ArrowUp');self.page.evaluate('gameplayTest.step(120)');self.page.keyboard.up('ArrowUp')
        self.assertEqual(self.state()['player']['y'],position['y'])
        # Return to centre via actual movement, then travel through the maze.
        self.travel(0)
        for zoom in ['1.5','1.75']:
            self.page.select_option('#zoomSelect',zoom)
            self.travel(None)
            state=self.state()
            self.assertNotEqual(state['camera'],{'x':0,'y':0})
            canvas=self.page.locator('#maze').bounding_box()
            for axis,extent in [('x',canvas['width']),('y',canvas['height'])]:
                screen=(state['player'][axis]-state['camera'][axis])*float(zoom)
                self.assertGreaterEqual(screen,0)
                self.assertLessEqual(screen,extent)
            self.assert_no_scroll()
        before=self.state()
        self.page.keyboard.press('v')
        self.assertEqual(self.state()['player']['x'],before['player']['x'])
        self.assertEqual(self.state()['player']['y'],before['player']['y'])
        # S from rest reverses, then W brakes the reverse; steering rotates at rest.
        self.page.keyboard.down('s');self.page.evaluate('gameplayTest.step(12)');self.page.keyboard.up('s')
        self.assertLess(self.state()['speed'],0)
        self.page.keyboard.down('w');self.page.evaluate('gameplayTest.step(36)');self.page.keyboard.up('w')
        self.assertGreaterEqual(self.state()['speed'],0)
        self.page.evaluate("window.dispatchEvent(new Event('blur'))")
        angle=self.state()['angle']
        self.page.keyboard.down('a');self.page.evaluate('gameplayTest.step(30)');self.page.keyboard.up('a')
        self.assertLess(self.state()['angle'],angle)
        self.page.keyboard.down('d');self.page.evaluate('gameplayTest.step(30)');self.page.keyboard.up('d')
        self.assertAlmostEqual(self.state()['angle'],angle,places=5)
        # Aim into a perimeter wall using steering only; long acceleration stops at collision.
        self.page.click('#resetBtn')
        self.page.keyboard.down('a');self.page.evaluate('gameplayTest.step(120)');self.page.keyboard.up('a')
        self.page.keyboard.down('w');self.page.evaluate('gameplayTest.step(2400)');self.page.keyboard.up('w')
        blocked=self.state()
        self.assertLess(blocked['speed'],10)  # Forgiving collision may slide along a wall.
        self.assertAlmostEqual(min(blocked['player']['x'],blocked['player']['y']),48,delta=.6)
        self.page.evaluate('gameplayTest.step(120)')  # Released throttle coasts to rest.
        self.assertEqual(self.state()['speed'],0)
        self.assertGreater(self.state()['distance'],0)
        self.assert_no_scroll()


if __name__=='__main__':
    (ROOT/'test-results/phase-4').mkdir(parents=True,exist_ok=True)
    unittest.main(verbosity=2)
