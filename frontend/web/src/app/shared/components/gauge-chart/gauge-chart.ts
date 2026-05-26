import { Component, Input, OnChanges } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-gauge-chart',
  templateUrl: './gauge-chart.html',
  styleUrls: ['./gauge-chart.scss'],
  standalone: true,
  imports: [CommonModule],
})
export class GaugeChartComponent implements OnChanges {
  @Input() value = 0;   // 0–100
  @Input() size = 160;

  arc = ''; needle = ''; cx = 80; cy = 80; r = 60;
  color = '#27AE60';
  displayValue = '0%';

  ngOnChanges(): void { this.render(); }

  private render(): void {
    const v = Math.max(0, Math.min(100, this.value));
    this.cx = this.size / 2; this.cy = this.size / 2;
    this.r  = this.size * 0.375;
    this.displayValue = v.toFixed(1) + '%';

    // colour
    if (v >= 70) this.color = '#E84545';
    else if (v >= 40) this.color = '#F5A623';
    else if (v >= 20) this.color = '#F5D623';
    else this.color = '#27AE60';

    // SVG arc: 180° gauge (π)
    const start = -Math.PI;
    const end   = start + Math.PI * (v / 100);
    const sx = this.cx + this.r * Math.cos(start);
    const sy = this.cy + this.r * Math.sin(start);
    const ex = this.cx + this.r * Math.cos(end);
    const ey = this.cy + this.r * Math.sin(end);
    const large = end - start > Math.PI ? 1 : 0;
    this.arc = `M ${sx} ${sy} A ${this.r} ${this.r} 0 ${large} 1 ${ex} ${ey}`;

    // needle
    const nx = this.cx + (this.r - 10) * Math.cos(end);
    const ny = this.cy + (this.r - 10) * Math.sin(end);
    this.needle = `M ${this.cx} ${this.cy} L ${nx} ${ny}`;
  }
}
