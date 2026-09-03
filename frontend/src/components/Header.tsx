interface HeaderProps {
  apiOnline: boolean | null;
  onReset: () => void;
}

export function Header({ apiOnline, onReset }: HeaderProps) {
  return (
    <header className="app-header">
      <div>
        <div className="eyebrow">SECURITY OPERATIONS CENTER</div>
        <h1>Agent 安全审批控制台</h1>
      </div>
      <div className="header-actions">
        <span className={`connection ${apiOnline === null ? "checking" : apiOnline ? "online" : "offline"}`}>
          <i /> {apiOnline === true ? "API 已连接" : apiOnline === false ? "API 未连接" : "正在检查 API"}
        </span>
        <button className="button secondary" onClick={onReset}>重置演示</button>
      </div>
    </header>
  );
}
