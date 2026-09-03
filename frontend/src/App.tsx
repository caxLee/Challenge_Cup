import { useEffect, useState } from "react";
import { createTask, getAuditRecords, getDemoRequests, getHealth } from "./api";
import type { AuditRecord, DemoRequest, TaskEvent, TaskResponse } from "./types/security";
import { AuditPanel } from "./components/AuditPanel";
import { ApprovalPanel } from "./components/ApprovalPanel";
import { DemoScenarioList } from "./components/DemoScenarioList";
import { EventTimeline } from "./components/EventTimeline";
import { Header } from "./components/Header";
import { RequestDetailCard } from "./components/RequestDetailCard";
import { RiskAssessmentCard } from "./components/RiskAssessmentCard";
import { StatusBanner } from "./components/StatusBanner";

export default function App() {
  const [demos, setDemos] = useState<DemoRequest[]>([]);
  const [selectedDemo, setSelectedDemo] = useState<number | null>(null);
  const [task, setTask] = useState<TaskResponse | null>(null);
  const [events, setEvents] = useState<TaskEvent[]>([]);
  const [auditRecords, setAuditRecords] = useState<AuditRecord[]>([]);
  const [auditLoading, setAuditLoading] = useState(false);
  const [auditError, setAuditError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    getHealth().then(() => setApiOnline(true)).catch(() => setApiOnline(false));
    void loadAudit();
    getDemoRequests().then(setDemos).catch(reason => setError(reason instanceof Error ? reason.message : "演示数据加载失败"));
  }, []);

  const loadAudit = async () => {
    setAuditLoading(true); setAuditError(null);
    try { setAuditRecords(await getAuditRecords()); }
    catch (reason) { setAuditError(reason instanceof Error ? reason.message : "审计加载失败"); }
    finally { setAuditLoading(false); }
  };

  const refresh = async (nextTask: TaskResponse) => {
    setTask(nextTask);
    setEvents([]);
    void loadAudit();
    setRefreshKey(value => value + 1);
  };

  const submit = async () => {
    if (selectedDemo === null) return;
    setLoading(true); setError(null); setTask(null); setEvents([]);
    try {
      await refresh(await createTask(demos[selectedDemo].payload));
      setApiOnline(true);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "请求失败");
      setApiOnline(false);
    } finally { setLoading(false); }
  };

  const reset = () => { setSelectedDemo(null); setTask(null); setEvents([]); setAuditRecords([]); setError(null); setAuditError(null); setLoading(false); setAuditLoading(false); setRefreshKey(value => value + 1); };
  const select = (index: number) => { setSelectedDemo(index); setTask(null); setEvents([]); setError(null); };

  const draft = selectedDemo === null ? null : demos[selectedDemo]?.payload ?? null;
  return <div className="app-shell"><Header apiOnline={apiOnline} onReset={reset} /><div className="workspace"><aside><DemoScenarioList demos={demos} selected={selectedDemo} submitted={task !== null} loading={loading} onSelect={select} onSubmit={submit} /></aside><main><StatusBanner task={task} />{error && <div className="error-card">{error}</div>}<RequestDetailCard task={task} draft={draft} /><RiskAssessmentCard risk={task?.risk} /><EventTimeline taskId={task?.task_id} refreshKey={refreshKey} onEventsChange={setEvents} /></main><aside className="right-column"><ApprovalPanel task={task} onResolved={refresh} /><AuditPanel records={auditRecords} loading={auditLoading} error={auditError} /></aside></div></div>;
}
