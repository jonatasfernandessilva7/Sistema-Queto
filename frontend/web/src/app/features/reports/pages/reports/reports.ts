import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReportsService } from '../../../../core/services/reports';
import { ReportParserService } from '../../../../core/services/report-parser';
import { Report, ReportDetail, PearsonEntry, PercentileEntry, IsoLevel } from '../../../../core/models';
import { SharedModule } from '../../../../shared/shared-module';

@Component({
  selector: 'app-reports',
  templateUrl: './reports.html',
  styleUrls: ['./reports.scss'],
  standalone: true,
  imports: [CommonModule, SharedModule],
})
export class ReportsComponent implements OnInit {
  reports:  ReportDetail[] = [];
  loading = false;
  selected: ReportDetail | null = null;

  // ── Dados para gráficos do relatório selecionado ──────────────────────────
  pearsonEntries:    PearsonEntry[] = [];
  percentileEntries: PercentileEntry[] = [];
  probabilityHistory: number[] = [];   // sparkline: prob dos últimos N relatórios

  // ── Dados para gráfico radar de contexto organizacional ──────────────────
  radarEntries = [
    { label: 'Plano Risco',    value: 0, max: 1 },
    { label: 'Plano Crise',   value: 0, max: 1 },
    { label: 'Continuidade',  value: 0, max: 1 },
    { label: 'Recuperação',   value: 0, max: 1 },
    { label: 'Governança',    value: 0, max: 1 },
  ];

  constructor(
    private svc: ReportsService,
    private parser: ReportParserService,
  ) {}

  ngOnInit(): void { this.load(); }

  load(): void {
    this.loading = true;
    this.svc.list().subscribe({
      next: raw => {
        this.reports = this.parser.parseAll(raw);
        this.buildSparkline();
        this.loading = false;
      },
      error: () => { this.loading = false; },
    });
  }

  select(r: ReportDetail): void {
    this.selected = this.selected?.id === r.id ? null : r;
    if (this.selected) this.buildCharts(this.selected);
  }

  // ── Chart builders ────────────────────────────────────────────────────────

  private buildCharts(r: ReportDetail): void {
    this.pearsonEntries = r.pearson;
    this.percentileEntries = r.percentiles.map(p => ({
      ...p,
      color: this.probColor(p.value),
    }));
    this.buildRadar(r);
  }

  private buildRadar(r: ReportDetail): void {
    // Tentar extrair contexto do texto do relatório
    const t = r.relatorio ?? '';
    const bool = (pat: RegExp) => pat.test(t) ? 1 : 0;
    this.radarEntries = [
      { label: 'Plano Risco',   value: bool(/plano de risco.*?✓|has_risk_plan.*?true/i),   max: 1 },
      { label: 'Plano Crise',   value: bool(/plano de crise.*?✓|has_crisis_plan.*?true/i),  max: 1 },
      { label: 'Continuidade',  value: bool(/continuidade.*?✓|has_continuity.*?true/i),     max: 1 },
      { label: 'Recuperação',   value: bool(/recuperação.*?✓|has_recovery.*?true/i),        max: 1 },
      { label: 'Governança',    value: bool(/governança.*?✓|formal_governance.*?true/i),    max: 1 },
    ];
  }

  private buildSparkline(): void {
    this.probabilityHistory = this.reports
      .filter(r => r.probability_pct !== null)
      .slice(0, 20)
      .reverse()
      .map(r => r.probability_pct!);
  }

  // ── Utilidades template ───────────────────────────────────────────────────

  getTs(r: ReportDetail): string {
    const ts = r.timestamp ?? '';
    return ts ? ts.substring(0, 16).replace('T', ' ') : '—';
  }

  isoColor(level: IsoLevel | null): string {
    return { VERDE:'#27AE60', AMARELO:'#F5D623', LARANJA:'#F5A623', VERMELHO:'#E84545' }[level ?? ''] ?? '#718096';
  }

  probColor(v: number): string {
    if (v >= 70) return '#E84545';
    if (v >= 40) return '#F5A623';
    if (v >= 20) return '#F5D623';
    return '#27AE60';
  }

  hasPearson(): boolean     { return this.pearsonEntries.length > 0; }
  hasPercentiles(): boolean { return this.percentileEntries.length > 0; }
  hasSparkline(): boolean   { return this.probabilityHistory.length > 1; }

  get sparklineColor(): string {
    const last = this.probabilityHistory[this.probabilityHistory.length - 1] ?? 0;
    return this.probColor(last);
  }
}
