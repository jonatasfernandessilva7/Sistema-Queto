import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AudioService } from '../../../../core/services/audio';
import { ToastService } from '../../../../core/services/toast';
import { AudioProcessResult, IsoLevel, PearsonEntry, PercentileEntry } from '../../../../core/models';
import { BarEntry } from '../../../../shared/components/bar-chart/bar-chart';
import { SharedModule } from '../../../../shared/shared-module';

type UploadState = 'idle' | 'uploading' | 'processing' | 'done' | 'error';

@Component({
  selector: 'app-audio-upload',
  templateUrl: './audio-upload.html',
  styleUrls: ['./audio-upload.scss'],
  standalone: true,
  imports: [CommonModule, FormsModule, SharedModule],
})
export class AudioUploadComponent {
  state: UploadState = 'idle';
  result: AudioProcessResult | null = null;
  selectedFile: File | null = null;
  consentAccepted = false;
  dragOver = false;
  errorMessage = '';
  recordingActive = false;

  // Chart data
  pearsonEntries:    BarEntry[] = [];
  percentileEntries: BarEntry[] = [];
  radarEntries = [
    { label: 'Plano Risco',  value: 0, max: 1 },
    { label: 'Plano Crise',  value: 0, max: 1 },
    { label: 'Continuidade', value: 0, max: 1 },
    { label: 'Recuperação',  value: 0, max: 1 },
    { label: 'Governança',   value: 0, max: 1 },
  ];

  constructor(
    private audio: AudioService,
    private toast: ToastService,
  ) {}

  // Upload / gravação 

  onFileSelected(ev: Event): void {
    const f = (ev.target as HTMLInputElement).files?.[0];
    if (f) this.setFile(f);
    (ev.target as HTMLInputElement).value = '';
  }

  onDrop(ev: DragEvent): void {
    ev.preventDefault(); this.dragOver = false;
    const f = ev.dataTransfer?.files?.[0];
    if (f) this.setFile(f);
  }

  private setFile(f: File): void {
    if (!f.name.toLowerCase().endsWith('.wav')) {
      this.toast.error('Apenas arquivos WAV são suportados.');
      return;
    }
    this.selectedFile = f;
    this.state  = 'idle';
    this.result = null;
    this.clearCharts();
  }

  upload(): void {
    if (!this.selectedFile || !this.consentAccepted) {
      this.toast.error('Aceite o termo de consentimento LGPD antes de continuar.');
      return;
    }
    this.state = 'uploading';
    this.audio.uploadAudio(this.selectedFile).subscribe({
      next: r  => { this.onResult(r); this.toast.success('Áudio processado com sucesso!'); },
      error: e => { this.state = 'error'; this.errorMessage = e.message; this.toast.error(e.message); },
    });
  }

  startRecord(): void {
    this.recordingActive = true;
    this.audio.startRecording().subscribe({ next: () => this.toast.info('Gravação iniciada.') });
  }

  stopRecord(): void {
    this.recordingActive = false;
    this.state = 'processing';
    this.audio.stopRecording().subscribe({
      next: r  => { this.onResult(r); this.toast.success('Reunião processada!'); },
      error: e => { this.state = 'error'; this.errorMessage = e.message; },
    });
  }

  reset(): void {
    this.state = 'idle'; this.result = null;
    this.selectedFile = null; this.clearCharts();
  }

  // Processamento do resultado

  private onResult(r: AudioProcessResult): void {
    this.result = r;
    this.state  = 'done';
    this.buildPearson(r);
    this.buildPercentiles(r);
    this.buildRadar(r);
  }

  private buildPearson(r: AudioProcessResult): void {
    const pc = r.pearson_correlations ?? {};
    const labelMap: Record<string, string> = {
      sentimento: 'Sentimento', maturidade: 'Maturidade',
      continuidade: 'Continuidade', historico: 'Histórico', conformidade: 'Conformidade',
    };
    this.pearsonEntries = Object.entries(pc)
      .filter(([, v]) => v !== null)
      .map(([k, v]) => ({ label: labelMap[k] ?? k, value: v as number }));
  }

  private buildPercentiles(r: AudioProcessResult): void {
    const p = r.percentiles ?? {};
    this.percentileEntries = Object.entries(p)
      .map(([k, v]) => ({ label: k.toUpperCase(), value: v * 100 }))
      .sort((a, b) => {
        const n = (s: string) => parseInt(s.replace('P', ''), 10);
        return n(a.label) - n(b.label);
      });
  }

  private buildRadar(r: AudioProcessResult): void {
    const ctx = r.organizational_context;
    if (!ctx) return;
    this.radarEntries = [
      { label: 'Plano Risco',  value: ctx.has_risk_plan        ? 1 : 0, max: 1 },
      { label: 'Plano Crise',  value: ctx.has_crisis_plan      ? 1 : 0, max: 1 },
      { label: 'Continuidade', value: ctx.has_continuity_plan  ? 1 : 0, max: 1 },
      { label: 'Recuperação',  value: ctx.has_recovery_plan    ? 1 : 0, max: 1 },
      { label: 'Governança',   value: ctx.formal_governance     ? 1 : 0, max: 1 },
    ];
  }

  private clearCharts(): void {
    this.pearsonEntries = []; this.percentileEntries = [];
    this.radarEntries = this.radarEntries.map(e => ({ ...e, value: 0 }));
  }

  // Helpers template

  get isoLevel(): IsoLevel  { return (this.result?.iso_22324?.level ?? 'VERDE') as IsoLevel; }
  get probPct(): number     { return (this.result?.mean_probability ?? 0) * 100; }
  get isoColor(): string    {
    return { VERDE:'#27AE60', AMARELO:'#F5D623', LARANJA:'#F5A623', VERMELHO:'#E84545' }
      [this.isoLevel] ?? '#718096';
  }
  get hasPearson(): boolean     { return this.pearsonEntries.length > 0; }
  get hasPercentiles(): boolean { return this.percentileEntries.length > 0; }
  get hasConformity(): boolean  { return this.result?.conformity_factor != null; }
  get conformityPct(): number   { return (this.result?.conformity_factor ?? 0) * 100; }
  get probColor(): string {
    const v = this.probPct;
    if (v >= 70) return '#E84545'; if (v >= 40) return '#F5A623';
    if (v >= 20) return '#F5D623'; return '#27AE60';
  }
}
