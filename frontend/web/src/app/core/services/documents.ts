import { Injectable } from '@angular/core';
import { HttpEvent, HttpRequest } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { ApiService } from './api';
import { Document } from '../models';

export interface DocumentAnalysis {
  company_file: string;
  resume: string;
  extracted_tables: boolean;
  status?: string;
  details?: string;
}

export interface DocumentAnalysisResponse {
  status: number;
  message: string;
  results: DocumentAnalysis[];
}

@Injectable({ providedIn: 'root' })
export class DocumentsService {
  constructor(private api: ApiService) {}

  list(): Observable<Document[]> {
    return this.api.get<Document[]>('/v1/u/docs').pipe(
      map(r => (Array.isArray(r) ? r : []))
    );
  }

  upload(files: File[]): Observable<unknown> {
    const form = new FormData();
    files.forEach(f => form.append('file', f, f.name));
    return this.api.postForm('/v1/u/docs', form);
  }

  /** Substitui um documento: remove o antigo e faz upload do novo */
  replace(id: number, newFile: File): Observable<unknown> {
    return new Observable(obs => {
      this.api.delete(`/v1/u/docs/${id}`).subscribe({
        next: () => {
          this.upload([newFile]).subscribe({
            next: r => { obs.next(r); obs.complete(); },
            error: e => obs.error(e),
          });
        },
        error: e => obs.error(e),
      });
    });
  }

  delete(id: number): Observable<unknown> {
    return this.api.delete(`/v1/u/docs/${id}`);
  }

  view(id: number): string {
    // Retorna URL do endpoint de visualização inline (PDF no browser)
    return `${this.api.base}/v1/u/docs/${id}`;
  }

  analyze(): Observable<DocumentAnalysisResponse> {
    return this.api.get<DocumentAnalysisResponse>('/v1/u/docs-analysis');
  }
}
