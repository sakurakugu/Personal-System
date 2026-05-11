import { existsSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const 当前目录 = dirname(fileURLToPath(import.meta.url));
const 根目录 = resolve(当前目录, "..");
const hooks目录 = resolve(根目录, ".githooks");

if (!existsSync(hooks目录)) {
  process.exit(0);
}

const git检测结果 = spawnSync("git", ["--version"], {
  cwd: 根目录,
  stdio: "ignore",
});

if (git检测结果.error || git检测结果.status !== 0) {
  process.exit(0);
}

const 当前配置结果 = spawnSync("git", ["config", "core.hooksPath"], {
  cwd: 根目录,
  encoding: "utf8",
});

if (当前配置结果.status === 0 && 当前配置结果.stdout.trim() === ".githooks") {
  process.exit(0);
}

const 设置结果 = spawnSync("git", ["config", "core.hooksPath", ".githooks"], {
  cwd: 根目录,
  stdio: "inherit",
});

if (设置结果.error) {
  process.exit(0);
}

process.exit(设置结果.status ?? 0);
