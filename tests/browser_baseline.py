"""Optional Linux Chromium baseline smoke test; pip install playwright if needed.

Runs a local HTTP server. Internal hooks exist only in an intercepted test response;
the on-disk prototype and first browser visit are completely unmodified.
"""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
import unittest

from playwright.sync_api import sync_playwright
from browser_support import launch_browser, save_browser_artifacts

ROOT = Path(__file__).resolve().parents[1]
HOOK = """
window.baseline = {
  state: function(){ return {current:current,done:done,mode:gameMode,
    zoom:gameZoom,speed:driveSpeed,pressed:pressed,failures:failures,
    remaining:mapRemainingMs,showMap:showMap,modal:modalOpen,scale:DRIVE_SCALE}; },
  generate:generateMaze, center:worldCenter, nearby:findNearby,
  map:setMapVisible, tick:updateMapBudget,
  park:function(point){Object.assign(current.player,worldCenter(point.x,point.y));
    driveSpeed=0;pressed={};findNearby();},
  clock:function(){mapLastTick=performance.now();return mapLastTick;},
  question:openQuestion, answer:chooseAnswer, close:hideDialog,
  correct:function(i){return QUESTIONS[i].correct;}
};
"""


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


class BrowserBaselineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=ROOT))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f"http://127.0.0.1:{cls.server.server_port}/emi_maze_dualview_v1.2/index.html"
        cls.playwright = sync_playwright().start()
        cls.browser = launch_browser(cls.playwright)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def setUp(self):
        self.context = self.browser.new_context(viewport={"width": 1366, "height": 768})
        self.context.tracing.start(screenshots=True, snapshots=True, sources=True)
        self.page = self.context.new_page()
        self.errors = []
        self.page.on("pageerror", lambda error: self.errors.append(str(error)))

    def tearDown(self):
        try:
            save_browser_artifacts(self.context, self.page, ROOT / "test-results/browser-baseline",
                                   self._testMethodName, self.errors)
        finally:
            self.context.close()
        self.assertEqual(self.errors, [])

    def load_hooks(self):
        def intercept(route):
            response = route.fetch()
            source = response.text().replace("  readMapBudget();updateMapControls();", HOOK + "  readMapBudget();updateMapControls();")
            route.fulfill(response=response, body=source)
        self.page.route(self.url, intercept)
        self.page.goto(self.url)

    def state(self):
        return self.page.evaluate("baseline.state()")

    def test_original_http_page_controls_and_layout(self):
        self.page.goto(self.url)
        self.assertEqual(self.page.locator("#mazeSize").inner_text(), "25 × 19")
        self.assertEqual(self.page.locator("#zoomSelect").input_value(), "1.5")
        self.page.keyboard.press("v")
        self.assertTrue(self.page.locator("body").evaluate("e=>e.classList.contains('drive-mode')"))
        (ROOT / "test-results").mkdir(exist_ok=True)
        self.page.screenshot(path=str(ROOT / "test-results/baseline-drive.png"))
        self.page.keyboard.press("v")
        self.page.select_option("#zoomSelect", "1.75")
        self.page.click("#panelToggle")
        self.assertEqual(self.page.locator("#sidePanel").get_attribute("aria-hidden"), "false")
        self.page.keyboard.press("Escape")
        for width, height in [(1366, 768), (1024, 768), (390, 844)]:
            self.page.set_viewport_size({"width": width, "height": height})
            self.assertTrue(self.page.evaluate("document.documentElement.scrollHeight <= innerHeight"))
        self.page.set_viewport_size({"width": 1366, "height": 768})
        self.page.screenshot(path=str(ROOT / "test-results/baseline-2d.png"))

    def test_seeded_maps_all_original_sizes(self):
        self.load_hooks()
        result = self.page.evaluate("""() => {
          let total=0, layouts=new Set();
          const originalNow=Date.now, originalRandom=Math.random;
          try {
            for (const [w,h] of [[25,19],[21,15],[17,13],[13,9]]) {
              for(let seed=1;seed<=200;seed++) {
                Date.now=()=>seed*104729;Math.random=()=>0.25;
                const m=baseline.generate(w,h), keys=m.stations.map(p=>`${p.x},${p.y}`);
                if(keys.length!==4 || new Set(keys).size!==4) throw Error('station count/duplicates');
                const seen=new Set(['2,2']), queue=[[2,2]];
                for(let i=0;i<queue.length;i++) {
                  const [x,y]=queue[i];
                  for(const [dx,dy] of [[1,0],[-1,0],[0,1],[0,-1]]) {
                    const nx=x+dx,ny=y+dy,key=`${nx},${ny}`;
                    if(m.grid[ny]?.[nx]===0 && !seen.has(key)) { seen.add(key);queue.push([nx,ny]); }
                  }
                }
                for(const p of [...m.stations,m.exit]) {
                  if(!seen.has(`${p.x*2},${p.y*2}`)) throw Error('unreachable point');
                }
                if(keys.includes('1,1') || keys.includes(`${m.exit.x},${m.exit.y}`)) throw Error('station overlap');
                layouts.add(JSON.stringify(m.grid));total++;
              }
            }
          } finally {Date.now=originalNow;Math.random=originalRandom;}
          return {total,distinct:layouts.size};
        }""")
        self.assertEqual(result, {"total": 800, "distinct": 800})

    def test_attempts_questions_mode_and_drive_input(self):
        self.load_hooks()
        self.page.evaluate("baseline.park(baseline.state().current.stations[0])")
        self.page.keyboard.press("e")
        self.assertTrue(self.state()["modal"])
        self.assertEqual(self.page.locator("[data-answer]").count(), 4)
        link = self.page.locator("#dialog a")
        self.assertEqual(link.get_attribute("target"), "_blank")
        self.assertEqual(link.get_attribute("rel"), "noopener noreferrer")
        # Stub the destination: verify a real new tab without a YouTube request.
        self.page.context.route("https://www.youtube.com/**", lambda route: route.fulfill(body="Test video destination"))
        with self.page.expect_popup() as popup:
            link.click()
        popup.value.close()
        self.page.bring_to_front()
        self.page.click(f'[data-answer="{self.page.evaluate("baseline.correct(0)")}"]')
        self.assertIn("English Explanation (optional)", self.page.locator("#dialog").inner_text())
        self.page.click("#continueMaze")
        before = self.state()
        self.page.keyboard.press("v")
        driving = self.state()
        self.assertEqual(before["current"]["player"]["x"], driving["current"]["player"]["x"])
        self.assertEqual(before["current"]["player"]["y"], driving["current"]["player"]["y"])
        self.assertEqual(before["current"]["stations"], driving["current"]["stations"])
        self.assertEqual(before["done"], driving["done"])
        self.assertEqual(driving["scale"], 12)
        self.page.keyboard.down("w")
        self.page.wait_for_timeout(150)
        self.assertGreater(self.state()["speed"], 0)
        self.page.evaluate("window.dispatchEvent(new Event('blur'))")
        self.assertEqual(self.state()["speed"], 0)
        self.assertEqual(self.state()["pressed"], {})
        self.page.keyboard.up("w")
        self.page.keyboard.down("w")
        self.page.evaluate("baseline.question(1)")
        self.assertEqual(self.state()["speed"], 0)
        self.assertEqual(self.state()["pressed"], {})
        self.page.keyboard.up("w")
        self.page.evaluate("baseline.answer(1,(baseline.correct(1)+1)%4)")
        self.page.click("#nextRound")
        reset = self.state()
        self.assertEqual(reset["done"], [False]*4)
        self.assertEqual(reset["remaining"], 30000)
        self.assertEqual(reset["current"]["width"], 21)
        self.assertNotEqual(before["current"]["grid"], reset["current"]["grid"])
        for _ in range(5):
            self.page.evaluate("baseline.question(0);baseline.answer(0,(baseline.correct(0)+1)%4)")
            self.page.click("#nextRound")
        self.assertEqual(self.state()["current"]["width"], 13)
        self.page.click("#resetBtn")
        self.assertEqual(self.state()["current"]["width"], 25)
        self.assertEqual(self.state()["remaining"], 30000)
        # Complete all questions and use E at finish in both modes.
        for mode in ("drive", "2d"):
            if self.state()["mode"] != mode:
                self.page.keyboard.press("v")
            for i in range(4):
                self.page.evaluate("i=>{baseline.park(baseline.state().current.stations[i]);}", i)
                self.page.keyboard.press("e")
                self.page.click(f'[data-answer="{self.page.evaluate("i=>baseline.correct(i)", i)}"]')
                self.page.click("#continueMaze")
            self.page.evaluate("baseline.park(baseline.state().current.exit)")
            self.page.keyboard.press("e")
            self.assertIn("ALL QUESTS COMPLETED", self.page.locator("#dialog").inner_text())
            self.assertEqual(self.page.locator("#dialog a").count(), 0)  # Original FORM_URL is empty.
            self.page.click("#again")

    def test_map_budget_counts_pauses_expires_and_resets(self):
        self.load_hooks()
        self.page.evaluate("""() => {
          baseline.map(true);const t=baseline.clock();baseline.tick(t+5000);baseline.map(false);
        }""")
        remaining = self.state()["remaining"]
        self.assertAlmostEqual(remaining, 25000, delta=100)
        self.page.evaluate("const t=baseline.clock();baseline.tick(t+5000)")
        self.assertEqual(self.state()["remaining"], remaining)
        self.page.evaluate("baseline.map(true);const t=baseline.clock();baseline.tick(t+31000)")
        self.assertEqual(self.state()["remaining"], 0)
        self.assertFalse(self.state()["showMap"])
        self.assertTrue(self.page.locator("#mapToggle").is_disabled())
        self.page.click("#resetBtn")
        self.assertEqual(self.state()["remaining"], 30000)


if __name__ == "__main__":
    unittest.main(verbosity=2)
