interface HeaderProps {
  dateStr: string;
}

export default function Header({ dateStr }: HeaderProps) {
  return (
    <header className="header">
      <div className="header-inner">
        <div>
          <h1 className="header-title">AI<span>算力</span>产业链资讯</h1>
          <p className="header-subtitle">每日精选 · 上游材料颠覆 · 中游芯片革新 · 下游应用爆发</p>
        </div>
        <div className="header-meta">
          <span className="header-date">{dateStr}</span>
          <span className="header-author">Designed by 郑公泽 & 窦斯琪</span>
        </div>
      </div>
    </header>
  );
}
