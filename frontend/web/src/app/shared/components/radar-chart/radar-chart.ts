import { Component, Input, OnChanges } from '@angular/core';
import { CommonModule } from '@angular/common';

export interface RadarEntry { label: string; value: number; max?: number; }

@Component({
  selector: 'app-radar-chart',
  templateUrl: './radar-chart.html',
  styleUrls: ['./radar-chart.scss'],
  standalone: true,
  imports: [CommonModule],
})
export class RadarChartComponent implements OnChanges {
  @Input() entries: RadarEntry[] = [];
  @Input() size = 220;

  cx = 110; cy = 110; radius = 85;
  gridPaths: string[] = [];
  axisLines: Array<{ x1:number; y1:number; x2:number; y2:number; label:string; lx:number; ly:number }> = [];
  dataPath = '';
  dataPoints: Array<{ x:number; y:number; value:string }> = [];

  ngOnChanges(): void { this.render(); }

  private render(): void {
    this.cx = this.size / 2; this.cy = this.size / 2;
    this.radius = this.size * 0.38;
    const n = this.entries.length;
    if (!n) return;

    const angle = (i: number) => (Math.PI * 2 * i / n) - Math.PI / 2;

    // grid circles (20%, 40%, 60%, 80%, 100%)
    this.gridPaths = [0.2, 0.4, 0.6, 0.8, 1].map(pct => {
      const pts = this.entries.map((_, i) => {
        const a = angle(i); const r = this.radius * pct;
        return `${this.cx + r * Math.cos(a)},${this.cy + r * Math.sin(a)}`;
      });
      return `M ${pts.join(' L ')} Z`;
    });

    // axis lines and labels
    const labelRadius = this.radius + 22;
    this.axisLines = this.entries.map((e, i) => {
      const a = angle(i);
      const lx = this.cx + labelRadius * Math.cos(a);
      const ly = this.cy + labelRadius * Math.sin(a);
      return { x1: this.cx, y1: this.cy, x2: this.cx + this.radius * Math.cos(a), y2: this.cy + this.radius * Math.sin(a), label: e.label, lx, ly };
    });

    // data polygon
    const pts = this.entries.map((e, i) => {
      const max = e.max ?? 5;
      const pct = Math.min(1, Math.max(0, e.value / max));
      const a = angle(i);
      return { x: this.cx + this.radius * pct * Math.cos(a), y: this.cy + this.radius * pct * Math.sin(a), value: e.value.toFixed(1) };
    });
    this.dataPath = `M ${pts.map(p => `${p.x},${p.y}`).join(' L ')} Z`;
    this.dataPoints = pts;
  }
}
