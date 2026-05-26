import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { ApiService } from './api';
import { Report } from '../models';

interface ReportsApiResponse {
  success: boolean;
  reports: Report[];
  message: string;
}

@Injectable({ providedIn: 'root' })
export class ReportsService {
  constructor(private api: ApiService) {}

  list(): Observable<Report[]> {
    return this.api.get<ReportsApiResponse>('/v1/u/reports').pipe(
      map(r => r?.reports ?? (r as any) ?? [])
    );
  }
}
