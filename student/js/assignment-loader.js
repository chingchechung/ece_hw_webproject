/* Static allowlist loader. No unit is requested until selected from a valid manifest. */
(function (root) {
  'use strict';
  root.AssignmentLoader = Object.freeze({create: function (callbacks) {
    const validator = root.AssignmentValidator;
    const panel = document.getElementById('assignmentPanel');
    const select = document.getElementById('unitSelect');
    const load = document.getElementById('loadUnit');
    const refresh = document.getElementById('refreshManifest');
    const status = document.getElementById('assignmentStatus');
    let units = [], generation = 0, controller = null;

    function begin(message) {
      generation++;
      if (controller) controller.abort();
      controller = new AbortController();
      callbacks.onReset();
      panel.hidden = false;
      status.textContent = message;
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
      } catch (error) {
        if (token !== generation) return;
        status.textContent = error.message + ' 請重新整理清單。';
      }
    }
    async function loadUnit() {
      const entry = units.find(unit => unit.unitId === select.value);
      if (!entry) return;
      const token = begin('正在載入 ' + entry.unitId + '…');
      try {
        const data = await read(entry.file, controller.signal);
        if (token !== generation) return;
        validate(validator.validateUnit(data, entry.file), entry.file);
        callbacks.onReady(validator.normalizeUnit(data));
        panel.hidden = true;
        document.getElementById('maze').focus({preventScroll: true});
      } catch (error) {
        if (token !== generation) return;
        status.textContent = error.message + ' 可重試載入、選擇其他單元或重新整理清單。';
      }
    }
    load.addEventListener('click', loadUnit);
    refresh.addEventListener('click', refreshManifest);
    return Object.freeze({start: refreshManifest, open: function () {
      begin('請選擇單元。開始新單元會重置本次挑戰。');
      choices();
      select.focus({preventScroll: true});
    }});
  }});
}(globalThis));
