import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IsoLevel } from '../../../core/models';

@Component({
  selector: 'app-crisis-badge',
  template: `
    <span class="crisis-badge" [style.--c]="color" [style.--bg]="bg">
      <span class="dot"></span>{{ level }}
    </span>`,
  styleUrls: ['./crisis-badge.scss'],
  standalone: true,
  imports: [CommonModule],
})
export class CrisisBadgeComponent {
  @Input() level: IsoLevel = 'VERDE';

  get color(): string {
    return { VERDE:'#27AE60', AMARELO:'#F5D623', LARANJA:'#F5A623', VERMELHO:'#E84545', DESCONHECIDO:'#718096' }[this.level] ?? '#718096';
  }
  get bg(): string {
    return { VERDE:'rgba(39,174,96,.12)', AMARELO:'rgba(245,214,35,.15)', LARANJA:'rgba(245,166,35,.15)', VERMELHO:'rgba(232,69,69,.12)', DESCONHECIDO:'rgba(113,128,150,.1)' }[this.level] ?? 'rgba(113,128,150,.1)';
  }
}
