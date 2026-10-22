import { AssignmentValidator as validator } from './validator.js';

export function requireValid(issues, file) {
  if (issues.length) throw new Error(`${file}: ${issues.slice(0,3).map(i=>`${i.path}: ${i.message}`).join('; ')}`);
}
// The selector owns presentation; this data loader owns allowlisting and request races.
export class PublishedAssignments {
  constructor(base, fetcher = globalThis.fetch.bind(globalThis)) {
    this.base = new URL(base); this.fetcher = fetcher; this.units = []; this.generation = 0;
  }
  cancel() { this.generation++; this.controller?.abort(); }
  begin() { this.cancel(); this.controller = new AbortController(); return { token:this.generation, signal:this.controller.signal }; }
  async read(file, signal) {
    let response;
    try { response = await this.fetcher(new URL(file,this.base),{cache:'no-store',redirect:'error',signal}); }
    catch (error) { if(error.name==='AbortError')throw error; throw new Error(`Could not read ${file}. Check the local package or connection and retry.`); }
    if (!response.ok) throw new Error(`${file}: HTTP ${response.status}.`);
    try { return await response.json(); }
    catch(error) { if(error.name==='AbortError')throw error; throw new Error(`${file}: invalid JSON.`); }
  }
  async refresh() {
    this.units = []; const {token,signal} = this.begin();
    try {
      const data = await this.read('manifest.json',signal);
      if(token!==this.generation)return null;
      requireValid(validator.validateManifest(data),'manifest.json');
      this.units = validator.normalizeManifest(data).units;
      return this.units;
    } catch(error) { if(token!==this.generation)return null;throw error; }
  }
  async load(unitId) {
    const entry = this.units.find(unit=>unit.unitId===unitId);
    if (!entry) throw new Error('This unit is not listed in the validated public manifest.');
    const {token,signal} = this.begin();
    try {
      const data = await this.read(entry.file,signal);
      if(token!==this.generation)return null;
      requireValid(validator.validateUnit(data,entry.file),entry.file);
      return validator.normalizeUnit(data);
    } catch(error) { if(token!==this.generation)return null;throw error; }
  }
}
