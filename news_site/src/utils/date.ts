export function fmtDate(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

export function fmtDateCN(d: Date): string {
  const days = ['日', '一', '二', '三', '四', '五', '六'];
  return `${d.getMonth() + 1}月${d.getDate()}日 · 周${days[d.getDay()]}`;
}

export function parseDate(str: string): Date {
  const p = str.split('-');
  return new Date(parseInt(p[0]), parseInt(p[1]) - 1, parseInt(p[2]));
}

export function getMonthDays(year: number, month: number): { day: number; dateStr: string }[] {
  const firstDay = new Date(year, month, 1);
  const lastDay = new Date(year, month + 1, 0);
  const startWeekday = (firstDay.getDay() + 6) % 7;
  const days: { day: number; dateStr: string }[] = [];
  for (let i = 0; i < startWeekday; i++) {
    days.push({ day: 0, dateStr: '' });
  }
  for (let d = 1; d <= lastDay.getDate(); d++) {
    const date = new Date(year, month, d);
    days.push({ day: d, dateStr: fmtDate(date) });
  }
  return days;
}
