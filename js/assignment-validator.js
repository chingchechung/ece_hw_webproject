/* Browser-native v1 validation; also loadable with Node for contract parity tests.
 * Load assignment-rules.js first in a browser. No fetches, DOM changes or writes.
 */
(function (root, factory) {
  'use strict';
  if (typeof module === 'object' && module.exports) {
    module.exports = factory(require('./assignment-rules.js'));
  } else {
    root.AssignmentValidator = factory(root.AssignmentRules);
  }
}(typeof globalThis !== 'undefined' ? globalThis : this, function (rules) {
  'use strict';
  const youtubeUrl = new RegExp(rules.youtubeUrl);
  const formUrl = new RegExp(rules.googleFormUrl);
  const unitKeys = ['schemaVersion', 'unitId', 'title', 'googleFormUrl', 'questions'];
  const questionKeys = ['id', 'title', 'prompt', 'questionVideoUrl', 'explanationVideoUrl', 'options', 'correctOption', 'explanationText'];
  const own = (obj, key) => Object.prototype.hasOwnProperty.call(obj, key);
  const object = value => value !== null && typeof value === 'object' && !Array.isArray(value);
  const trim = value => typeof value === 'string' ? value.trim() : value;
  const clone = value => Array.isArray(value) ? value.map(clone) : object(value)
    ? Object.fromEntries(Object.entries(value).map(([key, item]) => [key, clone(item)])) : value;
  // RegExp '$' also matches before a final newline; require the entire string.
  const fullMatch = (pattern, value) => {
    const match = pattern.exec(value);
    return match !== null && match[0] === value;
  };

  function normalizeUnit(data) {
    const result = clone(data);
    if (!object(result)) return result;
    for (const key of ['title', 'googleFormUrl']) {
      if (own(result, key)) result[key] = trim(result[key]);
    }
    if (Array.isArray(result.questions)) {
      for (const question of result.questions) {
        if (!object(question)) continue;
        for (const key of ['title', 'prompt', 'questionVideoUrl', 'explanationVideoUrl', 'explanationText']) {
          if (own(question, key)) question[key] = trim(question[key]);
        }
        if (Array.isArray(question.options)) question.options = question.options.map(trim);
      }
    }
    return result;
  }

  function normalizeManifest(data) {
    const result = clone(data);
    if (object(result) && Array.isArray(result.units)) {
      for (const entry of result.units) {
        if (object(entry) && own(entry, 'title')) entry.title = trim(entry.title);
      }
    }
    return result;
  }

  function checks() {
    const errors = [];
    const add = (path, code, message) => errors.push({path, code, message});
    function obj(value, path, allowed) {
      if (!object(value)) {
        add(path, 'type', 'Expected an object.');
        return false;
      }
      for (const key of Object.keys(value).filter(key => !allowed.includes(key)).sort()) {
        add(`${path}.${key}`, 'unknown_field', 'Unknown field in schema v1.');
      }
      return true;
    }
    function text(value, key, path, required = true) {
      const field = `${path}.${key}`;
      if (!own(value, key)) {
        if (required) add(field, 'required', 'Required field is missing.');
        return null;
      }
      const item = value[key];
      if (typeof item !== 'string') {
        add(field, 'type', 'Expected a string.');
        return null;
      }
      if (required && !item.trim()) {
        add(field, 'blank', 'Must not be blank.');
        return null;
      }
      return item;
    }
    function version(value, path) {
      if (value.schemaVersion !== 1) {
        add(`${path}.schemaVersion`, 'schema_version', 'schemaVersion must be the number 1.');
      }
    }
    function unitId(value, path) {
      const id = text(value, 'unitId', path);
      if (id !== null && !fullMatch(/^S(0[1-9]|1[0-2])$/, id)) {
        add(`${path}.unitId`, 'unit_id', 'Expected S01 through S12.');
      }
      return id;
    }
    function url(value, key, path, pattern, message) {
      const item = text(value, key, path);
      if (item !== null && !fullMatch(pattern, item)) add(`${path}.${key}`, 'url', message);
    }
    return {errors, add, obj, text, version, unitId, url};
  }

  function validateUnit(input, filename = null) {
    const data = normalizeUnit(input), check = checks();
    if (!check.obj(data, '$', unitKeys)) return check.errors;
    check.version(data, '$');
    const unitId = check.unitId(data, '$');
    const expectedFile = typeof unitId === 'string' ? `${unitId}.json` : null;
    if (filename !== null && (typeof filename !== 'string' || filename !== expectedFile)) {
      check.add('$.unitId', 'filename', 'Filename must be exactly <unitId>.json (for example S01.json).');
    }
    check.text(data, 'title', '$');
    check.url(data, 'googleFormUrl', '$', formUrl, 'Expected a supported HTTPS Google Forms URL; replace placeholders.');
    if (!Array.isArray(data.questions)) {
      check.add('$.questions', 'type', 'Expected an array of questions.');
      return check.errors;
    }
    if (![4, 5].includes(data.questions.length)) {
      check.add('$.questions', 'question_count', 'A published unit needs exactly 4 or 5 questions.');
    }
    data.questions.forEach((question, index) => {
      const path = `$.questions[${index}]`;
      if (!check.obj(question, path, questionKeys)) return;
      const id = check.text(question, 'id', path), expected = `Q${String(index + 1).padStart(2, '0')}`;
      if (id !== null && id !== expected) {
        check.add(`${path}.id`, 'question_id', `Expected ${expected}; question IDs must be unique and sequential.`);
      }
      for (const field of ['title', 'prompt', 'explanationText']) check.text(question, field, path, false);
      for (const field of ['questionVideoUrl', 'explanationVideoUrl']) {
        check.url(question, field, path, youtubeUrl, 'Expected a supported HTTPS YouTube video URL; replace placeholders.');
      }
      if (!Array.isArray(question.options)) {
        check.add(`${path}.options`, 'type', 'Expected an array of four options in A-D order.');
      } else {
        if (question.options.length !== 4) {
          check.add(`${path}.options`, 'option_count', 'Exactly four options are required in A-D order.');
        }
        question.options.forEach((option, optionIndex) => {
          const optionPath = `${path}.options[${optionIndex}]`;
          if (typeof option !== 'string') check.add(optionPath, 'type', 'Expected a string.');
          else if (!option) check.add(optionPath, 'blank', 'Must not be blank.');
        });
      }
      const answer = check.text(question, 'correctOption', path);
      if (answer !== null && !['A', 'B', 'C', 'D'].includes(answer)) {
        check.add(`${path}.correctOption`, 'answer', 'Choose exactly one of A, B, C, D.');
      }
    });
    return check.errors;
  }

  function validateManifest(input) {
    const data = normalizeManifest(input), check = checks();
    if (!check.obj(data, '$', ['schemaVersion', 'units'])) return check.errors;
    check.version(data, '$');
    if (!Array.isArray(data.units)) {
      check.add('$.units', 'type', 'Expected an array of allowed units.');
      return check.errors;
    }
    if (data.units.length > 12) check.add('$.units', 'unit_count', 'At most 12 units are allowed.');
    const seen = new Set();
    data.units.forEach((entry, index) => {
      const path = `$.units[${index}]`;
      if (!check.obj(entry, path, ['unitId', 'title', 'file'])) return;
      const id = check.unitId(entry, path);
      check.text(entry, 'title', path);
      const filename = check.text(entry, 'file', path);
      const expectedFile = typeof id === 'string' ? `${id}.json` : null;
      if (filename !== null && filename !== expectedFile) {
        check.add(`${path}.file`, 'filename', 'file must be exactly <unitId>.json; paths and remote URLs are forbidden.');
      }
      if (id !== null) {
        if (seen.has(id)) check.add(`${path}.unitId`, 'duplicate_unit', 'Unit appears more than once in the allowlist.');
        seen.add(id);
      }
    });
    return check.errors;
  }

  return Object.freeze({normalizeUnit, normalizeManifest, validateUnit, validateManifest});
}));
