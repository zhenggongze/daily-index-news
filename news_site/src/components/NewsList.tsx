import type { NewsItem } from '../types/news';
import NewsCard from './NewsCard';

interface NewsListProps {
  news: NewsItem[];
  dateLabel: string;
}

export default function NewsList({ news, dateLabel }: NewsListProps) {
  if (news.length === 0) {
    return (
      <div className="empty-state">
        <div className="icon">🔍</div>
        <p>没有符合条件的新闻</p>
      </div>
    );
  }

  return (
    <div>
      <div className="day-header">
        {dateLabel}
        <span className="day-count">{news.length}条</span>
      </div>
      {news.map(n => (
        <NewsCard key={n.id} news={n} />
      ))}
    </div>
  );
}
