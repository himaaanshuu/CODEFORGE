import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const mode = process.argv[2] ?? "all";
if (!["all", "frontend", "backend"].includes(mode)) {
  console.error("Usage: node scripts/dev.mjs [all|frontend|backend]");
  process.exit(2);
}

const children = [];
if (mode !== "backend") {
  children.push({
    name: "Frontend",
    process: spawn("npm", ["run", "dev"], {
      cwd: path.join(root, "frontend"),
      stdio: "inherit",
      shell: process.platform === "win32",
    }),
  });
}

const windowsPython = path.join(root, "backend", "venv", "Scripts", "python.exe");
const unixPython = path.join(root, "backend", "venv", "bin", "python");
const python = existsSync(windowsPython)
  ? windowsPython
  : existsSync(unixPython)
    ? unixPython
    : process.platform === "win32" ? "python" : "python3";

if (mode !== "frontend") {
  children.push({
    name: "Backend",
    process: spawn(
      python,
      ["-m", "uvicorn", "backend.app.main:app", "--reload", "--port", "8000"],
      { cwd: root, stdio: "inherit" },
    ),
  });
}

let stopping = false;
function stopAll(exitCode = 0) {
  if (stopping) return;
  stopping = true;
  for (const { process: child } of children) child.kill();
  process.exitCode = exitCode;
}

for (const { name, process: child } of children) {
  child.on("error", (error) => {
    console.error(`Unable to start ${name.toLowerCase()}:`, error.message);
    stopAll(1);
  });
  child.on("exit", (code, signal) => {
    if (!stopping) {
      console.log(`${name} stopped (${signal ?? code}).`);
      stopAll(code ?? 1);
    }
  });
}

process.on("SIGINT", () => stopAll());
process.on("SIGTERM", () => stopAll());

console.log(mode === "all" ? "Starting CodeForge frontend and backend..." : `Starting CodeForge ${mode}...`);
if (mode !== "backend") console.log("Frontend: http://localhost:5173");
if (mode !== "frontend") console.log("Backend: http://localhost:8000");
