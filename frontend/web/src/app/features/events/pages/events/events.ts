import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { EventsService } from '../../../../core/services/events';
import { ToastService } from '../../../../core/services/toast';
import { SharedModule } from '../../../../shared/shared-module';

@Component({ selector: 'app-events', templateUrl: './events.html', styleUrls: ['./events.scss'], standalone: true, imports: [CommonModule, ReactiveFormsModule, SharedModule] })
export class EventsComponent implements OnInit {
  events: unknown[] = [];
  loading = false;
  submitting = false;
  form: FormGroup;
  showForm = false;

  constructor(private svc: EventsService, private toast: ToastService, fb: FormBuilder) {
    this.form = fb.group({
      type: ['ataque_cibernetico', Validators.required],
      origin: ['manual', Validators.required],
      detail_texto: [''],
    });
  }

  ngOnInit(): void { this.load(); }

  load(): void {
    this.loading = true;
    this.svc.all().subscribe({
      next: (r: any) => { this.events = r?.events ?? []; this.loading = false; },
      error: () => { this.loading = false; }
    });
  }

  submit(): void {
    if (this.form.invalid) return;
    this.submitting = true;
    const v = this.form.value;
    const payload = { type: v.type, origin: v.origin, details: { texto: v.detail_texto } };
    this.svc.submitTextEvent(payload).subscribe({
      next: () => { this.submitting = false; this.toast.success('Evento enviado!'); this.showForm = false; this.load(); },
      error: e => { this.submitting = false; this.toast.error(e.message); }
    });
  }

  getType(ev: any): string { return ev?.evento?.tipo ?? ev?.tipo ?? '—'; }
  getOrigin(ev: any): string { return ev?.evento?.origem ?? ev?.origem ?? '—'; }
  getTs(ev: any): string {
    const ts = ev?.timestamp ?? ev?.evento?.timestamp ?? '';
    return ts ? ts.substring(0,16).replace('T',' ') : '—';
  }
}
