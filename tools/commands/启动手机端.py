"""手机端模式启动器 — Android 热更新部署 + APK 构建。

--phone:     单独启动 apps/phone 的 Android 手机端热更新
--apk:       构建 apps/phone 的 Android 安装包
--help:      查看所有命令
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from shared.android_utils import (
    是否安卓模拟器,
    解析手机端访问主机,
    合并_android_签名配置,
    解析_gradlew_命令,
    确保_android_java_配置,
    确保_android_sdk_配置,
    选择安卓目标,
)
from shared.config import (
    APK_ARCH_CONFIG,
    APK_FULL_BUILD_ORDER,
    PHONE_DEV_PORT,
    PHONE_DIR,
    PHONE_LOG,
    ROOT_DIR,
)
from shared.dependency_manager import (
    确保手机端依赖,
    确保手机端_web资源,
    解析_npm_命令,
    解析_cap_命令,
)
from shared.env_utils import 确保手机端_env_文件
from shared.process_manager import (
    停止进程,
    提取进程_pid,
    更新状态,
    启动并转发日志,
    等待_http_服务,
    检查_http_服务,
    等待二次确认中断,
    打开文件资源管理器,
    _停止单个开发进程,
)
from shared.terminal import echo

SCRIPT_NAME = Path(__file__).name


# ---------------------------------------------------------------------------
# 进程停止
# ---------------------------------------------------------------------------

def 清理手机端状态() -> None:
    更新状态(processes={"phone_frontend": 0})
    更新状态(mobile=None)


def 停止手机端开发进程(*, state: dict | None = None, 显示未找到提示: bool = True) -> None:
    _停止单个开发进程(
        state=state,
        显示未找到提示=显示未找到提示,
        进程键="phone_frontend",
        进程显示名="手机端",
        未启动提示="手机端: 未启动",
        清理函数=清理手机端状态,
        提取_pid函数=lambda s: 提取进程_pid(s, "phone_frontend")[0],
    )


# ---------------------------------------------------------------------------
# 开发服务
# ---------------------------------------------------------------------------

def 确保手机端开发服务已启动(phone_port: int) -> int:
    service_url = f"http://127.0.0.1:{phone_port}"
    if 检查_http_服务(service_url):
        return 0

    npm_cmd = 解析_npm_命令()
    echo(f"未检测到手机端开发服务，正在启动 apps/phone（端口 {phone_port}）")
    phone_cmd = [*npm_cmd, "run", "dev", "--", "--host", "0.0.0.0", "--port", str(phone_port), "--strictPort"]
    phone_proc = 启动并转发日志(phone_cmd, PHONE_DIR, PHONE_LOG, force_color=True)

    try:
        等待_http_服务(service_url, timeout=60)
    except Exception as exc:
        停止进程(phone_proc.pid)
        raise RuntimeError(f"手机端开发服务启动失败，请检查日志: {PHONE_LOG}") from exc

    更新状态(processes={"phone_frontend": phone_proc.pid})
    echo(f"手机端开发服务已启动: {service_url}")
    return phone_proc.pid


# ---------------------------------------------------------------------------
# Android 热更新
# ---------------------------------------------------------------------------

def 启动安卓手机端(
    *, app_dir: Path, phone_target: Optional[str], phone_host: Optional[str], phone_port: int
) -> dict:
    android_dir = app_dir / "android"
    if not android_dir.exists():
        raise RuntimeError("未找到 Android 原生工程，请先确认 Capacitor Android 已初始化")

    等待_http_服务(f"http://127.0.0.1:{phone_port}", timeout=60)

    cap_cmd = 解析_cap_命令(app_dir)
    env = os.environ.copy()
    sdk_dir = 确保_android_sdk_配置(env, android_dir)
    java_home = 确保_android_java_配置(env)

    target = 选择安卓目标(app_dir, phone_target, env=env)
    is_emulator = 是否安卓模拟器(str(target.get("id", "")))
    requested_host = 解析手机端访问主机(target=target, phone_host=phone_host)
    live_reload_host = requested_host
    forward_ports_args: list[str] = []

    if not is_emulator and not phone_host:
        live_reload_host = "localhost"
        forward_ports_args = ["--forwardPorts", f"{phone_port}:{phone_port}"]

    server_url = f"http://{live_reload_host}:{phone_port}"

    echo(
        "正在启动 Android 手机端"
        f"（目标: {target.get('name', '未知目标')} / {target.get('id', '未知 ID')}，"
        f"开发服务器: {server_url}，SDK: {sdk_dir}，JAVA: {java_home}）"
    )
    if forward_ports_args:
        echo(f"已为真机启用 adb reverse 端口转发: {phone_port}:{phone_port}")

    mobile_info = {
        "target_id": str(target.get("id", "")),
        "target_name": str(target.get("name", "未知目标")),
        "server_url": server_url,
    }

    subprocess.run(
        [
            *cap_cmd, "run", "android",
            "--target", str(target.get("id", "")),
            "--live-reload",
            "--host", live_reload_host,
            "--port", str(phone_port),
            *forward_ports_args,
        ],
        check=True,
        cwd=app_dir,
        env=env,
    )

    更新状态(mobile=mobile_info)
    echo(f"Android 手机端已接入前端热更新: {server_url}")
    return mobile_info


def 单独启动手机端(*, phone_target: Optional[str], phone_host: Optional[str], phone_port: int) -> None:
    os.chdir(ROOT_DIR)
    确保手机端依赖()
    确保手机端_web资源()
    确保手机端开发服务已启动(phone_port)
    try:
        启动安卓手机端(
            app_dir=PHONE_DIR,
            phone_target=phone_target,
            phone_host=phone_host,
            phone_port=phone_port,
        )
    except KeyboardInterrupt:
        等待二次确认中断(
            首次提示="收到中断信号，再按一次 Ctrl+C 才会停止手机端开发环境",
            执行提示="检测到 Ctrl+C，正在停止手机端开发环境",
            停止函数=停止手机端开发进程,
        )
        return
    except Exception:
        停止手机端开发进程()
        raise


# ---------------------------------------------------------------------------
# APK 构建
# ---------------------------------------------------------------------------

def 获取_android_apk_输出目录(build_variant: str) -> Path:
    return PHONE_DIR / "android" / "app" / "build" / "outputs" / "apk" / build_variant


def 查找最新_android_apk(build_variant: str) -> Path:
    output_dir = 获取_android_apk_输出目录(build_variant)
    candidates = [path for path in output_dir.glob("*.apk") if path.is_file()]
    if not candidates:
        raise RuntimeError(f"未找到 {build_variant} 构建产物，请检查 Gradle 输出目录: {output_dir}")
    candidates.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    return candidates[0]


def 获取_android_apk_归档目录(build_variant: str) -> Path:
    return PHONE_DIR / ".cache" / "apk" / build_variant / "architectures"


def 选择_apk_架构配置(args: argparse.Namespace) -> list[str]:
    if args.all:
        return APK_FULL_BUILD_ORDER.copy()

    selected: list[str] = []
    for attr_name, profile_key in (
        ("x86_all", "x86-all"),
        ("arm64_all", "arm64-all"),
        ("x86", "x86"),
        ("x86_64", "x86_64"),
        ("arm_v8a", "arm-v8a"),
        ("arm_v7a", "arm-v7a"),
    ):
        if getattr(args, attr_name, False):
            selected.append(profile_key)
    return selected or ["all"]


def 复制_android_apk_到归档目录(*, build_variant: str, profile_key: str, source_apk: Path) -> Path:
    profile = APK_ARCH_CONFIG[profile_key]
    archive_dir = 获取_android_apk_归档目录(build_variant)
    archive_dir.mkdir(parents=True, exist_ok=True)
    target_apk = archive_dir / f"{source_apk.stem}-{profile['suffix']}{source_apk.suffix}"
    shutil.copy2(source_apk, target_apk)
    return target_apk


def 构建安卓安装包(*, build_variant: str, profile_keys: list[str]) -> list[Path]:
    if build_variant not in {"debug", "release"}:
        raise RuntimeError(f"不支持的 Android 构建类型: {build_variant}")

    android_dir = PHONE_DIR / "android"
    if not android_dir.exists():
        raise RuntimeError("未找到 apps/phone/android 原生工程，请先在 apps/phone 初始化 Capacitor Android")

    确保手机端_env_文件()
    确保手机端依赖()

    npm_cmd = 解析_npm_命令()
    cap_cmd = 解析_cap_命令(PHONE_DIR)
    gradlew_cmd = 解析_gradlew_命令(android_dir)
    env = os.environ.copy()
    sdk_dir = 确保_android_sdk_配置(env, android_dir)
    java_home = 确保_android_java_配置(env)
    env["VITE_ENABLE_DEVELOPER_LOGIN"] = "true" if build_variant == "debug" else "false"
    env["VITE_ENABLE_API_ENV_SWITCH"] = "true" if build_variant == "debug" else "false"
    has_release_signing = 合并_android_签名配置(env) if build_variant == "release" else False

    variant_label = "Debug" if build_variant == "debug" else "Release"
    gradle_task = f"assemble{variant_label}"

    echo(f"正在构建手机端静态资源（Android {variant_label}）")
    subprocess.run([*npm_cmd, "run", "build"], check=True, cwd=PHONE_DIR, env=env)

    if build_variant == "release":
        sign_text = "已签名" if has_release_signing else "未签名"
        echo(f"正在同步 Android 原生工程（SDK: {sdk_dir}，JAVA: {java_home}，Release: {sign_text}）")
    else:
        echo(f"正在同步 Android 原生工程（SDK: {sdk_dir}，JAVA: {java_home}）")
    subprocess.run([*cap_cmd, "sync", "android"], check=True, cwd=PHONE_DIR, env=env)

    outputs: list[Path] = []
    total = len(profile_keys)
    for index, profile_key in enumerate(profile_keys, start=1):
        profile = APK_ARCH_CONFIG[profile_key]
        architectures = ",".join(profile["architectures"])
        current_env = env.copy()
        current_env["ANDROID_TARGET_ARCHITECTURES"] = architectures
        echo(
            f"正在执行 Android 安装包构建 [{index}/{total}]: "
            f"{gradle_task}（{profile['label']}，架构: {architectures}）"
        )
        subprocess.run(
            [*gradlew_cmd, gradle_task, f"-PandroidTargetArchitectures={architectures}"],
            check=True,
            cwd=android_dir,
            env=current_env,
        )

        source_apk = 查找最新_android_apk(build_variant)
        archived_apk = 复制_android_apk_到归档目录(
            build_variant=build_variant,
            profile_key=profile_key,
            source_apk=source_apk,
        )
        size_mb = round(archived_apk.stat().st_size / 1024 / 1024, 2)
        echo(f"Android 安装包构建成功: {archived_apk} [{size_mb} MB]")
        outputs.append(archived_apk)

    if len(outputs) == 1:
        打开文件资源管理器(outputs[0])
    else:
        打开文件资源管理器(outputs[0].parent)
    return outputs


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def 打印帮助() -> None:
    script_path = f"./tools/commands/{SCRIPT_NAME}"
    print("用法:")
    print(f"  python {script_path} --phone [--target TARGET] [--host HOST] [--port PORT]")
    print(f"  python {script_path} --apk [--debug|--release] [--all|--x86-all|--arm64-all|--x86|--x86_64|--arm-v8a|--arm-v7a]")
    print(f"  python {script_path} --help")
    print("")
    print("模式说明:")
    print("  --phone: 手机端热更新部署，管理 apps/phone 的 Android 调试接入")
    print("  --apk:   构建 apps/phone 的 Android 安装包")
    print("")
    print("手机端参数:")
    print("  --target:  指定 Android 目标 ID，仅 `--phone` 可用")
    print("  --host:    指定手机端访问开发服务器的主机地址，仅 `--phone` 可用")
    print(f"  --port:    指定 apps/phone 开发服务器端口，仅 `--phone` 可用，默认 {PHONE_DEV_PORT}")
    print("")
    print("安装包参数:")
    print("  --debug:    构建 Debug APK，仅 `--apk` 可用")
    print("  --release:  构建 Release APK，仅 `--apk` 可用，默认值")
    print("  --all:      构建全部 7 个架构包")
    print("  --x86-all:  构建 x86+x86_64 双架构 APK")
    print("  --arm64-all: 构建 arm64-v8a+armeabi-v7a 双架构 APK")
    print("  --x86:      仅构建 x86 APK")
    print("  --x86_64:   仅构建 x86_64 APK")
    print("  --arm-v8a:  仅构建 arm64-v8a APK")
    print("  --arm-v7a:  仅构建 armeabi-v7a APK")
    print("")
    print("示例:")
    print(f"  python {script_path} --phone")
    print(f"  python {script_path} --phone --target emulator-5554")
    print(f"  python {script_path} --apk --debug")
    print(f"  python {script_path} --apk --release --arm-v8a")


def 解析参数() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="手机端模式启动器", add_help=False)
    client_group = parser.add_mutually_exclusive_group()
    client_group.add_argument("--phone", action="store_true", help="启动 Android 手机端热更新")
    client_group.add_argument("--apk", action="store_true", help="构建 Android APK 安装包")
    parser.add_argument("action", nargs="?", help=argparse.SUPPRESS)
    parser.add_argument("--target", help="指定 Android 目标 ID（仅 --phone 使用）")
    parser.add_argument("--host", help="指定手机端访问前端开发服务器的主机地址（仅 --phone 使用）")
    parser.add_argument("--port", type=int, default=PHONE_DEV_PORT, help="开发服务器端口（默认 5174）")
    variant_group = parser.add_mutually_exclusive_group()
    variant_group.add_argument("--debug", action="store_true", help="构建 Debug APK")
    variant_group.add_argument("--release", action="store_true", help="构建 Release APK（默认）")
    parser.add_argument("--all", action="store_true", help="构建全部 7 个架构包")
    parser.add_argument("--x86-all", dest="x86_all", action="store_true", help="x86+x86_64")
    parser.add_argument("--arm64-all", dest="arm64_all", action="store_true", help="arm64-v8a+armeabi-v7a")
    parser.add_argument("--x86", action="store_true", help="仅构建 x86 APK")
    parser.add_argument("--x86_64", action="store_true", help="仅构建 x86_64 APK")
    parser.add_argument("--arm-v8a", dest="arm_v8a", action="store_true", help="仅构建 arm64-v8a APK")
    parser.add_argument("--arm-v7a", dest="arm_v7a", action="store_true", help="仅构建 armeabi-v7a APK")
    parser.add_argument("-h", "--help", action="store_true", help="显示帮助信息")
    return parser.parse_args()


def main() -> int:
    args = 解析参数()

    if args.help:
        打印帮助()
        return 0

    try:
        if not args.phone and not args.apk:
            args.phone = True

        if (args.target or args.host or args.port != PHONE_DEV_PORT) and not args.phone:
            raise RuntimeError("--target、--host、--port 仅可与 --phone 一起使用")

        if (args.debug or args.release) and not args.apk:
            raise RuntimeError("--debug、--release 仅可与 --apk 一起使用")

        if (
            args.all or args.x86_all or args.arm64_all
            or args.x86 or args.x86_64 or args.arm_v8a or args.arm_v7a
        ) and not args.apk:
            raise RuntimeError("架构构建参数仅可与 --apk 一起使用")

        if args.phone:
            单独启动手机端(
                phone_target=args.target,
                phone_host=args.host,
                phone_port=args.port,
            )
        elif args.apk:
            build_variant = "debug" if args.debug else "release"
            profile_keys = 选择_apk_架构配置(args)
            构建安卓安装包(build_variant=build_variant, profile_keys=profile_keys)

        return 0
    except subprocess.CalledProcessError as exc:
        print(f"命令执行失败，返回代码为: {exc.returncode}: {exc.cmd}", file=sys.stderr)
        return exc.returncode
    except KeyboardInterrupt:
        print("")
        echo("操作已取消")
        return 130
    except Exception as exc:
        print(f"错误: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
