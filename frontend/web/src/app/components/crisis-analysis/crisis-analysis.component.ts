import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { C2MApiService, CrisisProbabilityResponse } from '../../services/c2m-api.service';

@Component({
  selector: 'app-crisis-analysis',
  templateUrl: './crisis-analysis.component.html',
  styleUrls: ['./crisis-analysis.component.css']
})
export class CrisisAnalysisComponent implements OnInit {
  analysisForm: FormGroup;
  loading = false;
  result: CrisisProbabilityResponse | null = null;
  error: string | null = null;

  crisisLevels = [
    { value: 'breach', label: 'Breach de Dados' },
    { value: 'outage', label: 'Interrupção de Serviço' },
    { value: 'ransomware', label: 'Ransomware' },
    { value: 'ddos', label: 'DDoS Attack' },
    { value: 'insider_threat', label: 'Insider Threat' },
    { value: 'supply_chain', label: 'Supply Chain Attack' }
  ];

  colorMap = {
    'GREEN': '#4CAF50',
    'YELLOW': '#FFC107',
    'ORANGE': '#FF9800',
    'RED': '#F44336'
  };

  constructor(
    private fb: FormBuilder,
    private apiService: C2MApiService
  ) {
    this.analysisForm = this.fb.group({
      transcript: ['', [Validators.required, Validators.minLength(50)]],
      event_type: ['', Validators.required],
      governance_level: [3, [Validators.required, Validators.min(1), Validators.max(5)]]
    });
  }

  ngOnInit(): void {
    // Check API health
    this.apiService.healthCheck().subscribe(
      () => console.log('API connected'),
      (error) => console.error('API connection error:', error)
    );
  }

  analyzeEvent(): void {
    if (this.analysisForm.invalid) {
      this.error = 'Please fill all required fields correctly';
      return;
    }

    this.loading = true;
    this.error = null;

    this.apiService.calculateCrisisProbability(this.analysisForm.value).subscribe(
      (response) => {
        this.result = response;
        this.loading = false;
      },
      (error) => {
        this.error = error.error?.detail || 'Error analyzing event';
        this.loading = false;
      }
    );
  }

  getProbabilityPercentage(): number {
    return this.result ? Math.round(this.result.probability * 100) : 0;
  }

  getColorStyle(): string {
    if (!this.result) return '';
    return this.colorMap[this.result.color as keyof typeof this.colorMap] || '#9E9E9E';
  }

  reset(): void {
    this.analysisForm.reset();
    this.result = null;
    this.error = null;
  }
}
