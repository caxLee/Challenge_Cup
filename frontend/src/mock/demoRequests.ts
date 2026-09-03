import type { TaskRequest } from "../types/security";

export interface DemoRequest {
  title: string;
  description: string;
  expectedLevel: "L0" | "L1" | "L2" | "L3" | "L4";
  payload: TaskRequest;
}

const user = { user_id: "user-1", user_role: "staff" };

export const demoRequests: DemoRequest[] = [
  {
    title: "公开知识查询",
    description: "读取公开知识库内容",
    expectedLevel: "L0",
    payload: { ...user, goal: "查询公开知识", tool: "knowledge.search", arguments: { query: "public" } },
  },
  {
    title: "内部知识查询",
    description: "只读访问内部知识库",
    expectedLevel: "L1",
    payload: { ...user, goal: "查询内部知识", tool: "knowledge.internal_search", arguments: { query: "internal" } },
  },
  {
    title: "修改业务记录",
    description: "修改一条业务记录并等待本人确认",
    expectedLevel: "L2",
    payload: { ...user, goal: "修改业务记录", tool: "records.update", arguments: { record_id: "42", value: "updated" } },
  },
  {
    title: "生产环境执行命令",
    description: "在生产环境执行命令并等待独立审批",
    expectedLevel: "L3",
    payload: { ...user, goal: "执行生产命令", tool: "shell.execute", arguments: { command: "echo demo" } },
  },
  {
    title: "导出敏感数据",
    description: "向外部目标导出敏感数据",
    expectedLevel: "L4",
    payload: { ...user, goal: "导出敏感数据", tool: "database.export", arguments: { destination: "outside.example" }, destination: { trust: "external" } },
  },
];
