export class GraphicsSettings {
  constructor(callbacks) {
    this.callbacks = callbacks;
    this.dialog = document.getElementById('graphics-dialog');
    document.getElementById('settings')?.addEventListener('click', () => this.open());
    document.getElementById('settings-close')?.addEventListener('click', () => this.close());
    this.dialog?.addEventListener('cancel', event => { event.preventDefault(); this.close(); });
    this.dialog?.addEventListener('keydown', event => {
      if (event.key === 'Escape') { event.preventDefault(); event.stopPropagation(); this.close(); }
      if (event.key === 'Tab') {
        const controls=[...this.dialog.querySelectorAll('button,select,input,a[href]')].filter(node=>!node.disabled&&!node.hidden);
        const index=controls.indexOf(document.activeElement);
        const next=event.shiftKey?(index-1+controls.length)%controls.length:(index+1)%controls.length;
        event.preventDefault();controls[next]?.focus();
      }
    });
  }
  open() {
    if (!this.dialog || this.dialog.open || !this.callbacks.canOpen()) return;
    this.callbacks.pause(); this.dialog.showModal();
    this.dialog.querySelector('[aria-pressed="true"]')?.focus();
  }
  close() {
    if (!this.dialog?.open) return;
    this.dialog.close(); this.callbacks.resume();
  }
}
