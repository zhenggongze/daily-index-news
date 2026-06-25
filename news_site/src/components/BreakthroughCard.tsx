import { useState } from 'react';
import type { BreakthroughItem } from '../types/news';

interface Props {
  item: BreakthroughItem;
}

export default function BreakthroughCard({ item }: Props) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className={`bt-card ${expanded ? 'bt-expanded' : ''}`}>
      <div className="bt-header">
        <span className="bt-badge">⚡ 爆炸新闻</span>
        <span className="bt-date">{item.date}</span>
      </div>
      <div className="bt-title">{item.title}</div>
      <div className="bt-summary">{item.summary}</div>

      <button
        className="bt-toggle"
        onClick={() => setExpanded(!expanded)}
      >
        {expanded ? '收起分析 ▲' : '展开深度分析 ▼'}
      </button>

      {expanded && (
        <div className="bt-analysis">{item.deepAnalysis}</div>
      )}
    </div>
  );
}
