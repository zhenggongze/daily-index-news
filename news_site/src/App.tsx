import { useState, useEffect, useMemo, useCallback } from 'react';
import type { NewsItem, DayData, DateIndex, MainlineFilter, ImpactFilter } from './types/news';
import { fmtDateCN, parseDate } from './utils/date';
import { filterByMainline, filterByImpact } from './utils/filter';
import Header from './components/Header';
import DateNav from './components/DateNav';
import StatsBar from './components/StatsBar';
import FilterBar from './components/FilterBar';
import NewsList from './components/NewsList';

const BASE = import.meta.env.BASE_URL;

export default function App() {
  const [allNews, setAllNews] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentDateStr, setCurrentDateStr] = useState('');
  const [availableDates, setAvailableDates] = useState<string[]>([]);
  const [mlFilter, setMlFilter] = useState<MainlineFilter>([]);
  const [impFilter, setImpFilter] = useState<ImpactFilter>(['high', 'mid']);

  useEffect(() => {
    fetch(`${BASE}data/index.json?t=${Date.now()}`)
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
    setCurrentDateStr(ds);
    fetch(`${BASE}data/${ds}.json?t=${Date.now()}`)
      .then(r => r.json())
      .then((data: DayData) => {
        setAllNews(data.news);
        setLoading(false);
      })
      .catch(() => {
        setAllNews([]);
        setLoading(false);
      });
  }, []);

  const changeDate = useCallback((delta: number) => {
    const idx = availableDates.indexOf(currentDateStr);
    const newIdx = idx + delta;
    if (newIdx >= 0 && newIdx < availableDates.length) {
      loadDate(availableDates[newIdx]);
    }
  }, [availableDates, currentDateStr, loadDate]);

  const goToday = useCallback(() => {
    if (availableDates.length > 0) {
      loadDate(availableDates[availableDates.length - 1]);
    }
  }, [availableDates, loadDate]);

  const filteredNews = useMemo(() => {
    let result = filterByMainline(allNews, mlFilter);
    result = filterByImpact(result, impFilter);
    return result;
  }, [allNews, mlFilter, impFilter]);

  const stats = useMemo(() => {
    const high = allNews.filter(n => (n.impact || '').includes('大')).length;
    const mid = allNews.filter(n => (n.impact || '').includes('中')).length;
    const low = allNews.filter(n => !(n.impact || '').includes('大') && !(n.impact || '').includes('中')).length;
    return { total: allNews.length, high, mid, low };
  }, [allNews]);

  const currentIdx = availableDates.indexOf(currentDateStr);
  const hasPrev = currentIdx > 0;
  const hasNext = currentIdx < availableDates.length - 1;

  const dateLabel = currentDateStr ? fmtDateCN(parseDate(currentDateStr)) : '';

  return (
    <div>
      <Header dateStr={currentDateStr} />

      <DateNav
          dateStr={currentDateStr}
          availableDates={availableDates}
          onPrev={() => changeDate(-1)}
          onNext={() => changeDate(1)}
          onToday={goToday}
          onSelect={loadDate}
          hasPrev={hasPrev}
          hasNext={hasNext}
        />

      <div className="container">
        <FilterBar
          mlFilter={mlFilter}
          impFilter={impFilter}
          onMlChange={setMlFilter}
          onImpChange={setImpFilter}
        />

        {loading ? (
          <div className="loading">
            <div className="spinner" />
            <p>正在加载...</p>
          </div>
        ) : (
          <NewsList news={filteredNews} dateLabel={dateLabel} />
        )}
      </div>
    </div>
  );
}
