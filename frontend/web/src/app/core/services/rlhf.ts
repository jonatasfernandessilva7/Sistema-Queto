import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from './api';
import { FeedbackCreate, RlhfWeights } from '../models';

@Injectable({ providedIn: 'root' })
export class RlhfService {
  constructor(private api: ApiService) {}
  weights(): Observable<{ weights: RlhfWeights }> { return this.api.get('/v1/u/rlhf/weights'); }
  adjustments(limit = 50): Observable<unknown> { return this.api.get(`/v1/u/rlhf/adjustments?limit=${limit}`); }
  submitFeedback(fb: FeedbackCreate): Observable<unknown> { return this.api.post('/v1/u/rlhf/feedback', fb); }
  process(min = 10): Observable<unknown> { return this.api.post(`/v1/u/rlhf/process?min_feedbacks=${min}`); }
  resetWeights(): Observable<unknown> { return this.api.post('/v1/u/rlhf/reset-weights'); }
}
