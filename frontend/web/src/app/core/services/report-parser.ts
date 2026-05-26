/**
 * ReportParserService
 *
 * Extrai dados estruturados C2M do campo `relatorio` (texto UTF-8).
 * O relatório gerado pelo backend contém seções como:
 *   PROBABILIDADE DE CRISE CIBERNÉTICA:  34.21%
 *   ISO 22324: LARANJA
 *   Pearson: sentimento=0.8821 | maturidade=0.3210 ...
 *   Percentis: p10=0.1200 | p25=0.2100 | p50=0.3400 ...
 *
 * Se o campo é binário (PDF), retorna valores nulos e is_binary_pdf=true.
 */
import { Injectable } from '@angular/core';
import { Report, ReportDetail, PearsonEntry, PercentileEntry, IsoLevel, Priority } from '../models';

@Injectable({ providedIn: 'root' })
export class ReportParserService {

  parse(r: Report): ReportDetail {
    const text = r.relatorio ?? '';
    const isBinary = text.startsWith('[PDF binário');

    if (isBinary) {
      return {
        ...r,
        probability_pct: null, iso_level: null, iso_color: '#718096',
        priority: null, pearson: [], percentiles: [], ci_lower: null,
        ci_upper: null, std_deviation: null, conformity_factor: null,
        sentiment_label: null, sentiment_polarity: null,
        risk_agents_count: null, is_binary_pdf: true,
      };
    }

    return {
      ...r,
      probability_pct:    this.extractFloat(text, /PROBABILIDADE[^:]*:\s*([\d.]+)%/i) ??
                          this.extractFloat(text, /mean_probability_pct["\s:]+(\d+\.?\d*)/i),
      iso_level:          this.extractIsoLevel(text),
      iso_color:          this.isoColor(this.extractIsoLevel(text)),
      priority:           this.extractPriority(text),
      pearson:            this.extractPearson(text),
      percentiles:        this.extractPercentiles(text),
      ci_lower:           this.extractFloat(text, /IC\s*95[^:]*lower["\s:=]+([\d.]+)/i) ??
                          this.extractFloat(text, /lower["\s:=]+([\d.]+)/i),
      ci_upper:           this.extractFloat(text, /IC\s*95[^:]*upper["\s:=]+([\d.]+)/i) ??
                          this.extractFloat(text, /upper["\s:=]+([\d.]+)/i),
      std_deviation:      this.extractFloat(text, /(?:σ|std_deviation|desvio\s+padrão)["\s:=]+([\d.]+)/i),
      conformity_factor:  this.extractFloat(text, /conformity_factor["\s:=]+([\d.]+)/i) ??
                          this.extractFloat(text, /FATOR DE CONFORMIDADE[^:]*:\s*([\d.]+)/i),
      sentiment_label:    this.extractStr(text, /SENTIMENTO[^:]*:\s*(\w+)/i),
      sentiment_polarity: this.extractFloat(text, /polarity[=:\s]+([-\d.]+)/i),
      risk_agents_count:  this.extractInt(text, /AGENTES DE RISCO[^:]*:\s*(\d+)/i),
      is_binary_pdf:      false,
    };
  }

  parseAll(reports: Report[]): ReportDetail[] {
    return reports.map(r => this.parse(r));
  }

  // ── helpers ────────────────────────────────────────────────────────────────

  private extractFloat(text: string, re: RegExp): number | null {
    const m = text.match(re);
    return m ? parseFloat(m[1]) : null;
  }

  private extractInt(text: string, re: RegExp): number | null {
    const m = text.match(re);
    return m ? parseInt(m[1], 10) : null;
  }

  private extractStr(text: string, re: RegExp): string | null {
    const m = text.match(re);
    return m ? m[1].trim() : null;
  }

  private extractIsoLevel(text: string): IsoLevel | null {
    const m = text.match(/ISO\s*22324[^:]*:\s*(VERDE|AMARELO|LARANJA|VERMELHO)/i) ??
              text.match(/Nível[^:]*:\s*(VERDE|AMARELO|LARANJA|VERMELHO)/i) ??
              text.match(/\b(VERDE|AMARELO|LARANJA|VERMELHO)\b/i);
    return m ? (m[1].toUpperCase() as IsoLevel) : null;
  }

  private extractPriority(text: string): Priority | null {
    const m = text.match(/Prioridade[^:]*:\s*(Crítico|Alta|Moderada|Baixa|Desconhecida)/i);
    if (!m) return null;
    const map: Record<string, Priority> = {
      'crítico': 'Crítico', 'alto': 'Alta', 'alta': 'Alta',
      'moderada': 'Moderada', 'moderado': 'Moderada',
      'baixo': 'Baixa', 'baixa': 'Baixa', 'desconhecida': 'Desconhecida',
    };
    return map[m[1].toLowerCase()] ?? null;
  }

  private extractPearson(text: string): PearsonEntry[] {
    // "sentimento: r=0.8821" ou "sentimento=0.8821"
    const labelMap: Record<string, string> = {
      sentimento: 'Sentimento', maturidade: 'Maturidade',
      continuidade: 'Continuidade', historico: 'Histórico',
      conformidade: 'Conformidade',
    };
    const results: PearsonEntry[] = [];
    // block pattern: "Pearson: sentimento=0.88 | maturidade=0.32 ..."
    const blockM = text.match(/Pearson[^:\n]*:([^\n]+)/i);
    if (blockM) {
      const pairs = blockM[1].matchAll(/([\w]+)[=:\s]+([-\d.]+)/g);
      for (const p of pairs) {
        const key = p[1].toLowerCase();
        if (labelMap[key]) results.push({ label: labelMap[key], value: parseFloat(p[2]) });
      }
    }
    // fallback: individual lines "sentimento: r=0.88"
    if (!results.length) {
      for (const [key, label] of Object.entries(labelMap)) {
        const m = text.match(new RegExp(`${key}[^:=\\n]*[=:r]\\s*([-\\d.]+)`, 'i'));
        if (m) results.push({ label, value: parseFloat(m[1]) });
      }
    }
    return results;
  }

  private extractPercentiles(text: string): PercentileEntry[] {
    const results: PercentileEntry[] = [];
    const blockM = text.match(/Percentis[^:\n]*:([^\n]+)/i);
    if (blockM) {
      const pairs = blockM[1].matchAll(/(p\d+)[=:\s]+([\d.]+)/gi);
      for (const p of pairs) results.push({ label: p[1].toUpperCase(), value: parseFloat(p[2]) * 100 });
    }
    return results;
  }

  private isoColor(level: IsoLevel | null): string {
    const map: Record<string, string> = {
      VERDE: '#27AE60', AMARELO: '#F5D623', LARANJA: '#F5A623', VERMELHO: '#E84545',
    };
    return map[level ?? ''] ?? '#718096';
  }
}
