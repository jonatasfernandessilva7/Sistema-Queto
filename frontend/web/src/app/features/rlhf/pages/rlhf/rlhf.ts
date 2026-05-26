import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { RlhfService } from '../../../../core/services/rlhf';
import { ToastService } from '../../../../core/services/toast';
import { RlhfWeights } from '../../../../core/models';
import { SharedModule } from '../../../../shared/shared-module';

@Component({ selector: 'app-rlhf', templateUrl: './rlhf.html', styleUrls: ['./rlhf.scss'], standalone: true, imports: [CommonModule, ReactiveFormsModule, SharedModule] })
export class RlhfComponent implements OnInit {
  weights: RlhfWeights | null = null;
  adjustments: unknown[] = [];
  loadingWeights = false;
  loadingAdj = false;
  processing = false;
  resetting = false;
  feedbackForm: FormGroup;
  submittingFb = false;

  weightKeys: { key: keyof RlhfWeights; label: string; desc: string }[] = [
    { key: 'crisis_threshold',             label: 'Threshold de Crise',            desc: 'Score mínimo na Decision Tree para acionar Monte Carlo' },
    { key: 'decision_tree_sentiment',      label: 'Peso — Sentimento (DT)',         desc: 'Contribuição do sentimento negativo na filtragem inicial' },
    { key: 'decision_tree_type',           label: 'Peso — Tipo de Evento (DT)',     desc: 'Contribuição do tipo de evento crítico' },
    { key: 'decision_tree_governance',     label: 'Peso — Governança (DT)',         desc: 'Contribuição da falta de governança' },
    { key: 'decision_tree_maturity',       label: 'Peso — Maturidade (DT)',         desc: 'Contribuição da baixa maturidade organizacional' },
    { key: 'monte_carlo_simulations',      label: 'Simulações Monte Carlo',         desc: 'Número de cenários por ciclo de inferência' },
    { key: 'monte_carlo_sentiment_modifier', label: 'Modificador de Sentimento (MC)', desc: 'Ajuste fino do sentimento no cálculo de P_crisis' },
  ];

  constructor(
    private svc: RlhfService,
    private toast: ToastService,
    fb: FormBuilder,
  ) {
    this.feedbackForm = fb.group({
      report_id:              ['', Validators.required],
      actual_crisis:          [false],
      c2m_probability_comment:['accurate', Validators.required],
      usefulness_score:       [3, [Validators.min(1), Validators.max(5)]],
      comments:               [''],
    });
  }

  ngOnInit(): void { this.loadWeights(); this.loadAdjustments(); }

  loadWeights(): void {
    this.loadingWeights = true;
    this.svc.weights().subscribe({
      next: r => { this.weights = r.weights; this.loadingWeights = false; },
      error: () => { this.loadingWeights = false; },
    });
  }

  loadAdjustments(): void {
    this.loadingAdj = true;
    this.svc.adjustments(20).subscribe({
      next: (r: any) => {
        this.adjustments = r?.adjustments ?? r ?? [];
        this.loadingAdj = false;
      },
      error: () => { this.loadingAdj = false; },
    });
  }

  submitFeedback(): void {
    if (this.feedbackForm.invalid) return;
    this.submittingFb = true;
    this.svc.submitFeedback(this.feedbackForm.value).subscribe({
      next: () => {
        this.submittingFb = false;
        this.toast.success('Feedback enviado! O sistema RLHF irá processar os ajustes.');
        this.feedbackForm.patchValue({ report_id: '', comments: '' });
      },
      error: e => { this.submittingFb = false; this.toast.error(e.message); },
    });
  }

  processFeedback(): void {
    this.processing = true;
    this.svc.process(5).subscribe({
      next: (r: any) => {
        this.processing = false;
        const msg = r?.message ?? 'Processamento concluído.';
        this.toast.success(msg);
        this.loadWeights();
        this.loadAdjustments();
      },
      error: e => { this.processing = false; this.toast.error(e.message); },
    });
  }

  resetWeights(): void {
    if (!confirm('Resetar todos os pesos para os valores padrão?')) return;
    this.resetting = true;
    this.svc.resetWeights().subscribe({
      next: () => { this.resetting = false; this.toast.success('Pesos restaurados.'); this.loadWeights(); },
      error: e => { this.resetting = false; this.toast.error(e.message); },
    });
  }

  getWeightVal(key: keyof RlhfWeights): number {
    return this.weights ? (this.weights[key] as number) : 0;
  }

  getAdjTs(a: any): string {
    const ts = a?.timestamp ?? a?.created_at ?? '';
    return ts ? ts.substring(0, 16).replace('T', ' ') : '—';
  }

  getAdjParam(a: any): string { return a?.parameter ?? a?.param ?? '—'; }
  getAdjOld(a: any): string  { return typeof a?.old_value === 'number' ? a.old_value.toFixed(4) : '—'; }
  getAdjNew(a: any): string  { return typeof a?.new_value === 'number' ? a.new_value.toFixed(4) : '—'; }

  isThreshold(key: keyof RlhfWeights): boolean { return key === 'crisis_threshold'; }
  isSimCount(key: keyof RlhfWeights): boolean   { return key === 'monte_carlo_simulations'; }
}
