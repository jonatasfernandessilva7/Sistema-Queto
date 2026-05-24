import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface AudioUploadResponse {
  audio_id: string;
  filename: string;
  status: string;
  timestamp: string;
}

export interface CrisisProbabilityRequest {
  transcript: string;
  event_type: string;
  corporate_documents?: string[];
  governance_level?: number;
}

export interface CrisisProbabilityResponse {
  probability: number;
  iso_classification: string;
  color: string;
  level: string;
  conformity_factor: number;
  reasoning: string;
  matched_standards: any[];
}

export interface ConformityReportResponse {
  conformity_factor: number;
  corporate_alignment: number;
  iso_alignment: number;
  matched_standards: any[];
  similar_documents: any[];
}

export interface ReportResponse {
  report_id: string;
  content: string;
  crisis_level: string;
  recommendations: string[];
  timestamp: string;
}

@Injectable({
  providedIn: 'root'
})
export class C2MApiService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) { }

  /**
   * Upload audio file for processing
   */
  uploadAudio(file: File): Observable<AudioUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post<AudioUploadResponse>(
      `${this.apiUrl}/audio/upload`,
      formData
    );
  }

  /**
   * Get audio processing status
   */
  getAudioStatus(audioId: string): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/audio/status/${audioId}`);
  }

  /**
   * Calculate crisis probability with C2M algorithm
   */
  calculateCrisisProbability(request: CrisisProbabilityRequest): Observable<CrisisProbabilityResponse> {
    return this.http.post<CrisisProbabilityResponse>(
      `${this.apiUrl}/crisis/probability`,
      request
    );
  }

  /**
   * Get conformity analysis (conformidade C)
   */
  getConformityAnalysis(transcript: string, documents?: string[]): Observable<ConformityReportResponse> {
    return this.http.post<ConformityReportResponse>(
      `${this.apiUrl}/vector/conformity`,
      {
        transcript,
        corporate_documents: documents
      }
    );
  }

  /**
   * Search for similar ISO documents
   */
  searchISODocuments(query: string, isoStandard?: string): Observable<any[]> {
    const params: any = {};
    if (isoStandard) {
      params['iso_standard'] = isoStandard;
    }
    return this.http.post<any[]>(
      `${this.apiUrl}/vector/iso-search`,
      { query },
      { params }
    );
  }

  /**
   * Generate crisis report
   */
  generateReport(eventTranscript: string, crisisLevel: string): Observable<ReportResponse> {
    return this.http.post<ReportResponse>(
      `${this.apiUrl}/reports/generate`,
      {
        transcript: eventTranscript,
        crisis_level: crisisLevel
      }
    );
  }

  /**
   * Get list of reports
   */
  getReports(): Observable<ReportResponse[]> {
    return this.http.get<ReportResponse[]>(`${this.apiUrl}/reports/list`);
  }

  /**
   * Submit feedback (RLHF)
   */
  submitFeedback(analysisId: string, feedback: any): Observable<any> {
    return this.http.post(
      `${this.apiUrl}/feedback/submit`,
      {
        analysis_id: analysisId,
        ...feedback
      }
    );
  }

  /**
   * Health check
   */
  healthCheck(): Observable<any> {
    return this.http.get(`${this.apiUrl}/health`);
  }
}
