import type { NewsItem, MainlineFilter, ImpactFilter } from '../types/news';

// 故事线标签作为主线扩展选项（用 story_tags 字段过滤）
const STORY_AS_MAINLINE = ['扩产', '涨价', '降价', '技术', '业绩', '需求', '供给'];

export function filterByMainline(news: NewsItem[], filter: MainlineFilter): NewsItem[] {
  if (filter.length === 0) return news;
  return news.filter(n => {
    // A/B/C/D 用 mainline 字段过滤
    const mlMatch = filter.some(f => !STORY_AS_MAINLINE.includes(f) && n.mainline.includes(f));
    // 扩产/涨价等 用 story_tags 字段过滤
    const storyMatch = filter.some(f => STORY_AS_MAINLINE.includes(f) && (n.story_tags || []).includes(f));
    return mlMatch || storyMatch;
  });
}

export function filterByImpact(news: NewsItem[], filter: ImpactFilter): NewsItem[] {
  if (filter.length === 0) return news;
  const results: NewsItem[] = [];
  if (filter.includes('high')) results.push(...news.filter(n => (n.impact || '').includes('大')));
  if (filter.includes('mid')) results.push(...news.filter(n => (n.impact || '').includes('中')));
  if (filter.includes('low')) results.push(...news.filter(n => !(n.impact || '').includes('大') && !(n.impact || '').includes('中')));
  return results;
}
