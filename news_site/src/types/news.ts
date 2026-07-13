export interface NewsItem {
  id: number;
  title: string;
  summary: string;
  mainline: string;
  impact: string;
  source: string;
  time: string;
  url?: string;
  story_tags?: string[];
}

export interface BreakthroughItem {
  id: number;
  date: string;
  title: string;
  summary: string;
  deepAnalysis: string;
}

export interface DayData {
  date: string;
  updated: string;
  count: number;
  news: NewsItem[];
  daily_summary?: Record<string, string>;
}

export interface DateIndex {
  dates: string[];
  count: number;
}

export type MainlineFilter = string[];
export type ImpactFilter = string[];
export type StoryTagFilter = string[];
export type ViewMode = 'daily' | 'breakthrough';
