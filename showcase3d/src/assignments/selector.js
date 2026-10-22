import { PublishedAssignments } from './loader.js';

export class AssignmentSelector {
  constructor(callbacks) {
    this.callbacks=callbacks;this.loader=new PublishedAssignments(new URL('./assignments/',document.baseURI));
    const $=id=>document.getElementById(id);this.dialog=$('assignment-picker');this.select=$('unit-select');this.status=$('assignment-status');this.pending=null;
    $('assignment-mode').addEventListener('click',()=>this.open());
    $('refresh-assignments').addEventListener('click',()=>this.refresh());
    $('load-assignment').addEventListener('click',()=>this.request(this.select.value));
    $('choose-demo').addEventListener('click',()=>this.request('demo'));
    $('confirm-assignment').addEventListener('click',()=>this.confirm());
    $('cancel-assignment').addEventListener('click',()=>this.close());
    this.dialog.addEventListener('cancel',event=>{event.preventDefault();this.close();});
    this.dialog.addEventListener('keydown',event=>{if(event.key==='Escape'){event.preventDefault();event.stopPropagation();this.close();}});
    this.select.addEventListener('change',()=>this.clearPending());
  }
  clearPending() { this.pending=null;document.getElementById('assignment-warning').hidden=true; }
  choices() {
    this.select.replaceChildren(...this.loader.units.map(unit=>Object.assign(document.createElement('option'),{value:unit.unitId,textContent:`${unit.unitId} · ${unit.title}`})));
    this.select.disabled=document.getElementById('load-assignment').disabled=!this.loader.units.length;
  }
  open() {
    if(this.dialog.open || !this.callbacks.canOpen())return;
    this.callbacks.pause();this.dialog.showModal();this.refresh();
  }
  async refresh() {
    this.clearPending();this.select.replaceChildren();this.select.disabled=true;document.getElementById('load-assignment').disabled=true;
    this.status.textContent='Reading the public unit manifest…';
    try {
      const units=await this.loader.refresh();if(units===null||!this.dialog.open)return;
      this.choices();this.status.textContent=units.length?'Choose any published unit, including earlier units for review.':'No educational units have been published. Demonstration mode remains separate.';
    } catch(error) { if(this.dialog.open)this.status.textContent=`${error.message} Refresh to retry, or return to the current attempt.`; }
  }
  request(target) {
    if(target!=='demo'&&!this.loader.units.some(unit=>unit.unitId===target))return;
    this.pending=target;document.getElementById('assignment-warning').hidden=false;
    document.getElementById('switch-message').textContent=`Start ${target==='demo'?'3D Demonstration Mode':target+' · Educational Assignment Mode'}? Only successful validation replaces the current attempt. Its progress and map time will reset.`;
    document.getElementById('confirm-assignment').focus();
  }
  async confirm() {
    const target=this.pending;if(!target)return;
    this.clearPending();
    if(target==='demo'){this.loader.cancel();this.callbacks.demo();this.close();return;}
    this.status.textContent=`Loading and validating ${target}…`;
    try {
      const unit=await this.loader.load(target);if(!unit||!this.dialog.open)return;
      this.callbacks.unit(unit);this.close();
    } catch(error) {if(this.dialog.open)this.status.textContent=`${error.message} The previous attempt is retained. Retry or cancel.`;}
  }
  close() { this.loader.cancel();this.clearPending();if(this.dialog.open){this.dialog.close();this.callbacks.resume();} }
}
