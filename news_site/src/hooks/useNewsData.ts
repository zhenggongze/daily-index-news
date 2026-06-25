import { useState, useEffect, useCallback } from 'react';
import type { DayData, DateIndex, NewsItem } from '../types/news';

export function useNewsData() {
  const [news, setNews] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [dateStr, setDateStr] = useState<string>('');
  const [count, setCount] = useState(0);
  const [availableDates, setAvailableDates] = useState<string[]>([]);

  useEffect(() => {
    fetch(`/data/index.json?t=${Date.now()}`)
      .then(r => r.json())
      .then((idx: DateIndex) => {
        setAvailableDates(idx.dates);
        if (idx.dates.length > 0) {
          loadDate(idx.dates[idx.dates.length - 1]);
        } else {
          setLoading(false);
        }
      })
      .catch(() => setLoading(false));
  }, []);

  const loadDate = useCallback((ds: string) => {
    setLoading(true);
    setDateStr(ds);
    fetch(`/data/${ds}.json?t=${Date.now()}`)
      .then(r => r.json())
      .then((data: DayData) => {
        setNews(data.news);
        setCount(data.count);
        setLoading(false);
      })
      .catch(() => {
        setNews([]);
        setCount(0);
        setLoading(false);
      });
  }, []);

  return { news, loading, dateStr, count, availableDates, loadDate };
}
