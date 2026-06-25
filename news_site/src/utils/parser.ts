export interface ParsedSummary {
  mainSummary: string;
  impact: string;
  analysis: string;
  conclusion: string;
}

export function parseSummary(summary: string): ParsedSummary {
  const conclusionMatch = summary.match(/【大白话结论】[^【]*/);
  const conclusion = conclusionMatch ? conclusionMatch[0].trim() : '';
  const analysisMatch = summary.match(/【产业链影响】[^【]*/);
  const analysis = analysisMatch ? analysisMatch[0].trim() : '';
  const impactMatch = summary.match(/【影响程度】[^【]*/);
  const impact = impactMatch ? impactMatch[0].trim() : '';

  let mainSummary = summary;
  if (impactMatch) mainSummary = mainSummary.replace(impactMatch[0], '');
  if (analysisMatch) mainSummary = mainSummary.replace(analysisMatch[0], '');
  if (conclusionMatch) mainSummary = mainSummary.replace(conclusionMatch[0], '');

  return { mainSummary: mainSummary.trim(), impact, analysis, conclusion };
}
