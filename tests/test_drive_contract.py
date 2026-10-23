"""Phase 5B preserves the approved physics, 2D art, data and input paths."""
import hashlib
import unittest
from pathlib import Path

from drive_reference import DRIVE_REFERENCE
from tests.lite_localization import historical_source

ROOT=Path(__file__).resolve().parents[1]


class DrivingPreservationTests(unittest.TestCase):
    def test_protected_gameplay_and_2d_sources_match_approved_phase5a3(self):
        source=historical_source('student/js/game.js')
        # Normalize only the authorized reduced-motion scheduling change. All
        # other gameplay/input bytes must still match the approved source.
        source=source.replace('t>=pending.revealAt)', 't>=pending.revealAt||motionPreference.matches)')
        source=source.replace("  // OS reduced motion affects passive effects, never an explicit slash or its deadline.\n  motionPreference.addEventListener('change',function(){\n    if(current&&!pendingInteraction){if(gameMode==='drive')renderDrive(performance.now()/1000);else render(performance.now()/1000);}\n  });", "  motionPreference.addEventListener('change',function(){\n    if(!motionPreference.matches)return;\n    if(pendingInteraction)revealPending(pendingInteraction);else clearInteractionCue();\n  });")
        regions=[
            ('  var TILE=','  function randomizer(','010507759f50c7a810dc71179c14f23e25755cf9ec4d9e83a2ea67d020140ada'),
            ('  function randomizer(','  // BEGIN 2D VISUALS','c1e3d5c19c192b7e179febdc07934775f502f52850cf031911fe84709ecd95d6'),
            ('  // BEGIN 2D VISUALS','  function clearInteractionCue(','eb337724e4bbcd6a88cb1434baa95566f33c66d2128871ce2ad465c07a18f716'),
            ('  function clearInteractionCue(','  // ===== Low-power','91c146eea73415f0435442730c1528104246e81548cfe73024be700021882376'),
            ('  function chooseDriveHeading(','  // Driving artwork','951bb25fe7ca80c4c4fb8be5aa29296c784afa91e9ab336e795637ce00a6be95'),
            ('  function frame(',None,'009dc13fdb5e6d2abc3f83e0f89942a6a65f80cd7f747113ee3c261852f789a1'),
        ]
        for start,end,expected in regions:
            with self.subTest(region=start):
                body=source[source.index(start):source.index(end) if end else len(source)]
                self.assertEqual(hashlib.sha256(body.encode()).hexdigest(),expected)
        self.assertEqual(hashlib.sha256((ROOT/'student/js/rpg-renderer.js').read_text()
            .replace('if(!settings.reveal)return 0;', 'if(reducedMotion.matches||!settings.reveal)return 0;')
            .replace('    function drawInteraction(g,maze,time){\n', '    function drawInteraction(g,maze,time){\n      if(reducedMotion.matches){clearInteraction();return;}\n')
            .replace("release:'5b1-1'", "release:'5a3-1'").encode()).hexdigest(),
                         'ab8e91df38b8dff681399990d47c3e8b021807fa481b89f0fee90c61a8491667')

    def test_frozen_drive_and_compatible_asset_versions(self):
        self.assertEqual(hashlib.sha256(DRIVE_REFERENCE.encode()).hexdigest(),
                         '01bfa3e151cdadf1b8166c97ed2e462600fe0f5f855535fa8ff148e34b3eafc2')
        html=(ROOT/'student/index.html').read_text()
        self.assertIn('./js/drive-materials.js?v=5b1-1',html)
        self.assertIn('./js/game.js?v=1.0.0',html)
        self.assertIn('./js/rpg-renderer.js?v=5b1-1',html)


if __name__=='__main__':
    unittest.main()
