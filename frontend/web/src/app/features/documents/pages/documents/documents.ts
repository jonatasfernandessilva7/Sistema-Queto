import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { DocumentsService, DocumentAnalysis } from '../../../../core/services/documents';
import { ToastService } from '../../../../core/services/toast';
import { Document } from '../../../../core/models';
import { SharedModule } from '../../../../shared/shared-module';

type PanelMode = 'none' | 'view' | 'replace' | 'analysis';

@Component({
  selector: 'app-documents',
  templateUrl: './documents.html',
  styleUrls: ['./documents.scss'],
  standalone: true,
  imports: [CommonModule, FormsModule, SharedModule],
})
export class DocumentsComponent implements OnInit {
  docs: Document[] = [];
  loading     = false;
  uploading   = false;
  analyzing   = false;
  replacing   = false;
  deleting: number | null = null;

  /** Documento atualmente em foco (visualização / substituição) */
  activeDoc: Document | null = null;
  panelMode: PanelMode = 'none';

  /** URL do PDF para exibição inline no <iframe> */
  viewUrl = '';

  /** Arquivo selecionado para substituição */
  replaceFile: File | null = null;
  replacePreview = '';

  /** Resultado da análise semântica */
  analysisResults: DocumentAnalysis[] = [];

  constructor(
    private svc: DocumentsService,
    private toast: ToastService,
  ) {}

  ngOnInit(): void { this.load(); }

  // ── Listagem ──────────────────────────────────────────────────────────────

  load(): void {
    this.loading = true;
    this.svc.list().subscribe({
      next: d => { this.docs = d; this.loading = false; },
      error: () => { this.loading = false; },
    });
  }

  // ── Upload ────────────────────────────────────────────────────────────────

  onUpload(ev: Event): void {
    const files = Array.from((ev.target as HTMLInputElement).files ?? []);
    if (!files.length) return;
    this.uploading = true;
    this.svc.upload(files).subscribe({
      next: () => {
        this.uploading = false;
        this.toast.success(`${files.length} documento(s) enviado(s) com sucesso.`);
        this.load();
      },
      error: e => { this.uploading = false; this.toast.error(e.message); },
    });
    // reset input
    (ev.target as HTMLInputElement).value = '';
  }

  // ── Visualização ──────────────────────────────────────────────────────────

  openView(doc: Document): void {
    this.activeDoc = doc;
    this.viewUrl   = this.svc.view(doc.id);
    this.panelMode = 'view';
  }

  openInNewTab(doc: Document): void {
    window.open(this.svc.view(doc.id), '_blank');
  }

  // ── Substituição ──────────────────────────────────────────────────────────

  openReplace(doc: Document): void {
    this.activeDoc    = doc;
    this.replaceFile  = null;
    this.replacePreview = '';
    this.panelMode    = 'replace';
  }

  onReplaceSelected(ev: Event): void {
    const f = (ev.target as HTMLInputElement).files?.[0];
    if (!f) return;
    this.replaceFile    = f;
    this.replacePreview = f.name;
    (ev.target as HTMLInputElement).value = '';
  }

  confirmReplace(): void {
    if (!this.activeDoc || !this.replaceFile) return;
    this.replacing = true;
    this.svc.replace(this.activeDoc.id, this.replaceFile).subscribe({
      next: () => {
        this.replacing    = false;
        this.replaceFile  = null;
        this.replacePreview = '';
        this.panelMode    = 'none';
        this.activeDoc    = null;
        this.toast.success('Documento substituído. Cache de embeddings invalidado.');
        this.load();
      },
      error: e => { this.replacing = false; this.toast.error(e.message); },
    });
  }

  // ── Exclusão ──────────────────────────────────────────────────────────────

  confirmDelete(doc: Document): void {
    if (!confirm(`Remover "${doc.filename}"? Esta ação não pode ser desfeita.`)) return;
    this.deleting = doc.id;
    this.svc.delete(doc.id).subscribe({
      next: () => {
        this.deleting = null;
        this.toast.success('Documento removido.');
        if (this.activeDoc?.id === doc.id) this.closePanel();
        this.load();
      },
      error: e => { this.deleting = null; this.toast.error(e.message); },
    });
  }

  // ── Análise semântica ─────────────────────────────────────────────────────

  runAnalysis(): void {
    this.analyzing   = true;
    this.panelMode   = 'analysis';
    this.activeDoc   = null;
    this.analysisResults = [];
    this.svc.analyze().subscribe({
      next: r => {
        this.analysisResults = r?.results ?? [];
        this.analyzing = false;
        this.toast.success('Análise semântica concluída!');
      },
      error: e => { this.analyzing = false; this.toast.error(e.message); },
    });
  }

  // ── Painel ────────────────────────────────────────────────────────────────

  closePanel(): void {
    this.panelMode  = 'none';
    this.activeDoc  = null;
    this.viewUrl    = '';
    this.replaceFile = null;
    this.replacePreview = '';
  }

  // ── Helpers template ──────────────────────────────────────────────────────

  ext(filename: string): string {
    return filename.split('.').pop()?.toUpperCase() ?? '?';
  }

  extColor(filename: string): string {
    const map: Record<string, string> = {
      PDF: '#E84545', DOCX: '#2B7BE8', DOC: '#2B7BE8',
      TXT: '#27AE60', MD: '#27AE60',
    };
    return map[this.ext(filename)] ?? '#718096';
  }

  isPdf(filename: string): boolean {
    return filename.toLowerCase().endsWith('.pdf');
  }

  isActive(doc: Document): boolean {
    return this.activeDoc?.id === doc.id;
  }
}
