"""Phase 5A.3: keyboard-driven free slash, unchanged light and deployment caching."""
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
import unittest

import browser_atmosphere as atmosphere
from browser_student import ROOT, fixture
from browser_visuals import VisualHarness

APPROVED=(ROOT/'tests/fixtures/visuals/phase-5a2-renderer.js').read_text()
assert hashlib.sha256(APPROVED.encode()).hexdigest()=='d990d4b61faefb942aafffe90a086f711798b46c343fd27a09e01faaf98c27af'
EPOCH=datetime(2026,10,21,tzinfo=timezone.utc)


class SlashTests(VisualHarness):
    artifact_directory=ROOT/'test-results/phase-5a3'
    bridge=(atmosphere.AtmosphereTests.bridge+APPROVED.replace('root.MazeRpgVisuals=','root.ApprovedPhase5a2Visuals=')+
            (ROOT/'tests/slash_probe.js').read_text())

    def setUp(self):
        if self._testMethodName=='test_real_keyboard_exploration_video':
            self.record_video_directory=self.artifact_directory/'video'
        super().setUp()

    def tearDown(self):
        video=self.page.video
        try:
            super().tearDown()
        finally:
            if video:
                video.save_as(str(self.artifact_directory/'explore-slash-question.webm'));video.delete()

    def prepare(self,clock=True):
        self.artifact_directory.mkdir(parents=True,exist_ok=True)
        if clock:self.page.clock.install(time=EPOCH)
        self.publish(fixture(1,'S01'),fixture(2,'S02'));self.open()
        if clock:self.page.clock.pause_at(EPOCH+timedelta(minutes=5))
        self.page.evaluate('slashTest.startFrames()')
        self.corridor()

    def state(self):
        return self.page.evaluate('slashTest.state()')

    def corridor(self,direction=None):
        path=self.page.evaluate('d=>slashTest.corridor(d)',direction)
        self.page.locator('#maze').focus();return path

    def mode(self,value):
        self.page.select_option('#atmosphereSelect',value,force=True)

    def save(self,name,data):
        (self.artifact_directory/name).write_text(json.dumps(data,indent=2),encoding='utf-8')

    def test_empty_corridor_intentional_presses_and_auto_repeat(self):
        self.prepare();before=self.state();self.assertIsNone(before['near'])
        for attempt in range(3):
            self.page.keyboard.press('e')
            if attempt==0:self.page.keyboard.press('e')  # Inside the 180 ms cooldown.
            self.page.clock.run_for(250)
            state=self.state();self.assertTrue(state['slashing']);self.assertIsNone(state['pending'])
            self.assertFalse(state['modal']);self.assertFalse(state['veil']);self.assertEqual(state['answers'],0)
            self.assertGreater(self.page.evaluate('slashTest.effect().pixels'),150)
            self.page.clock.run_for(400)
        calls=self.page.evaluate("slashTest.calls.filter(e=>e.event==='slash')")
        self.assertEqual(len(calls),3);self.assertTrue(all(c['args']==2 for c in calls))
        self.page.keyboard.down('e')
        self.page.evaluate("window.dispatchEvent(new KeyboardEvent('keydown',{key:'e',repeat:true,bubbles:true}))")
        self.page.clock.run_for(200);self.page.keyboard.down('e');self.page.keyboard.up('e')
        self.assertEqual(self.page.evaluate("slashTest.calls.filter(e=>e.event==='slash').length"),4)
        self.page.clock.run_for(500);after=self.state()
        for key in ['grid','done','failures','remaining','player']:self.assertEqual(after[key],before[key])
        self.assertFalse(after['slashing']);self.assertIsNone(after['pending'])

    def test_four_directions_real_e_frame_sequences(self):
        self.prepare();results=[]
        for direction,axis,sign in [('right',0,1),('left',0,-1),('down',1,1),('up',1,-1)]:
            self.corridor(direction);self.page.keyboard.press('e');frames=[]
            for target,delta in [(0,0),(120,120),(280,160),(460,180),(620,160)]:
                if delta:self.page.clock.run_for(delta)
                self.shot(f'{direction}-{target:03d}ms.png')
                effect=self.page.evaluate('slashTest.effect()');frames.append({'ms':target,**effect})
                self.assertFalse(self.state()['modal']);self.assertIsNone(self.state()['pending'])
                if 0<target<550:self.assertGreater(effect['pixels'],100)
                if target==280:
                    self.assertGreater(effect['offset'][axis]*sign,12)
                    self.closeup(f'{direction}-closeup.png')
                    if direction=='right':self.closeup('slash-closeup.png')
                if target==620:self.assertEqual(effect['pixels'],0)
            results.append({'direction':direction,'frames':frames})
        self.assertEqual(len({r['frames'][2]['mask'] for r in results}),4)
        self.save('direction-sequences.json',results)

    def closeup(self,name):
        box=self.page.locator('#maze').bounding_box();p=self.page.evaluate('refineTest.screenPlayer()')
        width=min(360,box['width']);height=min(300,box['height'])
        self.page.screenshot(path=str(self.artifact_directory/name),clip={
            'x':box['x']+max(0,min(box['width']-width,p['x']-width/2)),
            'y':box['y']+max(0,min(box['height']-height,p['y']-height/2)),
            'width':width,'height':height})

    def test_walking_slash_preserves_movement_collision_and_map_budget(self):
        self.prepare();path=self.corridor();before=self.state()
        self.page.keyboard.down(path['key']);self.page.keyboard.press('e');self.page.clock.run_for(250)
        moving=self.state();self.assertNotEqual([moving['player']['x'],moving['player']['y']],
                                              [before['player']['x'],before['player']['y']])
        self.assertTrue(moving['player']['moving']);self.assertTrue(moving['slashing']);self.assertIsNone(moving['pending'])
        self.page.keyboard.up(path['key']);self.page.clock.run_for(500)
        self.assertEqual(self.state()['grid'],before['grid']);self.assertEqual(self.state()['done'],before['done'])
        self.assertEqual(self.state()['remaining'],before['remaining']);self.assertFalse(self.state()['modal'])
        self.page.evaluate('slashTest.start()');self.page.keyboard.down('ArrowUp');self.page.keyboard.press('e')
        self.page.clock.run_for(1200);wall=self.state();self.page.clock.run_for(500)
        self.assertEqual(self.state()['player']['y'],wall['player']['y']);self.assertTrue(wall['positionSafe'])
        self.page.keyboard.up('ArrowUp')
        # Free E has no map charge/pause; an already open map follows its usual clock.
        self.corridor();self.page.evaluate('refineTest.map(true)');remaining=self.state()['remaining']
        self.page.keyboard.press('e');self.page.clock.run_for(300)
        self.assertAlmostEqual(remaining-self.state()['remaining'],300,delta=20)

    def test_completed_station_and_question_use_identical_slash(self):
        self.prepare();self.page.evaluate('slashTest.station(true)');self.page.locator('#maze').focus()
        self.page.keyboard.press('e');self.page.clock.run_for(250)
        complete=self.state();free=self.page.evaluate('slashTest.effect()')
        self.assertFalse(complete['modal']);self.assertIsNone(complete['pending']);self.assertTrue(complete['done'][0])
        self.page.keyboard.press('Escape');self.page.evaluate('slashTest.station(false)');self.page.locator('#maze').focus()
        self.page.keyboard.press('e');start=self.state();self.assertIsNotNone(start['pending'])
        self.page.clock.run_for(250);near=self.page.evaluate('slashTest.effect()')
        self.assertEqual(near['mask'],free['mask']);self.assertGreater(near['pixels'],150)
        self.shot('question-slash.png')
        self.assertFalse(self.state()['modal']);self.page.clock.run_for(300);self.assertFalse(self.state()['modal'])
        self.page.clock.run_for(100);self.assertTrue(self.state()['modal'])
        self.shot('question-open.png')
        self.assertEqual(len(self.page.evaluate("atmosphereTest.events.filter(e=>e.event==='question')")),1)
        calls=self.page.evaluate('slashTest.calls');self.assertEqual([c['args'] for c in calls if c['event']=='slash'],[2,2])
        self.assertEqual(len([c for c in calls if c['event']=='activation']),1)
        self.save('free-versus-question.json',{'free':free,'question':near,'calls':calls})

    def test_free_slash_cancels_at_lifecycle_boundaries(self):
        self.prepare()
        for action in ['escape','blur','hidden','restart','atmosphere','view','selector','unit']:
            with self.subTest(action=action):
                self.mode('strong');self.corridor();self.page.keyboard.press('e');self.page.clock.run_for(100)
                if action=='escape':self.page.keyboard.press('Escape')
                elif action=='blur':self.page.evaluate("window.dispatchEvent(new Event('blur'))")
                elif action=='hidden':self.page.evaluate('atmosphereTest.hidden(true)')
                elif action=='restart':self.page.locator('#resetBtn').evaluate('e=>e.click()')
                elif action=='atmosphere':self.mode('normal')
                elif action=='view':self.page.keyboard.press('v')
                else:
                    self.page.locator('#unitLabel').evaluate('e=>e.click()')
                    if action=='unit':
                        self.page.select_option('#unitSelect','S01');self.page.locator('#loadUnit').evaluate('e=>e.click()')
                        self.page.locator('#confirmSwitch').evaluate('e=>e.click()')
                        self.page.wait_for_function("document.querySelector('#unitLabel').textContent.startsWith('S01')")
                self.assertFalse(self.state()['slashing']);self.assertIsNone(self.state()['pending'])
                self.page.clock.run_for(700);self.assertFalse(self.state()['modal'])
                if action=='hidden':self.page.evaluate('atmosphereTest.hidden(false)')
                if action=='view':self.page.keyboard.press('v')
                if action=='selector':self.page.keyboard.press('Escape')

    def test_off_reduced_motion_and_drive_bypass_free_effect(self):
        self.prepare()
        for mode,reduced,drive in [('off',False,False),('normal',True,False),('strong',True,False),('strong',False,True)]:
            self.mode(mode);self.page.emulate_media(reduced_motion='reduce' if reduced else 'no-preference');self.corridor()
            if drive:self.page.keyboard.press('v')
            self.page.keyboard.press('e');self.page.clock.run_for(250)
            self.assertFalse(self.state()['slashing']);self.assertIsNone(self.state()['pending']);self.assertFalse(self.state()['modal'])
            if drive:self.page.keyboard.press('v')
        self.mode('strong');self.corridor();self.page.keyboard.press('e');self.page.clock.run_for(100)
        self.assertTrue(self.state()['slashing']);self.page.emulate_media(reduced_motion='reduce');self.page.clock.run_for(32)
        self.assertFalse(self.state()['slashing']);self.assertFalse(self.state()['modal'])
        self.page.emulate_media(reduced_motion='no-preference')
        for control in ['space','canvas','touch']:
            self.corridor()
            if control=='space':self.page.keyboard.press('Space')
            elif control=='canvas':self.page.locator('#maze').click()
            else:
                self.page.set_viewport_size({'width':390,'height':844});self.page.clock.run_for(32)
                self.page.locator('#touchInteract').click()
            self.page.clock.run_for(250)
            self.assertTrue(self.state()['slashing']);self.assertIsNone(self.state()['pending']);self.assertFalse(self.state()['modal'])
            self.assert_no_scroll();self.page.keyboard.press('Escape')

    def test_finish_stays_locked_and_delays_unlocked_dialog(self):
        self.prepare();self.page.evaluate('slashTest.finish()')
        self.page.locator('#maze').focus();self.page.keyboard.press('e');self.page.clock.run_for(250)
        self.assertTrue(self.state()['slashing']);self.assertFalse(self.state()['modal']);self.assertIsNone(self.state()['pending'])
        self.page.keyboard.press('Escape');self.page.evaluate('visualTest.passAll()');self.page.keyboard.press('e')
        self.assertIsNotNone(self.state()['pending']);self.page.clock.run_for(550);self.assertFalse(self.state()['modal'])
        self.page.keyboard.press('Escape');self.page.clock.run_for(750);self.assertFalse(self.state()['modal'])
        self.page.keyboard.press('e');self.page.clock.run_for(650)
        self.assertTrue(self.state()['modal']);self.assertEqual(self.state()['answers'],0)
        self.assertEqual(self.page.locator('#dialog a').get_attribute('href'),fixture(2,'S02')['googleFormUrl'])

    def test_approved_spotlight_is_pixel_identical(self):
        self.prepare();results=[]
        for width,height in [(1366,768),(1024,768),(390,844)]:
            self.page.set_viewport_size({'width':width,'height':height})
            self.page.clock.run_for(32)
            for mode in ['off','normal','strong']:
                for zoom in [1.5,1.75]:
                    for map_open in [False,True]:
                        with self.subTest(width=width,mode=mode,zoom=zoom,map=map_open):
                            difference=self.page.evaluate('a=>slashTest.lightingParity(...a)',[mode,zoom,map_open])
                            results.append({'viewport':[width,height],'mode':mode,'zoom':zoom,'mapOpen':map_open,'changedPixels':difference})
                            self.assertEqual(difference,0)
            self.assert_no_scroll()
        self.save('lighting-parity.json',results)

    def test_versioned_relative_assets_bypass_stale_script_cache(self):
        self.artifact_directory.mkdir(parents=True,exist_ok=True)
        self.publish(fixture(1,'S01'));self.server.cache_scripts=True;self.context.unroute('https://**/*')
        (self.site/'cache-probe.html').write_text('<title>Synthetic cache probe</title>')
        self.page.goto(self.url+'cache-probe.html')
        paths=['rpg-renderer.js','game.js']
        for name in paths:(self.site/'js'/name).write_text('/* synthetic old cached script */')
        old=self.page.evaluate("async paths=>Promise.all(paths.map(async name=>(await fetch('./js/'+name+'?v=5a2-old')).text()))",paths)
        for name in paths:(self.site/'js'/name).write_bytes((ROOT/'student/js'/name).read_bytes())
        cached=self.page.evaluate("async paths=>Promise.all(paths.map(async name=>(await fetch('./js/'+name+'?v=5a2-old')).text()))",paths)
        self.assertEqual(cached,old)
        self.page.goto(self.url+'index.html?v=5a3-1')
        self.page.wait_for_function("!document.querySelector('#unitSelect').disabled")
        self.load('S01')
        versions=self.page.evaluate("({game:document.documentElement.dataset.gameRelease,renderer:MazeRpgVisuals.release,scripts:Array.from(document.scripts,s=>s.getAttribute('src'))})")
        self.assertEqual(versions['game'],'5a3-1');self.assertEqual(versions['renderer'],'5a3-1')
        for name in paths:
            self.assertIn('./js/'+name+'?v=5a3-1',versions['scripts'])
            self.assertTrue(any(u.endswith('/js/'+name+'?v=5a3-1') for u in self.requests))
        self.assert_no_scroll();self.save('deployment-cache.json',versions)

    def test_real_keyboard_exploration_video(self):
        self.prepare(clock=False);path=self.corridor();records=[]
        self.shot('exploration-start.png');self.page.wait_for_timeout(250)
        for _ in range(3):
            self.page.keyboard.press('e');self.page.wait_for_timeout(650)
            action=self.page.evaluate("slashTest.calls.filter(e=>e.event==='slash').at(-1)")
            self.assertIn('sample',action);self.assertGreater(action['sample']['pixels'],150)
            self.assertFalse(action['sample']['pending']);self.assertFalse(action['sample']['modal']);records.append(action)
        # One protocol command releases both real keys after a bounded hold,
        # even if the Python host is stalled before it can send another command.
        hold=math.ceil((path['distance']-20)*1000/175)
        self.page.keyboard.press(path['key']+'+e',delay=hold)
        for _ in range(8):
            near=self.state()['near']
            if near and near['type']=='question' and near['index']==0:break
            self.page.keyboard.press(path['key'],delay=80)
        else:self.fail('Real walking did not reach synthetic Q1')
        walking=self.page.evaluate("slashTest.calls.filter(e=>e.event==='slash').at(-1)")
        self.assertTrue(walking['sample']['player']['moving']);self.assertFalse(walking['sample']['pending'])
        self.page.keyboard.press('e');self.page.wait_for_selector('[data-answer]')
        question=self.page.evaluate("slashTest.calls.filter(e=>e.event==='slash').at(-1)")
        self.assertTrue(question['sample']['pending']);self.assertFalse(question['sample']['modal'])
        self.assertGreater(question['sample']['pixels'],150)
        self.page.wait_for_timeout(400);self.shot('real-question-open.png')
        self.assertEqual(self.page.locator('[data-answer]').count(),len(fixture(2,'S02')['questions'][0]['options']))
        self.save('exploration-recording.json',{'path':path,'freePresses':records,'walking':walking,'question':question,'calls':self.page.evaluate('slashTest.calls'),
                                             'events':self.page.evaluate('atmosphereTest.events')})


if __name__=='__main__':
    unittest.main(verbosity=2)
