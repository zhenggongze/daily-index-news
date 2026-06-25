import type { BreakthroughItem } from '../types/news';
import BreakthroughCard from './BreakthroughCard';

interface Props {
  items: BreakthroughItem[];
}

export default function BreakthroughList({ items }: Props) {
  return (
    <div>
      <div className="bt-section-header">
        <span className="bt-section-icon">⚡</span>
        <span>AI算力产业链 爆炸新闻汇编</span>
        <span className="bt-section-sub">2026年3月-6月 · 共{items.length}条</span>
      </div>
      {items.map(item => (
        <BreakthroughCard key={item.id} item={item} />
      ))}
    </div>
  );
}
