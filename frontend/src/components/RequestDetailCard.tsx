import type { TaskRequest, TaskResponse } from "../types/security";

const json = (value: unknown) => JSON.stringify(value ?? {}, null, 2);

export function RequestDetailCard({ task, draft }: { task: TaskResponse | null; draft?: TaskRequest | null }) {
  const request = task?.request ?? draft;
  if (!request) return <section className="panel empty-card">提交演示请求后查看请求详情。</section>;
  return (
    <section className="panel">
      <div className="panel-heading">请求详情 {!task && <span className="muted">待提交</span>}</div>
      <div className="detail-grid">
        <div><label>目标</label><p>{request.goal}</p></div>
        <div><label>工具</label><p className="mono">{request.tool}</p></div>
        <div><label>请求用户</label><p>{request.user_id}</p></div>
        <div><label>用户角色</label><p>{request.user_role}</p></div>
      </div>
      <JsonBlock title="arguments" value={request.arguments} />
      <JsonBlock title="sources" value={request.sources} />
      <JsonBlock title="destination" value={request.destination} />
    </section>
  );
}

function JsonBlock({ title, value }: { title: string; value: unknown }) {
  return <div className="json-block"><label>{title}</label><pre>{json(value)}</pre></div>;
}
