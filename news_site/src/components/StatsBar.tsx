interface StatsBarProps {
  total: number;
  high: number;
  mid: number;
  low: number;
}

export default function StatsBar({ total, high, mid, low }: StatsBarProps) {
  return (
    <div className="stats-bar">
      <div className="stat-item">
        <div className="num">{total}</div>
        <div className="label">总条数</div>
      </div>
      <div className="stat-item high">
        <div className="num">{high}</div>
        <div className="label">影响大</div>
      </div>
      <div className="stat-item mid">
        <div className="num">{mid}</div>
        <div className="label">影响中</div>
      </div>
      <div className="stat-item low">
        <div className="num">{low}</div>
        <div className="label">影响小</div>
      </div>
    </div>
  );
}
