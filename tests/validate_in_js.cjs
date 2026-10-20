// One shared JSON corpus enters on stdin; results exit as JSON. No dependencies.
'use strict';
const fs = require('node:fs');
const validator = require('../js/assignment-validator.js');
const rules = require('../js/assignment-rules.js');
const cases = JSON.parse(fs.readFileSync(0, 'utf8'));
const results = cases.map(item => ({
  errors: item.kind === 'unit'
    ? validator.validateUnit(item.data, item.filename ?? null)
    : validator.validateManifest(item.data),
  normalized: item.kind === 'unit'
    ? validator.normalizeUnit(item.data) : validator.normalizeManifest(item.data)
}));
process.stdout.write(JSON.stringify({rules, results}));
