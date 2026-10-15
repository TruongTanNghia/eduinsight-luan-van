// Kiểm thử nhanh: khởi động server qua stdio và gọi các tool.
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import { fileURLToPath } from "node:url";

const client = new Client({ name: "test", version: "1.0.0" });
await client.connect(new StdioClientTransport({ command: process.execPath, args: [fileURLToPath(new URL("./server.mjs", import.meta.url))] }));
const tools = await client.listTools();
console.log("TOOLS:", tools.tools.map((t) => t.name).join(", "));
const prompts = await client.listPrompts();
console.log("PROMPTS:", prompts.prompts.map((p) => p.name).join(", "));
const res = await client.listResources();
console.log("RESOURCES:", res.resources.length);
const call = async (name, args = {}) => (await client.callTool({ name, arguments: args })).content[0].text;
console.log("rules chars:", (await call("get_design_rules")).length);
console.log("tokens css starts:", (await call("get_design_tokens", { format: "css" })).slice(0, 40).replace(/\n/g, " "));
console.log((await call("list_screens")).split("\n").length, "screens");
console.log("component all chars:", (await call("get_component", { name: "all" })).length);
console.log("screen+ref chars:", (await call("get_screen", { screen: "student-profile", include_reference: true })).length);
const bad = `export default function P(){ const v=7.123; return (<aside className="w-64 bg-indigo-600 text-white"><div className="rounded-xl border shadow-lg bg-gradient-to-r from-purple-500 to-pink-500 p-4" onClick={()=>{}}>🎓 {v.toFixed(2)}</div><span className="bg-mint text-white">x</span><img src="a.png"/></aside>) }`;
const good = `import { Sticker } from "@/components/ui/sticker"; import { DemoBadge } from "@/components/ui/tag";
export default function P(){ return (<Sticker tone="yellow"><h1 className="text-[54px] font-extrabold">Tổng quan</h1><DemoBadge /><span className="num">{(7.12).toFixed(2).replace(".", ",")}</span></Sticker>) }`;
const b = JSON.parse(await call("audit_ui", { code: bad, filename: "bad.tsx" }));
console.log("BAD:", b.score, b.verdict, b.findings.map((f) => f.rule).join(","));
const g = JSON.parse(await call("audit_ui", { code: good, filename: "good.tsx" }));
console.log("GOOD:", g.score, g.verdict, g.findings.map((f) => f.rule).join(","));
const p = await client.getPrompt({ name: "build_screen", arguments: { screen: "dashboard" } });
console.log("prompt chars:", p.messages[0].content.text.length);
await client.close();
