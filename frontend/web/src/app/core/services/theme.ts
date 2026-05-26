import { Injectable, signal } from '@angular/core';

export type Theme = 'light' | 'dark';

@Injectable({ providedIn: 'root' })
export class ThemeService {
  private readonly STORAGE_KEY = 'queto-theme';
  readonly theme = signal<Theme>(this._load());

  toggle(): void {
    const next: Theme = this.theme() === 'light' ? 'dark' : 'light';
    this.theme.set(next);
    document.documentElement.setAttribute('data-theme', next === 'dark' ? 'dark' : '');
    localStorage.setItem(this.STORAGE_KEY, next);
  }

  apply(): void {
    document.documentElement.setAttribute('data-theme', this.theme() === 'dark' ? 'dark' : '');
  }

  private _load(): Theme {
    const stored = localStorage.getItem(this.STORAGE_KEY) as Theme | null;
    return stored ?? 'light';
  }
}
