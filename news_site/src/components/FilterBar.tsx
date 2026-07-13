import type { MainlineFilter, ImpactFilter } from '../types/news';

interface FilterBarProps {
  mlFilter: MainlineFilter;
  impFilter: ImpactFilter;
  onMlChange: (f: MainlineFilter) => void;
  onImpChange: (f: ImpactFilter) => void;
}

const mlOptions: { key: string; label: string; color?: string }[] = [
  { key: 'A', label: 'A国产替代' },
  { key: 'B', label: 'B英伟达链' },
  { key: 'C', label: 'C具身智能' },
  { key: 'D', label: 'D大厂应用' },
  { key: '扩产', label: 'E扩产', color: '#4caf50' },
];

const impOptions: { key: string; label: string; cls: string }[] = [
  { key: 'high', label: '影响大', cls: 'impact-h' },
  { key: 'mid', label: '影响中', cls: 'impact-m' },
  { key: 'low', label: '影响小', cls: 'impact-l' },
];

function toggleItem(list: string[], key: string): string[] {
  if (list.includes(key)) {
    return list.filter(x => x !== key);
  }
  return [...list, key];
}

export default function FilterBar({ mlFilter, impFilter, onMlChange, onImpChange }: FilterBarProps) {
  return (
    <div className="filter-bar">
      <div className="filter-row">
        <span className="filter-label">主线：</span>
        <button
          className={`filter-tab ${mlFilter.length === 0 ? 'active' : ''}`}
          onClick={() => onMlChange([])}
        >全部</button>
        {mlOptions.map(t => {
          const active = mlFilter.includes(t.key);
          return (
            <button
              key={t.key}
              className={`filter-tab ${active ? 'active' : ''}`}
              style={t.color ? (active ? { background: t.color, borderColor: t.color, color: '#fff' } : { borderColor: t.color, color: t.color }) : undefined}
              onClick={() => onMlChange(toggleItem(mlFilter, t.key))}
            >
              {t.label}
            </button>
          );
        })}
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
    </div>
  );
}
