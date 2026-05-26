export type IsoLevel = 'VERDE' | 'AMARELO' | 'LARANJA' | 'VERMELHO' | 'DESCONHECIDO';
export type Priority = 'Baixa' | 'Moderada' | 'Alta' | 'Crítico' | 'Desconhecida';

// ── Chart entries ──
export interface BarEntry { label: string; value: number; color?: string; }

export interface MonteCarloResult {
  mean_probability: number;
  mean_probability_pct: number;
  std_deviation: number;
  confidence_interval_95: { lower: number; upper: number };
  percentiles: Record<string, number>;
  pearson_correlations: Record<string, number | null>;
  iso_22324: { level: IsoLevel; color: string; action: string };
  priority: Priority;
}

export interface EventModel {
  id?: number;
  tipo: string;
  origem: string;
  timestamp: string;
  detalhes?: Record<string, unknown>;
}

export interface C2MAnalysis {
  status: string;
  mean_probability: number;
  mean_probability_pct: number;
  std_deviation: number;
  confidence_interval_95: { lower: number; upper: number };
  percentiles: Record<string, number>;
  pearson_correlations: Record<string, number | null>;
  priority: Priority;
  iso_22324: { level: IsoLevel; color: string; action: string };
  conformity_factor: number;
  sentiment: { polarity: number; interpretation: string; subjectivity: number };
  risk_agents: RiskAgent[];
  organizational_context: OrgContext;
  decision_tree: { is_potential_crisis: boolean; confidence_score: number; reasoning: string };
  analysis_summary: string;
  crisis_signals?: { keywords_found: string[] };
  low_risk_assessment: boolean;
}

export interface RiskAgent {
  name: string;
  category: string;
  severity: number;
  impact_chain: string[];
  mitigation: string;
}

export interface OrgContext {
  maturity_level: number;
  has_risk_plan: boolean;
  has_crisis_plan: boolean;
  has_continuity_plan: boolean;
  has_recovery_plan: boolean;
  historical_similar_events: number;
  formal_governance: boolean;
}

export interface Document {
  id: number;
  filename: string;
}

/** Relatório persistido no banco — campo relatorio é texto UTF-8 ou PDF [binário] */
export interface Report {
  id: number;
  documento_id: number | null;
  relatorio: string;
  relatorio_size_bytes?: number;
  timestamp: string;
}

/** Relatório enriquecido: metadados C2M extraídos do texto do relatório */
export interface ReportDetail extends Report {
  probability_pct:   number | null;
  iso_level:         IsoLevel | null;
  iso_color:         string;
  priority:          Priority | null;
  pearson:           PearsonEntry[];
  percentiles:       PercentileEntry[];
  ci_lower:          number | null;
  ci_upper:          number | null;
  std_deviation:     number | null;
  conformity_factor: number | null;
  sentiment_label:   string | null;
  sentiment_polarity: number | null;
  risk_agents_count: number | null;
  is_binary_pdf:     boolean;
}

export interface PearsonEntry  { label: string; value: number; }
export interface PercentileEntry { label: string; value: number; }

export interface RlhfWeights {
  decision_tree_sentiment: number;
  decision_tree_type: number;
  decision_tree_governance: number;
  decision_tree_maturity: number;
  crisis_threshold: number;
  monte_carlo_simulations: number;
  monte_carlo_sentiment_modifier: number;
}

export interface FeedbackCreate {
  report_id: string;
  actual_crisis: boolean;
  c2m_probability_comment: 'too_high' | 'too_low' | 'accurate';
  priority_feedback?: string;
  usefulness_score?: number;
  comments?: string;
}

export interface MemoryState {
  sistemas: Record<string, string>;
  historico_eventos: EventModel[];
}

export interface AudioProcessResult {
  status: number;
  message: string;
  emotion?: string;
  num_voices?: string;
  mean_probability?: number;
  priority?: string;
  iso_22324?: { level: IsoLevel; color: string; action: string };
  analysis_summary?: string;
  pearson_correlations?: Record<string, number | null>;
  percentiles?: Record<string, number>;
  conformity_factor?: number;
  std_deviation?: number;
  confidence_interval_95?: { lower: number; upper: number };
  sentiment?: { polarity: number; interpretation: string; subjectivity: number };
  organizational_context?: OrgContext;
}
