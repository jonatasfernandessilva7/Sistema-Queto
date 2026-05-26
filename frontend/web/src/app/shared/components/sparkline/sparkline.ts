import { Component, Input, OnChanges } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-sparkline',
  template: `
    <svg [attr.width]="w" [attr.height]="h" [attr.viewBox]="'0 0 ' + w + ' ' + h" class="sparkline">
      <defs>
        <linearGradient [id]="gradId" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" [attr.stop-color]="color" stop-opacity=".25"/>
          <stop offset="100%" [attr.stop-color]="color" stop-opacity="0"/>
        </linearGradient>
      </defs>
      <path [attr.d]="areaPath" [attr.fill]="'url(#' + gradId + ')'"/>
      <path [attr.d]="linePath" [attr.stroke]="color" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      @if (lastX !== null) {
        <circle [attr.cx]="lastX" [attr.cy]="lastY" r="3.5" [attr.fill]="color"/>
      }
    </svg>`,
  styles: ['.sparkline { display:block; overflow:visible; }'],
  standalone: true,
  imports: [CommonModule],
})
export class SparklineComponent implements OnChanges {
  @Input() values: number[] = [];   // valores 0-100
  @Input() w = 200; @Input() h = 48;
  @Input() color = '#2B7BE8';

  linePath = ''; areaPath = '';
  lastX: number | null = null; lastY = 0;
  readonly gradId = `sg_${Math.random().toString(36).slice(2)}`;

  ngOnChanges(): void { this.render(); }

  private render(): void {
    const v = this.values;
    if (!v.length) { this.linePath = ''; this.areaPath = ''; return; }
    const pad = 4;
    const min = 0; const max = 100;
    const xs = (i: number) => pad + i * (this.w - pad * 2) / Math.max(v.length - 1, 1);
    const ys = (val: number) => this.h - pad - (val - min) / (max - min) * (this.h - pad * 2);
    const pts = v.map((val, i) => ({ x: xs(i), y: ys(val) }));
    this.linePath = pts.map((p, i) => `${i ? 'L' : 'M'}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ');
    this.areaPath = this.linePath + ` L${pts[pts.length - 1].x.toFixed(1)},${this.h} L${pts[0].x.toFixed(1)},${this.h} Z`;
    this.lastX = pts[pts.length - 1].x;
    this.lastY = pts[pts.length - 1].y;
  }
}
