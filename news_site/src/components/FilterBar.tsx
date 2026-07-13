import type { MainlineFilter, ImpactFilter, StoryTagFilter } from '../types/news';

interface FilterBarProps {
  mlFilter: MainlineFilter;
  impFilter: ImpactFilter;
  storyFilter: StoryTagFilter;
  onMlChange: (f: MainlineFilter) => void;
  onImpChange: (f: ImpactFilter) => void;
  onStoryChange: (f: StoryTagFilter) => void;
}

const mlOptions: { key: string; label: string }[] = [
  { key: 'A', label: 'A国产替代' },
  { key: 'B', label: 'B英伟达链' },
  { key: 'C', label: 'C具身智能' },
  { key: 'D', label: 'D大厂应用' },
];

const impOptions: { key: string; label: string; cls: string }[] = [
  { key: 'high', label: '影响大', cls: 'impact-h' },
  { key: 'mid', label: '影响中', cls: 'impact-m' },
  { key: 'low', label: '影响小', cls: 'impact-l' },
];

// 故事线标签配置：标签名 -> 颜色
const storyOptions: { key: string; color: string }[] = [
  { key: '扩产', color: '#4caf50' },
  { key: '涨价', color: '#e94560' },
  { key: '降价', color: '#ff9800' },
  { key: '技术', color: '#2196f3' },
  { key: '国产替代', color: '#9c27b0' },
  { key: '政策', color: '#b71c1c' },
  { key: '业绩', color: '#009688' },
  { key: '并购', color: '#e91e63' },
  { key: '需求', color: '#03a9f4' },
  { key: '供给', color: '#fdd835' },
  { key: '风险', color: '#757575' },
];

function toggleItem(list: string[], key: string): string[] {
  if (list.includes(key)) {
    return list.filter(x => x !== key);
  }
  return [...list, key];
}

export default function FilterBar({ mlFilter, impFilter, storyFilter, onMlChange, onImpChange, onStoryChange }: FilterBarProps) {
  return (
    <div className="filter-bar">
      <div className="filter-row">
        <span className="filter-label">主线：</span>
        <button
          className={`filter-tab ${mlFilter.length === 0 ? 'active' : ''}`}
          onClick={() => onMlChange([])}
        >全部</button>
        {mlOptions.map(t => (
          <button
            key={t.key}
            className={`filter-tab ${mlFilter.includes(t.key) ? 'active' : ''}`}
            onClick={() => onMlChange(toggleItem(mlFilter, t.key))}
          >
            {t.label}
          </button>
        ))}
      </div>
      <div className="filter-row">
        <span className="filter-label">影响：</span>
        <button
          className={`filter-tab ${impFilter.length === 0 ? 'active' : ''}`}
          onClick={() => onImpChange([])}
        >全部</button>
        {impOptions.map(t => (
          <button
            key={t.key}
            className={`filter-tab ${t.cls} ${impFilter.includes(t.key) ? 'active' : ''}`}
            onClick={() => onImpChange(toggleItem(impFilter, t.key))}
          >
            {t.label}
          </button>
        ))}
      </div>
      <div className="filter-row filter-row-story">
        <span className="filter-label">故事线：</span>
        <button
          className={`filter-tab story-tab-all ${storyFilter.length === 0 ? 'active' : ''}`}
          onClick={() => onStoryChange([])}
        >全部</button>
        {storyOptions.map(t => {
          const active = storyFilter.includes(t.key);
          return (
            <button
              key={t.key}
              className={`filter-tab story-tab ${active ? 'active' : ''}`}
              style={active ? { background: t.color, borderColor: t.color, color: '#fff' } : { borderColor: t.color, color: t.color }}
              onClick={() => onStoryChange(toggleItem(storyFilter, t.key))}
            >
              {t.key}
            </button>
          );
        })}
      </div>
    </div>
  );
}
