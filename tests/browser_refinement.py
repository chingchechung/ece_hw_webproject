"""Synthetic 2D lighting/action regressions and paired Phase 5A measurements."""
import hashlib
import json
import statistics
import unittest

from browser_visuals import VisualHarness, BRIDGE
from browser_student import ROOT, fixture

PRIOR = (ROOT / 'tests/fixtures/visuals/phase-5a-renderer.js').read_text()
assert hashlib.sha256(PRIOR.encode()).hexdigest() == 'fee5cbe020767406b13b7b77df89390773c61e16e01e6eddd31f274e166dc1d8'
PROBE = (ROOT / 'tests/refinement_probe.js').read_text()


class RefinementTests(VisualHarness):
    artifact_directory = ROOT / 'test-results/phase-5a-refinement'
    bridge = BRIDGE + PRIOR.replace('root.MazeRpgVisuals=', 'root.PreviousPhase5aVisuals=') + PROBE

    def open(self, hooks=True, index=False):
        def renderer(route):
            if getattr(self, 'previous', False):
                route.fulfill(body=PRIOR, content_type='application/javascript')
            else:
                route.continue_()
        self.page.route('**/js/rpg-renderer.js*', renderer)
        super().open(hooks, index)

    def resize(self, width, height):
        self.page.set_viewport_size({'width': width, 'height': height})
        self.settle_layout()
        self.page.evaluate('visualTest.overview()')

    def test_focus_follows_avatar_zoom_camera_and_preserves_readability(self):
        self.prepare()
        for zoom, x, y, camera in [(1.5,260,200,{'x':100,'y':80}),
                                    (1.75,340,230,{'x':140,'y':90}),
                                    (1.5,350,230,{'x':235,'y':120})]:
            result = self.page.evaluate('a=>refineTest.focus(...a)', [zoom,x,y,camera])
            self.assertGreater(result['near'], .97)
            self.assertGreater(result['far'], .60)
            self.assertLess(result['far'], .85)
            softened = self.page.evaluate('a=>refineTest.focus(...a)', [zoom,x,y,camera,True])
            self.assertGreater(softened['far'], result['far'])
        a = self.page.evaluate('refineTest.focus(1.5,180,210,{x:100,y:80})')
        b = self.page.evaluate('refineTest.focus(1.5,400,210,{x:100,y:80})')
        self.assertGreater(a['left'], b['left']+.04)
        self.assertGreater(b['right'], a['right']+.04)

    def test_four_direction_swipe_expiry_and_reduced_motion(self):
        self.prepare()
        hashes = []
        for direction, axis, sign in [('right',0,1),('left',0,-1),('down',1,1),('up',1,-1)]:
            result = self.page.evaluate('d=>refineTest.swipe(d)', direction)
            self.assertTrue(result['started'])
            self.assertGreater(result['changed'], 40)
            self.assertGreater(result['offset'][axis]*sign, 12)
            self.assertEqual(result['expired'], result['clean'])
            hashes.append(result['during'])
        self.assertEqual(len(set(hashes)), 4)
        self.page.emulate_media(reduced_motion='reduce')
        reduced = self.page.evaluate("refineTest.swipe('right')")
        self.assertTrue(reduced['started'])
        self.assertGreater(reduced['changed'], 40)
        self.assertEqual(reduced['expired'], reduced['clean'])

    def test_e_pending_sequence_cancels_without_late_dialog(self):
        self.prepare()
        self.page.evaluate('visualTest.approach()')
        before = json.loads(self.page.evaluate('visualTest.state()'))
        self.page.locator('#maze').focus()
        self.page.keyboard.press('e')
        modal = self.page.evaluate('refineTest.modal()')
        self.assertFalse(modal['open']);self.assertTrue(modal['cue'])
        self.assertFalse(self.page.evaluate('refineTest.keyModal.open'))
        self.assertEqual(modal['pendingIndex'], 0)
        self.assertEqual(self.page.locator('[data-answer]').count(), 0)
        self.assertFalse(any(modal['pressed'].values()))
        self.page.keyboard.press('e')  # Held/repeated E cannot reopen or move.
        self.assertEqual(self.page.evaluate('refineTest.modal().pendingIndex'), 0)
        self.page.keyboard.press('Escape')
        self.assertFalse(self.page.evaluate('refineTest.modal().open'))
        self.assertFalse(self.page.evaluate('refineTest.modal().cue'))
        self.page.wait_for_timeout(700)
        self.assertFalse(self.page.is_visible('#veil'))
        self.assertEqual(json.loads(self.page.evaluate('visualTest.state()')), before)
        self.page.keyboard.press('e')
        self.page.wait_for_selector('[data-answer]')
        self.assertTrue(self.page.evaluate('refineTest.modal().open'))
        self.page.click('#dialogClose')
        self.page.keyboard.press('v')
        self.page.keyboard.press('e')
        self.assertTrue(self.page.evaluate('refineTest.modal().open'))
        self.assertFalse(self.page.evaluate('refineTest.modal().cue'))

    def test_station_finish_labels_and_review_artifacts(self):
        self.prepare()
        labels = self.page.evaluate('refineTest.labelCheck()')
        self.assertEqual(labels['before'], labels['after'])
        # Completed stations stay calm while incomplete devices and exits animate.
        hashes = self.page.evaluate('refineTest.states()')
        self.assertNotEqual(*hashes['idle']);self.assertEqual(*hashes['passed'])
        self.assertNotEqual(hashes['locked'], hashes['unlocked'])
        self.page.evaluate('visualTest.approach()');self.shot('station-before.png')
        self.page.locator('#maze').focus();self.page.keyboard.press('e')
        label = fixture(2,'S02')['questions'][0]['correctOptions'][-1]
        self.page.click(f'[data-answer="{label}"]');self.page.click('#continueMaze')
        self.page.evaluate('visualTest.draw(0)');self.shot('station-after.png')
        self.page.evaluate('visualTest.parkExit()');self.shot('finish-locked.png')
        self.page.evaluate('visualTest.passAll()');self.shot('finish-unlocked.png')
        for direction in ['right','left','down','up']:
            self.page.evaluate('d=>refineTest.stage(d)', direction)
            self.shot(f'swipe-{direction}.png')

    def test_reduced_motion_touch_map_and_mode_round_trip(self):
        self.prepare()
        self.resize(390,844)
        self.page.emulate_media(reduced_motion='reduce')
        self.page.evaluate('visualTest.approach()')
        self.page.click('#touchInteract')
        self.assertTrue(self.page.evaluate('refineTest.modal().cue'))
        self.page.wait_for_selector('[data-answer]')
        self.assertTrue(self.page.evaluate('refineTest.modal().open'))
        self.assertFalse(self.page.evaluate('refineTest.modal().cue'))
        self.page.click('#dialogClose')
        self.page.evaluate('refineTest.map(true)');self.shot('teacher-map-softened.png')
        self.page.evaluate('refineTest.map(false)')
        for zoom in ['1.5','1.75']:
            self.page.select_option('#zoomSelect', zoom)
            self.page.evaluate('visualTest.draw(0)');self.assert_no_scroll()
        self.shot('small-screen-175.png')
        before = json.loads(self.page.evaluate('visualTest.state()'))
        self.page.keyboard.press('v');self.page.evaluate('visualTest.draw(0)')
        self.page.keyboard.press('v');self.page.evaluate('visualTest.draw(0)')
        after = json.loads(self.page.evaluate('visualTest.state()'))
        before['player']['dir'] = after['player']['dir']
        self.assertEqual(after,before)

    def test_paired_phase5a_performance_and_viewport_artifacts(self):
        self.artifact_directory.mkdir(parents=True, exist_ok=True)
        self.publish(fixture(2,'S02'));results=[]
        for previous, interactions in [(True,False),(False,False),(False,True)]:
            self.previous=previous;self.open()
            for width,height in [(1366,768),(1024,768),(390,844)]:
                self.resize(width,height)
                self.page.evaluate('visualTest.approach()')
                trials=[self.page.evaluate('i=>refineTest.benchmark(i)', interactions) for _ in range(3)]
                result=dict(trials[0]);result['trials']=trials
                for key in ['meanRenderMs','p95RenderMs','observedFps']:
                    result[key]=statistics.median(t[key] for t in trials)
                result.update(renderer='phase5a' if previous else 'refined',browser=self.browser.version)
                results.append(result)
                self.shot(f"{'before' if previous else 'after'}-{'actions-' if interactions else ''}{width}.png")
                self.assert_no_scroll()
        (self.artifact_directory/'performance.json').write_text(json.dumps(results,indent=2))
        self.resize(1366,768)
        self.page.evaluate('visualTest.approach()')
        box=self.page.locator('#maze').bounding_box()
        player=self.page.evaluate('refineTest.screenPlayer()')
        self.page.screenshot(path=str(self.artifact_directory/'player-focus.png'),clip={
            'x':max(box['x'],min(box['x']+box['width']-640,box['x']+player['x']-320)),
            'y':max(box['y'],min(box['y']+box['height']-480,box['y']+player['y']-240)),
            'width':640,'height':480})


if __name__ == '__main__':
    unittest.main(verbosity=2)
