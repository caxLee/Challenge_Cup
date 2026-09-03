import type { TaskResponse } from "../types/security";

const json = (value: unknown) => JSON.stringify(value ?? {}, null, 2);

export function RequestDetailCard({ task }: { task: TaskResponse | null }) {
  if (!task) return <section className="panel empty-card">提交演示请求后查看请求详情。</section>;
  return (
    <section className="panel">
      <div className="panel-heading">请求详情</div>
      <div className="detail-grid">
        <div><label>目标</label><p>{task.request.goal}</p></div>
        <div><label>工具</label><p className="mono">{task.request.tool}</p></div>
        <div><label>请求用户</label><p>{task.request.user_id}</p></div>
        <div><label>用户角色</label><p>{task.request.user_role}</p></div>
      </div>
      <JsonBlock title="arguments" value={task.request.arguments} />
      <JsonBlock title="sources" value={task.request.sources} />
      <JsonBlock title="destination" value={task.request.destination} />
    </section>
  );
}

function JsonBlock({ title, value }: { title: string; value: unknown }) {
  return <div className="json-block"><label>{title}</label><pre>{json(value)}</pre></div>;
}
