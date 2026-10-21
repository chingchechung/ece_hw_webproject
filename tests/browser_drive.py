"""Synthetic Phase 5B geometry, visual evidence, control replay and benchmarks."""
import json
import statistics
import unittest

from browser_student import ROOT, fixture
from browser_visuals import VisualHarness, BRIDGE
from drive_reference import DRIVE_BRIDGE


class DrivingVisualTests(VisualHarness):
    artifact_directory=ROOT/'test-results/phase-5b'
    bridge=(BRIDGE+(ROOT/'tests/gameplay_driver.js').read_text()+DRIVE_BRIDGE+
            (ROOT/'tests/drive_probe.js').read_text())

    def setUp(self):
        if self._testMethodName=='test_real_browser_driving_video':
            self.record_video_directory=self.artifact_directory/'video'
        super().setUp()

    def tearDown(self):
        video=self.page.video
        try:
            super().tearDown()
        finally:
            if video:
                video.save_as(str(self.artifact_directory/'driving-keyboard-demo.webm'));video.delete()

    def prepare(self):
        self.artifact_directory.mkdir(parents=True,exist_ok=True)
        self.publish(fixture(1,'S01'),fixture(2,'S02'));self.open();self.page.keyboard.press('v')

    def state(self):
        return self.page.evaluate('driveTest.state()')

    def stage(self,name):
        return self.page.evaluate('name=>driveTest.stage(name)',name)

    def save(self,name,value):
        (self.artifact_directory/name).write_text(json.dumps(value,indent=2),encoding='utf-8')

    def test_matched_before_after_scene_gallery(self):
        self.prepare();scenes=[]
        names=['straight','left','right','corner','t','four','near-wall','station-far','station-near',
               'station-passed','finish-locked','finish-unlocked']
        for name in names:
            with self.subTest(scene=name):
                pose=self.stage(name);state=self.page.evaluate('driveTest.snapshot()')
                self.page.evaluate('driveTest.render(true,0)');before=self.page.evaluate('visualTest.pixels()');self.shot(name+'-before.png')
                self.assertEqual(self.page.evaluate('driveTest.snapshot()'),state)
                self.page.evaluate('driveTest.render(false,0)');after=self.page.evaluate('visualTest.pixels()');self.shot(name+'-after.png')
                self.assertNotEqual(before,after);self.assertEqual(self.page.evaluate('driveTest.snapshot()'),state)
                scenes.append(pose);self.assert_no_scroll()
        self.page.set_viewport_size({'width':390,'height':844});self.settle_layout();pose=self.stage('four')
        for previous in [True,False]:
            self.page.evaluate('p=>driveTest.render(p,0)',previous);self.shot('small-'+('before' if previous else 'after')+'.png')
            self.assert_no_scroll()
        scenes.append({'viewport':[390,844],**pose});self.save('scene-poses.json',scenes)

    def test_road_markings_match_real_grid_all_sizes_four_five_questions(self):
        self.prepare();results=[]
        for unit in ['S01','S02']:
            self.page.click('#unitLabel');self.load(unit)
            for width,height in [(25,19),(21,15),(17,13),(13,9)]:
                self.page.evaluate('a=>driveTest.newMaze(...a)',[width,height])
                result=self.page.evaluate('driveTest.roadAgreement()')
                self.assertGreater(result['checked'],300);self.assertEqual(result['questions'],4 if unit=='S01' else 5)
                results.append(result)
        self.save('road-mask-agreement.json',results)

    def test_wall_depth_matches_collision_rays_and_rotation(self):
        self.prepare();results=[]
        for scene in ['straight','left','right','corner','t','four','near-wall']:
            self.stage(scene);self.assertLess(self.page.evaluate('driveTest.depthAgreement()'),.005)
            results.append({'scene':scene,'maxDepthError':self.page.evaluate('driveTest.depthAgreement()')})
        self.save('wall-depth-agreement.json',results)

    def test_question_projection_depth_and_wall_occlusion(self):
        self.prepare();projections=[]
        for distance in [140,100,60]:
            self.page.evaluate('d=>driveTest.station(0,d)',distance)
            ob=self.page.evaluate('driveTest.projections()[0]')
            self.assertIsNotNone(ob['projection']);self.assertGreater(ob['projection']['w'],8)
            self.shot(f'station-{distance}-after.png');projections.append(ob)
        widths=[x['projection']['w'] for x in projections]
        self.assertLess(widths[0],widths[1]);self.assertLess(widths[1],widths[2])
        self.stage('near-wall')
        hidden=self.page.evaluate('driveTest.hiddenObject()')
        self.assertIsNone(hidden);self.save('station-projections.json',projections)

    def test_station_identifiers_completion_and_finish_assets(self):
        self.prepare();self.stage('station-near');assets=self.page.evaluate('driveTest.objectAssets()')
        for label in assets['labels']:
            self.assertEqual(label['before'],label['after']);self.assertTrue(any(label['before']))
            self.assertNotEqual(*label['hashes'])
        self.assertEqual(len({tuple(q['before']) for q in assets['labels']}),5)
        self.assertNotEqual(*assets['finish']);self.save('checkpoint-labels.json',assets)

    def test_frozen_and_new_renderer_preserve_identical_control_replays(self):
        self.prepare();results=[]
        for scene in ['straight','near-wall']:
            self.stage(scene);before=self.page.evaluate('driveTest.replay(true)');after=self.page.evaluate('driveTest.replay(false)')
            self.assertEqual(before,after)
            self.assertTrue(any(f['speed']<0 for f in after));self.assertTrue(any(f['speed']>0 for f in after))
            results.append({'scene':scene,'frames':len(after),'matched':True,'trace':after})
        self.save('control-replay.json',results)

    def test_real_steering_and_view_switch_preserve_progress(self):
        self.prepare();self.stage('t');before=self.state()
        self.page.keyboard.down('d');self.page.evaluate('gameplayTest.step(45)');self.page.keyboard.up('d')
        after=self.state();self.assertAlmostEqual(after['angle']-before['angle'],1.05,places=6)
        self.assertEqual(after['player']['x'],before['player']['x']);self.assertEqual(after['player']['y'],before['player']['y'])
        self.assertEqual(after['done'],before['done']);self.assertEqual(after['remaining'],before['remaining'])
        self.page.keyboard.press('v');self.page.evaluate('visualTest.draw(0)');self.shot('switch-2d.png')
        self.page.keyboard.press('v');self.page.evaluate('visualTest.draw(0)');self.shot('switch-drive.png')
        returned=self.state();self.assertEqual(returned['done'],after['done']);self.assertEqual(returned['remaining'],after['remaining'])
        self.assertEqual(returned['player']['x'],after['player']['x']);self.assertEqual(returned['player']['y'],after['player']['y'])
        self.page.keyboard.down('s');self.page.evaluate('gameplayTest.step(90)');self.page.keyboard.up('s')
        self.assertLess(self.state()['speed'],0);self.page.evaluate('driveTest.render(false,0)');self.shot('reverse.png')
        self.page.keyboard.down('w');self.page.evaluate('gameplayTest.step(90)');self.page.keyboard.up('w')
        self.assertGreater(self.state()['speed'],0);self.page.evaluate('driveTest.render(false,0)');self.shot('acceleration.png')

    def test_reduced_motion_has_steady_lights_and_cockpit(self):
        self.prepare();self.stage('station-near');self.page.evaluate('driveTest.motionPose()')
        self.page.emulate_media(reduced_motion='reduce')
        self.page.evaluate('driveTest.render(false,0)');a=self.page.evaluate('visualTest.pixels()')
        self.page.evaluate('driveTest.render(false,1)');b=self.page.evaluate('visualTest.pixels()')
        self.assertEqual(a,b);self.shot('reduced-motion.png')
        self.page.emulate_media(reduced_motion='no-preference')
        self.page.evaluate('driveTest.render(false,0)');a=self.page.evaluate('visualTest.pixels()')
        self.page.evaluate('driveTest.render(false,1)');b=self.page.evaluate('visualTest.pixels()')
        self.assertNotEqual(a,b)

    def test_teacher_map_is_unchanged_and_counts_only_viewing(self):
        self.prepare();self.stage('straight');self.page.evaluate('driveTest.map(true)')
        self.page.evaluate('driveTest.render(true,0)');before=self.page.evaluate('driveTest.minimap()')
        self.page.evaluate('driveTest.render(false,0)');after=self.page.evaluate('driveTest.minimap()')
        self.assertEqual(before,after);self.shot('teacher-map.png')
        self.page.evaluate('gameplayTest.step(120)');self.assertAlmostEqual(self.state()['remaining'],29000,delta=.1)
        self.page.evaluate('driveTest.map(false);gameplayTest.step(120)');self.assertAlmostEqual(self.state()['remaining'],29000,delta=.1)
        self.assert_no_scroll()

    def test_small_screens_and_both_2d_zooms(self):
        self.prepare()
        for width,height in [(1366,768),(1024,768),(390,844)]:
            self.page.set_viewport_size({'width':width,'height':height});self.settle_layout()
            self.stage('station-near');self.page.evaluate('driveTest.render(false,0)');self.assert_no_scroll()
            self.shot(f'viewport-{width}.png')
            self.page.keyboard.press('v')
            for zoom in ['1.5','1.75']:
                self.page.select_option('#zoomSelect',zoom);self.page.evaluate('visualTest.draw(0)');self.assert_no_scroll()
            self.page.keyboard.press('v')

    def test_paired_driving_performance_all_viewports(self):
        self.prepare();results=[]
        for width,height in [(1366,768),(1024,768),(390,844)]:
            self.page.set_viewport_size({'width':width,'height':height});self.settle_layout();self.stage('four')
            for previous in [True,False]:
                trials=[self.page.evaluate('p=>driveTest.benchmark(p)',previous) for _ in range(3)]
                result=dict(trials[0]);result['trials']=trials
                for key in ['meanRenderMs','p95RenderMs','renderedFps','rafFps']:result[key]=statistics.median(t[key] for t in trials)
                self.assertEqual(result['frames'],90);self.assertGreater(result['renderedFps'],0)
                result.update(renderer='phase5a3' if previous else 'phase5b',browser=self.browser.version);results.append(result)
        self.save('performance.json',results)

    def test_real_browser_driving_video(self):
        self.prepare();route=self.page.evaluate('driveTest.startVideo()');self.shot('video-2d-start.png')
        self.page.wait_for_timeout(300);self.page.keyboard.press('v');self.shot('video-drive-start.png')
        self.page.evaluate('driveTest.runVideo()')
        self.page.wait_for_function('!driveTest.videoState().running',timeout=45000)
        state=self.page.evaluate('driveTest.videoState()');self.assertEqual(state['speed'],0);self.assertFalse(state['modal'])
        self.assertEqual(len(state['events']),2);self.assertTrue({'w','s'}<=set(state['stats']['keys']))
        self.assertTrue({'a','d'}&set(state['stats']['keys']));self.shot('video-stopped-at-q1.png')
        self.page.keyboard.press('e');self.page.wait_for_selector('[data-answer]');self.assertFalse(self.state()['pending'])
        self.shot('video-question.png');self.page.wait_for_timeout(350);self.page.keyboard.press('Escape')
        self.page.wait_for_timeout(450);self.assertFalse(self.state()['modal']);self.assertEqual(self.state()['mode'],'drive')
        self.shot('video-return-to-drive.png');self.save('native-driving.json',{'route':route,'arrived':state,'returned':self.state()})


if __name__=='__main__':
    unittest.main(verbosity=2)
