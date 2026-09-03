import { useEffect, useState } from "react";
import { getTaskEvents } from "../api";
import type { TaskEvent } from "../types/security";

interface Props {
  taskId: string | undefined;
  refreshKey: number;
  onEventsChange?: (events: TaskEvent[]) => void;
}

export function EventTimeline({ taskId, refreshKey, onEventsChange }: Props) {
  const [events, setEvents] = useState<TaskEvent[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!taskId) {
      setEvents([]);
      setError(null);
      setLoading(false);
      onEventsChange?.([]);
      return;
    }

    const loadEvents = async () => {
      setLoading(true);
      setError(null);
      try {
        const nextEvents = await getTaskEvents(taskId);
        setEvents(nextEvents);
        onEventsChange?.(nextEvents);
      } catch (reason) {
        setError(reason instanceof Error ? reason.message : "事件加载失败");
      } finally {
        setLoading(false);
      }
    };

    void loadEvents();
  }, [taskId, refreshKey, onEventsChange]);

  return <section className="panel"><div className="panel-heading">事件时间线</div>{loading ? <p className="muted">正在加载事件…</p> : error ? <div className="inline-error"><strong>事件加载失败</strong><br />{error}</div> : events.length === 0 ? <p className="muted">暂无事件</p> : <div className="timeline">{events.map((event, index) => <div className="timeline-item" key={`${event.timestamp}-${index}`}><span className={`timeline-dot dot-${event.status}`} /><div><div className="timeline-meta"><strong>{event.event}</strong><time>{new Date(event.timestamp).toLocaleString("zh-CN")}</time></div><p>{event.message}</p>{event.error && <small className="error-text">{event.error}</small>}</div></div>)}</div>}</section>;
}
