import { ChevronLeft, ChevronRight } from 'lucide-react';
import { fmtDateCN, parseDate } from '../utils/date';

interface DateNavProps {
  dateStr: string;
  availableDates: string[];
  onPrev: () => void;
  onNext: () => void;
  onToday: () => void;
  onSelect: (ds: string) => void;
  hasPrev: boolean;
  hasNext: boolean;
}

export default function DateNav({ dateStr, availableDates, onPrev, onNext, onToday, onSelect, hasPrev, hasNext }: DateNavProps) {
  const label = dateStr ? fmtDateCN(parseDate(dateStr)) : '';

  return (
    <div className="date-nav">
      <button className="nav-btn" onClick={onPrev} disabled={!hasPrev}>
        <ChevronLeft size={16} />
      </button>

      <select
        className="date-select"
        value={dateStr}
        onChange={e => onSelect(e.target.value)}
      >
        {availableDates.map(ds => (
          <option key={ds} value={ds}>{fmtDateCN(parseDate(ds))}</option>
        ))}
      </select>

      <button className="nav-btn" onClick={onNext} disabled={!hasNext}>
        <ChevronRight size={16} />
      </button>
      <button className="today-btn" onClick={onToday}>今天</button>
    </div>
  );
}
