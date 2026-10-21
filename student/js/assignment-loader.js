/* Static allowlist loader. No unit is requested until selected from a valid manifest. */
(function (root) {
  'use strict';
  root.AssignmentLoader = Object.freeze({create: function (callbacks) {
    const validator = root.AssignmentValidator;
    const panel = document.getElementById('assignmentPanel');
    const shell = document.querySelector('.shell');
    const select = document.getElementById('unitSelect');
    const load = document.getElementById('loadUnit');
    const refresh = document.getElementById('refreshManifest');
    const status = document.getElementById('assignmentStatus');
    const back = document.getElementById('returnToMaze');
    const warning = document.getElementById('switchWarning');
    const confirm = document.getElementById('confirmSwitch');
    const cancel = document.getElementById('cancelSwitch');
    let units = [], generation = 0, controller = null, pending = null;

    function begin(message) {
      generation++;
      if (controller) controller.abort();
      controller = new AbortController();
      pending = null;
      warning.hidden = true;
      callbacks.onPause();
      back.hidden = !callbacks.hasAssignment();
      panel.hidden = false;
      shell.inert = true;
      status.textContent = message;
      status.tabIndex = -1;
      status.focus({preventScroll: true});
      return generation;
    }
    function choices() {
      select.replaceChildren();
      for (const entry of units) {
        const option = document.createElement('option');
        option.value = entry.unitId;
        option.textContent = entry.unitId + ' · ' + entry.title;
        select.appendChild(option);
      }
      select.disabled = load.disabled = units.length === 0;
    }
    async function read(file, signal) {
      let response;
      try {
        response = await fetch(new URL('./assignments/' + file, document.baseURI), {
          cache: 'no-store', signal: signal, redirect: 'error'
        });
      } catch (error) {
        if (error.name === 'AbortError') throw error;
        throw new Error('無法讀取 ' + file + '，請檢查連線後重試。');
      }
      if (!response.ok) throw new Error(file + ' 讀取失敗（HTTP ' + response.status + '）。');
      try { return await response.json(); }
      catch (error) {
        if (error.name === 'AbortError') throw error;
        throw new Error(file + ' 不是有效的 JSON。');
      }
    }
    function validate(issues, file) {
      if (issues.length) throw new Error(file + ' 驗證失敗：' + issues.slice(0, 3)
        .map(issue => issue.path + ': ' + issue.message).join('；'));
    }
    async function refreshManifest() {
      units = [];
      choices();
      const token = begin('正在讀取公開單元清單…');
      try {
        const data = await read('manifest.json', controller.signal);
        if (token !== generation) return;
        validate(validator.validateManifest(data), 'manifest.json');
        units = validator.normalizeManifest(data).units;
        choices();
        status.textContent = units.length ? '請選擇單元。已發布的單元也可再次練習。' : '目前沒有已發布的單元。可稍後重新整理清單。';
        if (callbacks.hasAssignment() && !units.some(unit => unit.unitId === callbacks.activeUnitId())) {
          status.textContent += ' 目前挑戰的單元已不在公開清單，無法重新載入；可返回本次已載入的挑戰或選擇其他單元。';
        }
      } catch (error) {
        if (token !== generation) return;
        status.textContent = error.message + ' 請重新整理清單。';
      }
    }
    async function loadUnit(entry) {
      const token = begin('正在載入 ' + entry.unitId + '…');
      try {
        const data = await read(entry.file, controller.signal);
        if (token !== generation) return;
        validate(validator.validateUnit(data, entry.file), entry.file);
        // Commit only after successful validation; a failed switch can return safely.
        callbacks.onReset();
        callbacks.onReady(validator.normalizeUnit(data));
        callbacks.onResume();
        panel.hidden = true;
        shell.inert = false;
        document.getElementById('maze').focus({preventScroll: true});
      } catch (error) {
        if (token !== generation) return;
        status.textContent = error.message + ' 可重試載入、選擇其他單元或重新整理清單。';
      }
    }
    function requestLoad() {
      const entry = units.find(unit => unit.unitId === select.value);
      if (!entry) return;
      if (!callbacks.hasAssignment()) { loadUnit(entry); return; }
      begin('新單元驗證成功後才會取代目前挑戰；可取消返回。');
      pending = entry;
      document.getElementById('switchMessage').textContent = '確定開始 ' + entry.unitId + '？新單元驗證成功後，目前挑戰的迷宮、進度及地圖時間將被重置。';
      warning.hidden = false;
      confirm.focus({preventScroll: true});
    }
    function returnToMaze() {
      if (!callbacks.hasAssignment()) return;
      generation++;
      if (controller) controller.abort();
      pending = null;
      warning.hidden = true;
      panel.hidden = true;
      shell.inert = false;
      callbacks.onResume();
      document.getElementById('maze').focus({preventScroll: true});
    }
    load.addEventListener('click', requestLoad);
    confirm.addEventListener('click', function () {
      const entry = pending;
      if (entry && units.includes(entry)) loadUnit(entry);
    });
    cancel.addEventListener('click', returnToMaze);
    back.addEventListener('click', returnToMaze);
    select.addEventListener('change', function () { pending = null; warning.hidden = true; });
    panel.addEventListener('keydown', function (event) {
      if (event.key === 'Escape' && callbacks.hasAssignment()) { event.preventDefault(); returnToMaze(); }
    });
    refresh.addEventListener('click', refreshManifest);
    return Object.freeze({start: refreshManifest, open: function () {
      begin('請選擇單元。目前挑戰已暫停，可取消並返回；開始新單元前會請你確認。');
      choices();
      select.focus({preventScroll: true});
    }});
  }});
}(globalThis));
