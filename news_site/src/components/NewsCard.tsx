import { useState } from 'react';
import type { NewsItem } from '../types/news';
import { parseSummary } from '../utils/parser';

interface NewsCardProps {
  news: NewsItem;
}

const mlLabels: Record<string, string> = {
  A: 'A国产替代', B: 'B英伟达链', C: 'C具身智能', D: 'D大厂应用',
};
const impactCls: Record<string, string> = {
  '大': 'impact-high', '中': 'impact-mid', '小': 'impact-low',
};
const impactColors: Record<string, string> = {
  '大': '#e94560', '中': '#ff9800', '小': '#bdbdbd',
};

export default function NewsCard({ news }: NewsCardProps) {
  const [expanded] = useState(true);
  const { mainSummary, analysis, conclusion } = parseSummary(news.summary);
  const mlParts = news.mainline ? news.mainline.split(/[,，]/).map(s => s.trim()).filter(Boolean) : [];
  const impCls = impactCls[news.impact] || 'impact-low';
  const impColor = impactColors[news.impact] || '#bdbdbd';

  const cleanAnalysis = analysis.replace(/^【产业链影响】/, '').trim();
  const cleanConclusion = conclusion.replace(/^【大白话结论】/, '').trim();

  return (
    <div className={`news-card ${impCls}`}>
      <div className="news-tags-row" style={{ borderLeftColor: impColor }}>
        <span className="tag-impact" style={{ background: impColor }}>{news.impact || '小'}</span>
        {mlParts.map(ml => (
          <span key={ml} className="tag-mainline">{mlLabels[ml] || ml}</span>
        ))}
      </div>

      <div className="news-title">{news.title}</div>

      {news.url && (
        <a className="news-url" href={news.url} target="_blank" rel="noopener noreferrer" onClick={e => e.stopPropagation()}>
          {news.url}
        </a>
      )}

      {expanded && (
        <>
          <div className="news-summary">{mainSummary}</div>
          {cleanAnalysis && (
            <div className="news-analysis-section">
              <div className="asection">🔗 {cleanAnalysis}</div>
            </div>
          )}
          {cleanConclusion && (
            <div className="news-conclusion-section">
              <span className="ctag">【大白话】</span>
              <div className="ctext">{cleanConclusion}</div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
