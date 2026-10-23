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
        throw new Error('Unable to read ' + file + '. Check your connection and retry.');
      }
      if (!response.ok) throw new Error(file + ' could not be loaded (HTTP ' + response.status + ').');
      try { return await response.json(); }
      catch (error) {
        if (error.name === 'AbortError') throw error;
        throw new Error(file + ' is not valid JSON.');
      }
    }
    function validate(issues, file) {
      if (issues.length) throw new Error(file + ' failed validation: ' + issues.slice(0, 3)
        .map(issue => issue.path + ': ' + issue.message).join('; '));
    }
    async function refreshManifest() {
      units = [];
      choices();
      const token = begin('Reading published units…');
      try {
        const data = await read('manifest.json', controller.signal);
        if (token !== generation) return;
        validate(validator.validateManifest(data), 'manifest.json');
        units = validator.normalizeManifest(data).units;
        choices();
        status.textContent = units.length ? 'Select a unit. Revisit any published unit for review.' : 'No published units. Refresh the list later.';
        if (callbacks.hasAssignment() && !units.some(unit => unit.unitId === callbacks.activeUnitId())) {
          status.textContent += ' The current unit is no longer published and cannot be reloaded. Return to your loaded attempt or select another unit.';
        }
      } catch (error) {
        if (token !== generation) return;
        status.textContent = error.message + ' Please refresh the list.';
      }
    }
    async function loadUnit(entry) {
      const token = begin('Loading ' + entry.unitId + '…');
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
        status.textContent = error.message + ' You can retry, select another unit or refresh the list.';
      }
    }
    function requestLoad() {
      const entry = units.find(unit => unit.unitId === select.value);
      if (!entry) return;
      if (!callbacks.hasAssignment()) { loadUnit(entry); return; }
      begin('The new unit replaces this attempt only after validation. Cancel to return.');
      pending = entry;
      document.getElementById('switchMessage').textContent = 'Start ' + entry.unitId + '? After validation, the maze, progress and map allowance will reset.';
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
      begin('Select a unit. Your attempt is paused; cancel to return. Confirm before starting a new unit.');
      choices();
      select.focus({preventScroll: true});
    }});
  }});
}(globalThis));
