import { Injectable, signal } from '@angular/core';

export interface Toast { id: number; message: string; type: 'success' | 'error' | 'info'; }

@Injectable({ providedIn: 'root' })
export class ToastService {
  private _seq = 0;
  toasts = signal<Toast[]>([]);

  show(message: string, type: Toast['type'] = 'info', duration = 3500): void {
    const id = ++this._seq;
    this.toasts.update(t => [...t, { id, message, type }]);
    setTimeout(() => this.toasts.update(t => t.filter(x => x.id !== id)), duration);
  }

  success(m: string): void { this.show(m, 'success'); }
  error(m: string): void   { this.show(m, 'error'); }
  info(m: string): void    { this.show(m, 'info'); }
}
