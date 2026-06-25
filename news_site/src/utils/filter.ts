import type { NewsItem, MainlineFilter, ImpactFilter } from '../types/news';

export function filterByMainline(news: NewsItem[], filter: MainlineFilter): NewsItem[] {
  if (filter.length === 0) return news;
  return news.filter(n => filter.some(ml => n.mainline.includes(ml)));
}

export function filterByImpact(news: NewsItem[], filter: ImpactFilter): NewsItem[] {
  if (filter.length === 0) return news;
  const results: NewsItem[] = [];
  if (filter.includes('high')) results.push(...news.filter(n => (n.impact || '').includes('大')));
  if (filter.includes('mid')) results.push(...news.filter(n => (n.impact || '').includes('中')));
  if (filter.includes('low')) results.push(...news.filter(n => !(n.impact || '').includes('大') && !(n.impact || '').includes('中')));
  return results;
}
