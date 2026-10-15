// Chạy audit_ui cho một hoặc nhiều file (Windows-safe): node audit.mjs <file...>
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
const client = new Client({ name: "audit", version: "1.0.0" });
await client.connect(new StdioClientTransport({ command: process.execPath, args: [fileURLToPath(new URL("./server.mjs", import.meta.url))] }));
let worst = 0;
for (const f of process.argv.slice(2)) {
  const r = JSON.parse((await client.callTool({ name: "audit_ui", arguments: { code: readFileSync(f, "utf8"), filename: f } })).content[0].text);
  console.log(`${r.score.toString().padStart(3)}  ${r.verdict.split(" — ")[0].padEnd(22)}  ${f}`);
  for (const x of r.findings) if (x.level !== "info") console.log(`     [${x.level}] ${x.rule}: ${x.message} → ${x.fix}${x.sample ? "\n        " + x.sample.join("\n        ") : ""}`);
  worst = Math.max(worst, r.errors);
}
await client.close();
process.exit(worst ? 1 : 0);
