import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from './api';
import { MemoryState } from '../models';

@Injectable({ providedIn: 'root' })
export class EventsService {
  constructor(private api: ApiService) {}
  all(): Observable<unknown> { return this.api.get('/v1/u/events'); }
  clusters(k = 3): Observable<unknown> { return this.api.get(`/v1/u/cluster-events?k=${k}`); }
  memoryState(): Observable<MemoryState> { return this.api.get<MemoryState>('/v1/u/memory-state'); }
  submitTextEvent(payload: unknown): Observable<unknown> {
    return this.api.post('/v1/u/evento-texto', payload);
  }
}
