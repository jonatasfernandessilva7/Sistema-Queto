import { Component, Input, OnChanges } from '@angular/core';
import { CommonModule } from '@angular/common';

export interface BarEntry { label: string; value: number; color?: string; }

@Component({
  selector: 'app-bar-chart',
  templateUrl: './bar-chart.html',
  styleUrls: ['./bar-chart.scss'],
  standalone: true,
  imports: [CommonModule],
})
export class BarChartComponent implements OnChanges {
  @Input() entries: BarEntry[] = [];
  @Input() title = '';
  @Input() unit = '';
  @Input() maxValue = 1;
  @Input() showNegative = false;   // ativa escala -1..+1 para Pearson

  rendered: Array<BarEntry & { pct: number; barColor: string; isNeg: boolean }> = [];

  ngOnChanges(): void { this.render(); }

  private render(): void {
    const abs = this.entries.map(e => Math.abs(e.value));
    const max = this.maxValue || Math.max(...abs, 0.01);
    this.rendered = this.entries.map(e => ({
      ...e,
      pct: Math.abs(e.value) / max * 100,
      barColor: e.color ?? this.colorFor(e.value),
      isNeg: e.value < 0,
    }));
  }

  private colorFor(v: number): string {
    if (!this.showNegative) {
      if (v >= 0.7) return '#E84545';
      if (v >= 0.4) return '#F5A623';
      if (v >= 0.2) return '#F5D623';
      return '#27AE60';
    }
    // Pearson: positivo = vermelho (risco aumenta), negativo = verde
    return v > 0 ? '#E84545' : '#27AE60';
  }
}
