"""Phase 5A.2 real-input timing, cancellation, preferences and rendering evidence."""
from datetime import datetime, timedelta, timezone
import hashlib
import json
import statistics
import unittest

from browser_visuals import VisualHarness, BRIDGE
from browser_refinement import PRIOR, PROBE
from browser_student import ROOT, fixture

PREVIOUS = (ROOT/'tests/fixtures/visuals/phase-5a1-renderer.js').read_text()
assert hashlib.sha256(PREVIOUS.encode()).hexdigest() == '0c9e484cabace70fbde80b5e815f38906a9b5ea8f66dc08fa1f7096e6bf17afd'
ATMOSPHERE_PROBE = (ROOT/'tests/atmosphere_probe.js').read_text()
EPOCH = datetime(2026,10,21,tzinfo=timezone.utc)


class AtmosphereTests(VisualHarness):
    artifact_directory = ROOT/'test-results/phase-5a2'
    bridge = (BRIDGE + PRIOR.replace('root.MazeRpgVisuals=', 'root.PreviousPhase5aVisuals=') +
              PREVIOUS.replace('root.MazeRpgVisuals=', 'root.PreviousRefinedVisuals=') + PROBE + ATMOSPHERE_PROBE)

    def setUp(self):
        if self._testMethodName == 'test_real_e_temporal_screenshots_and_video':
            self.record_video_directory = self.artifact_directory/'video'
        super().setUp()

    def tearDown(self):
        video = self.page.video
        try:
            super().tearDown()
        finally:
            if video:
                video.save_as(str(self.artifact_directory/'interaction-strong.webm'))
                video.delete()

    def prepare(self, clock=False):
        self.artifact_directory.mkdir(parents=True,exist_ok=True)
        if clock:
            self.page.clock.install(time=EPOCH)
        self.publish(fixture(1,'S01'),fixture(2,'S02'))
        self.open()
        if clock:
            self.page.clock.pause_at(EPOCH+timedelta(minutes=5))

    def approach(self):
        self.page.evaluate('visualTest.approach()')
        self.page.locator('#maze').focus()

    def snapshot(self):
        return self.page.evaluate('atmosphereTest.state()')

    def choose_mode(self, mode):
        # Desktop HUD and drawer are two views of one real cosmetic control.
        self.page.select_option('#atmosphereSelect', mode, force=True)

    def test_modes_default_persistence_and_off_pixel_parity(self):
        self.prepare()
        self.assertEqual(self.snapshot()['atmosphere'],'strong')
        self.page.evaluate('visualTest.passFirst()')
        before = self.page.evaluate('visualTest.state()')
        for mode in ['off','normal','strong']:
            self.choose_mode(mode)
            self.assertEqual(self.page.input_value('#drawerAtmosphereSelect'),mode)
            self.assertEqual(self.page.evaluate('visualTest.state()'),before)
            if mode=='off':self.assertEqual(self.page.evaluate('atmosphereTest.offParity()'),0)
        self.choose_mode('normal')
        self.page.reload()
        self.page.wait_for_function("!document.querySelector('#unitSelect').disabled")
        self.assertEqual(self.page.input_value('#atmosphereSelect'),'normal')
        self.assertEqual(self.page.evaluate('Object.fromEntries(Object.entries(localStorage))'),{'emi-maze.atmosphere':'normal'})
        self.page.evaluate("localStorage.setItem('emi-maze.atmosphere','invalid')")
        self.page.reload()
        self.page.wait_for_function("!document.querySelector('#unitSelect').disabled")
        self.assertEqual(self.page.input_value('#atmosphereSelect'),'strong')

    def test_storage_failure_remains_playable(self):
        self.page.add_init_script("Storage.prototype.getItem=Storage.prototype.setItem=()=>{throw new DOMException('Blocked','SecurityError')}")
        self.prepare()
        self.assertEqual(self.snapshot()['atmosphere'],'strong')
        self.choose_mode('off');self.approach();self.page.keyboard.press('e')
        self.assertTrue(self.snapshot()['modal'])

    def test_lighting_contrast_center_zoom_camera_and_teacher_map(self):
        self.prepare()
        for zoom,x,y,camera in [(1.5,260,200,{'x':100,'y':80}),
                               (1.75,340,230,{'x':140,'y':90}),
                               (1.5,350,230,{'x':235,'y':120})]:
            samples={m:self.page.evaluate('a=>atmosphereTest.light(...a)',[m,zoom,x,y,camera]) for m in ['off','normal','strong']}
            self.assertEqual(samples['off']['near'],1);self.assertEqual(samples['off']['far'],1)
            self.assertGreater(samples['normal']['near'],.97);self.assertGreater(samples['strong']['near'],.97)
            self.assertGreater(samples['strong']['far'],.45)
            self.assertGreater(samples['normal']['far'],samples['strong']['far']+.1)
            soft=self.page.evaluate('a=>atmosphereTest.light(...a)',['strong',zoom,x,y,camera,True])
            self.assertGreater(soft['far'],samples['strong']['far']+.1)
        a=self.page.evaluate("atmosphereTest.light('strong',1.5,180,210,{x:100,y:80})")
        b=self.page.evaluate("atmosphereTest.light('strong',1.5,400,210,{x:100,y:80})")
        self.assertGreater(a['left'],b['left']+.1);self.assertGreater(b['right'],a['right']+.1)

    def test_real_e_temporal_screenshots_and_video(self):
        self.prepare(clock=True);self.approach()
        self.page.keyboard.press('e');start=self.snapshot()['pending']['start'];records=[]
        for target,delta in [(0,0),(100,100),(250,150),(400,150),(650,250)]:
            if delta:self.page.clock.run_for(delta)
            state=self.snapshot();records.append({'targetMs':target,'elapsedMs':state['now']-start,'state':state})
            self.shot(f'strong-E-{target:03d}ms.png')
            if target<600:
                self.assertIsNotNone(state['pending']);self.assertFalse(state['modal']);self.assertFalse(state['veil'])
                self.assertEqual(state['answers'],0)
            else:
                self.assertIsNone(state['pending']);self.assertTrue(state['modal'])
            if target==250:self.assertGreater(self.page.evaluate('atmosphereTest.effectPixels()'),100)
        events=self.page.evaluate('atmosphereTest.events')
        questions=[e for e in events if e['event']=='question']
        self.assertEqual(len(questions),1);self.assertGreaterEqual(questions[0]['time']-start,600)
        (self.artifact_directory/'strong-sequence.json').write_text(json.dumps({'frames':records,'events':events},indent=2))

    def test_live_e_reveals_once_after_full_sequence(self):
        self.prepare();self.approach()
        self.page.keyboard.down('ArrowRight');self.page.evaluate('visualTest.step(1)')
        self.page.keyboard.up('ArrowRight');self.page.evaluate('visualTest.step(1)')
        self.page.keyboard.press('e');self.page.keyboard.press('e')
        self.page.wait_for_selector('[data-answer]')
        events=self.page.evaluate('atmosphereTest.events')
        press=next(e for e in events if e['event']=='E')
        questions=[e for e in events if e['event']=='question']
        self.assertIsNotNone(press['pending']);self.assertFalse(press['modal']);self.assertFalse(press['veil'])
        self.assertEqual(len(questions),1)
        elapsed=questions[0]['time']-press['pending']['start']
        self.assertGreaterEqual(elapsed,600)
        self.assertEqual(press['player']['dir'],'right')
        (self.artifact_directory/'live-sequence.json').write_text(json.dumps({'revealMs':elapsed,'events':events},indent=2))

    def test_normal_and_strong_timing_repeated_e_and_freeze(self):
        self.prepare(clock=True);measurements=[]
        for mode,total in [('normal',460),('strong',600)]:
            self.choose_mode(mode);self.approach();self.page.evaluate('refineTest.map(true)')
            self.page.keyboard.press('e');before=self.snapshot()
            for key in ['e','e','ArrowLeft','w']:self.page.keyboard.press(key)
            self.page.clock.run_for(total-50);self.page.evaluate('atmosphereTest.advanceGameplay()')
            during=self.snapshot();self.assertFalse(during['modal']);self.assertFalse(during['veil'])
            self.assertEqual(during['player'],before['player']);self.assertEqual(during['remaining'],before['remaining'])
            self.page.clock.run_for(100)
            self.assertTrue(self.snapshot()['modal']);self.assertIsNone(self.snapshot()['pending'])
            self.page.clock.run_for(700)
            questions=self.page.evaluate("atmosphereTest.events.filter(e=>e.event==='question')")
            self.assertEqual(len(questions),1)
            self.assertGreaterEqual(questions[0]['time']-before['pending']['start'],total)
            measurements.append({'mode':mode,'intendedRevealMs':total,
                                 'actualRevealMs':questions[0]['time']-before['pending']['start'],
                                 'before':before,'during':during})
            self.page.keyboard.press('Escape');self.page.evaluate('atmosphereTest.events.length=0;refineTest.map(false)')
        (self.artifact_directory/'timing-and-freeze.json').write_text(json.dumps(measurements,indent=2))

    def test_pending_cancellation_boundaries_and_new_unit(self):
        self.prepare(clock=True)
        actions={
            'escape':lambda:self.page.keyboard.press('Escape'),
            'escape-select':lambda:(self.page.locator('#zoomSelect').focus(),self.page.keyboard.press('Escape')),
            'blur':lambda:self.page.evaluate("window.dispatchEvent(new Event('blur'))"),
            'hidden':lambda:self.page.evaluate('atmosphereTest.hidden(true)'),
            'restart':lambda:self.page.locator('#resetBtn').evaluate('el=>el.click()'),
            'mode':lambda:self.choose_mode('off'),
            'drive':lambda:self.page.keyboard.press('v'),
            'selector':lambda:self.page.locator('#unitLabel').evaluate('el=>el.click()'),
        }
        for name,action in actions.items():
            with self.subTest(action=name):
                self.choose_mode('strong');self.approach();self.page.keyboard.press('e')
                self.page.clock.run_for(100);action();self.assertIsNone(self.snapshot()['pending'])
                if name=='escape':
                    self.page.evaluate("window.dispatchEvent(new KeyboardEvent('keydown',{key:'e',repeat:true,bubbles:true}))")
                self.page.clock.run_for(750)
                self.assertFalse(self.snapshot()['modal']);self.assertFalse(self.snapshot()['veil'])
                self.assertEqual(self.page.locator('[data-answer]').count(),0)
                if name=='hidden':self.page.evaluate('atmosphereTest.hidden(false)')
                if name=='drive':self.page.keyboard.press('v')
                if name=='selector':self.page.keyboard.press('Escape')
        self.choose_mode('strong');self.approach();self.page.keyboard.press('e')
        self.page.locator('#unitLabel').evaluate('el=>el.click()')
        self.page.select_option('#unitSelect','S01')
        self.page.locator('#loadUnit').evaluate('el=>el.click()')
        self.page.locator('#confirmSwitch').evaluate('el=>el.click()')
        self.page.wait_for_function("document.querySelector('#unitLabel').textContent.startsWith('S01')")
        self.page.clock.run_for(750)
        state=self.snapshot();self.assertEqual(state['unit'],'S01');self.assertFalse(state['modal'])
        self.assertEqual(state['done'],[False]*4);self.assertEqual(state['remaining'],30000)

    def test_off_reduced_motion_and_driving_are_immediate(self):
        self.prepare(clock=True)
        for mode,reduced,drive in [('off',False,False),('strong',True,False),('normal',False,True),('strong',False,True)]:
            self.choose_mode(mode);self.page.emulate_media(reduced_motion='reduce' if reduced else 'no-preference')
            self.approach()
            if drive:self.page.keyboard.press('v')
            self.page.keyboard.press('e');state=self.snapshot()
            self.assertTrue(state['modal']);self.assertIsNone(state['pending'])
            self.assertGreater(state['answers'],0);self.page.keyboard.press('Escape')
            if drive:self.page.keyboard.press('v')
        # A preference change during a pending animation must not wait on a skipped effect.
        self.approach();self.page.keyboard.press('e');self.page.clock.run_for(100)
        self.assertIsNotNone(self.snapshot()['pending'])
        changed_at=self.snapshot()['now']
        self.page.emulate_media(reduced_motion='reduce')
        self.assertTrue(self.page.evaluate("matchMedia('(prefers-reduced-motion: reduce)').matches"))
        # Chromium may deliver the media-query change on its next rendering
        # opportunity after the protocol response. The fake clock is paused;
        # permit two frames, rather than waiting out the remaining 500 ms cue.
        self.page.clock.run_for(32)
        state=self.snapshot()
        self.assertTrue(state['modal']);self.assertIsNone(state['pending'])
        question=self.page.evaluate("atmosphereTest.events.filter(e=>e.event==='question').at(-1)")
        self.assertGreaterEqual(question['time'],changed_at)
        self.assertLessEqual(question['time']-changed_at,32)

    def test_matched_modes_viewports_and_accessible_controls(self):
        self.prepare()
        for width,height in [(1366,768),(1024,768),(390,844)]:
            self.page.set_viewport_size({'width':width,'height':height});self.settle_layout();self.approach()
            before=self.page.evaluate('visualTest.state()')
            for mode in ['off','normal','strong']:
                if width==1366:
                    self.page.select_option('#atmosphereSelect',mode)
                else:
                    self.page.click('#panelToggle');self.page.select_option('#drawerAtmosphereSelect',mode);self.page.click('#panelClose')
                    self.page.wait_for_function("getComputedStyle(document.querySelector('#sidePanel')).opacity==='0'")
                self.page.evaluate('visualTest.draw(12)')
                self.assertEqual(self.page.evaluate('visualTest.state()'),before);self.assert_no_scroll()
                self.shot(f'mode-{mode}-{width}.png')
                if width==1366:self.page.evaluate('m=>atmosphereTest.rememberFrame(m)',mode)
            if width==1366:
                for control in ['#atmosphereSelect','#unitLabel','#modeToggle','#panelToggle','#mapToggle','#resetBtn']:
                    box=self.page.locator(control).bounding_box();self.assertGreaterEqual(box['x'],0)
                    self.assertLessEqual(box['x']+box['width'],width)
        self.page.set_viewport_size({'width':1460,'height':800})
        self.page.evaluate('atmosphereTest.modeSheet()')
        self.page.locator('#visualSheet').screenshot(path=str(self.artifact_directory/'mode-comparison.png'))
        self.page.evaluate('visualTest.removeSheet()')

    def test_modes_and_repeated_effect_performance(self):
        self.prepare();results=[]
        for renderer,mode,actions in [('phase5a1','strong',False),('current','off',False),('current','normal',False),
                                       ('current','strong',False),('current','strong',True)]:
            self.choose_mode(mode)
            for width,height in [(1366,768),(1024,768),(390,844)]:
                self.page.set_viewport_size({'width':width,'height':height});self.settle_layout();self.approach()
                trials=[self.page.evaluate('a=>atmosphereTest.benchmark(...a)',[renderer,actions]) for _ in range(3)]
                result=dict(trials[0]);result['trials']=trials
                for key in ['meanRenderMs','p95RenderMs','observedFps']:result[key]=statistics.median(t[key] for t in trials)
                result.update(renderer=renderer,mode=mode,actions=actions,browser=self.browser.version);results.append(result)
        (self.artifact_directory/'performance.json').write_text(json.dumps(results,indent=2))


if __name__=='__main__':
    unittest.main(verbosity=2)
