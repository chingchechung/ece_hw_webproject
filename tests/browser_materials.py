"""Phase 5B.1: paired materials, world stability, filtering and real driving."""
import base64
import unittest

from browser_student import ROOT
from browser_visuals import VisualHarness, BRIDGE
import browser_drive as driving
from drive_reference import PHASE5B_BRIDGE


class MaterialTests(VisualHarness):
    artifact_directory=ROOT/'test-results/phase-5b1'
    renderer_names=('phase5b','phase5b1')
    bridge=(BRIDGE+(ROOT/'tests/gameplay_driver.js').read_text()+PHASE5B_BRIDGE+
            (ROOT/'tests/drive_probe.js').read_text()+(ROOT/'tests/material_probe.js').read_text())
    prepare=driving.DrivingVisualTests.prepare
    stage=driving.DrivingVisualTests.stage
    state=driving.DrivingVisualTests.state
    save=driving.DrivingVisualTests.save

    def setUp(self):
        if self._testMethodName=='test_real_material_driving_recording':
            self.record_video_directory=self.artifact_directory/'video'
        super().setUp()

    def tearDown(self):
        video=self.page.video
        try:
            super().tearDown()
        finally:
            if video:
                video.save_as(str(self.artifact_directory/'materials-driving.webm'));video.delete()

    def test_matched_phase5b_material_gallery(self):
        self.prepare();scenes=[]
        for name in ['straight','near-wall','long','left','right','four','station-near']:
            pose=self.page.evaluate('materialTest.long()') if name=='long' else self.stage('corner' if name=='near-wall' else name)
            state=self.page.evaluate('driveTest.snapshot()')
            for previous in [True,False]:
                self.page.evaluate('p=>driveTest.render(p,0)',previous)
                self.shot(name+('-before.png' if previous else '-after.png'))
                self.assertEqual(self.page.evaluate('driveTest.snapshot()'),state)
            if name in ['near-wall','long','station-near']:
                encoded=self.page.evaluate('materialTest.native()').split(',')[1]
                (self.artifact_directory/(name+'-native.png')).write_bytes(base64.b64decode(encoded))
            scenes.append({'name':name,'pose':pose})
        for width,height in [(1366,768),(1024,768),(390,844)]:
            self.page.set_viewport_size({'width':width,'height':height});self.settle_layout();self.stage('station-near')
            for previous in [True,False]:
                self.page.evaluate('p=>driveTest.render(p,0)',previous);self.shot(f'viewport-{width}-'+('before.png' if previous else 'after.png'))
                self.assert_no_scroll()
        self.save('scene-poses.json',scenes)

    def test_world_anchoring_cached_data_and_distance_filtering(self):
        self.prepare();self.stage('straight');result=self.page.evaluate('materialTest.stability()')
        self.assertEqual(result['before'],result['after']);self.assertEqual(result['beforeWalls'],result['afterWalls']);self.assertLess(result['wallAnchorError'],1e-6);self.assertTrue(result['reused']);self.assertTrue(result['unmodified'])
        self.assertLess(result['wrapError'],1e-8);self.assertNotEqual(result['moved'],result['initial'])
        self.assertNotEqual(result['turned'],result['angle']);self.assertGreater(result['variance'][0],result['variance'][-2]*5)
        self.save('texture-stability.json',result);self.save('texture-memory.json',self.page.evaluate('materialTest.memory()'))

    def test_geometry_all_sizes_and_temporal_aliasing_samples(self):
        self.prepare();results=[];self.page.emulate_media(reduced_motion='reduce')
        for size in [(25,19),(21,15),(17,13),(13,9)]:
            self.page.evaluate('a=>driveTest.newMaze(...a)',size);self.page.evaluate('materialTest.long()')
            self.assertLess(self.page.evaluate('driveTest.depthAgreement()'),.005)
            roads=self.page.evaluate('driveTest.roadAgreement()');self.assertGreater(roads['checked'],300)
            result=self.page.evaluate('materialTest.alias()');self.assertEqual(result['stationary'],0)
            self.assertLess(result['mean'],5);self.assertLess(result['over30'],.04)
            results.append({'maze':size,'roads':roads,**result});self.assert_no_scroll()
        self.save('geometry-filtering.json',results)

    test_paired_phase5b_material_performance=driving.DrivingVisualTests.test_paired_driving_performance_all_viewports
    test_real_material_driving_recording=driving.DrivingVisualTests.test_real_browser_driving_video


if __name__=='__main__':
    unittest.main(verbosity=2)
