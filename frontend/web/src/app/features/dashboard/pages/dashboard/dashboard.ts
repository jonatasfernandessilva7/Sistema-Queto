import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { EventsService } from '../../../../core/services/events';
import { DocumentsService } from '../../../../core/services/documents';
import { ReportsService } from '../../../../core/services/reports';
import { MemoryState } from '../../../../core/models';
import { SharedModule } from '../../../../shared/shared-module';

@Component({ selector: 'app-dashboard', templateUrl: './dashboard.html', styleUrls: ['./dashboard.scss'], standalone: true, imports: [CommonModule, SharedModule] })
export class DashboardComponent implements OnInit {
  stats = [
    { label: 'Eventos Monitorados', value: '—' as string|number, sub: 'histórico', icon: '⚡' },
    { label: 'Documentos Indexados', value: '—' as string|number, sub: 'base vetorial', icon: '📄' },
    { label: 'Relatórios Gerados',  value: '—' as string|number, sub: 'análises C2M', icon: '📊' },
    { label: 'Sistemas Monitorados',value: '—' as string|number, sub: 'status geral', icon: '🔭' },
  ];

  pipeline = [
    { num: '1', label: 'Extração', desc: '3 Supervisores: Org, Risco, Continuidade' },
    { num: '2', label: 'Decision Tree', desc: 'Filtragem: sentimento, tipo, governança, maturidade' },
    { num: '3', label: 'Monte Carlo', desc: '50.000 cenários estocásticos · 5 variáveis' },
    { num: '4', label: 'ISO 22324', desc: 'Classificação + sumário executivo (LLM opcional)' },
  ];

  isoLevels = [
    { level:'VERDE',    range:'P̄ < 20%',    action:'Monitorar situação',    color:'#27AE60', bg:'rgba(39,174,96,.1)' },
    { level:'AMARELO',  range:'20% ≤ P̄ < 40%', action:'Preparar recursos', color:'#F5D623', bg:'rgba(245,214,35,.12)' },
    { level:'LARANJA',  range:'40% ≤ P̄ < 70%', action:'Ativar comitê de crise', color:'#F5A623', bg:'rgba(245,166,35,.12)' },
    { level:'VERMELHO', range:'P̄ ≥ 70%',    action:'Declarar crise',        color:'#E84545', bg:'rgba(232,69,69,.1)' },
  ];

  recentEvents: unknown[] = [];
  loading = true;
  memoryState: MemoryState | null = null;

  constructor(
    private events: EventsService,
    private docs: DocumentsService,
    private reports: ReportsService,
  ) {}

  ngOnInit(): void {
    this.events.memoryState().subscribe({
      next: ms => {
        this.memoryState = ms;
        this.stats[0].value = ms.historico_eventos?.length ?? 0;
        this.stats[3].value = Object.keys(ms.sistemas ?? {}).length;
        this.recentEvents = (ms.historico_eventos ?? []).slice(-5).reverse();
        this.loading = false;
      },
      error: () => { this.loading = false; }
    });
    this.docs.list().subscribe({ next: d => this.stats[1].value = d?.length ?? 0 });
    this.reports.list().subscribe({ next: (r: any) => this.stats[2].value = r?.result?.reports?.length ?? r?.length ?? 0 });
  }

  getEventType(ev: any): string { return ev?.evento?.tipo ?? ev?.type ?? '—'; }
  getEventTs(ev: any): string {
    const ts = ev?.timestamp ?? ev?.evento?.timestamp ?? '';
    return ts ? ts.substring(0, 16).replace('T',' ') : '—';
  }
}
