> 所有命令在沙箱外运行。

请帮我配置量化交易课程的 Python 编程环境。请严格按照以下步骤操作：

重要：本任务涉及安装系统工具和 Python 包，所有终端命令都需要在沙箱外（真实终端）运行。如果 TRAE 提示选择运行环境，请选择「在终端中运行」或「沙箱外运行」。

## 第零步：确认当前工作目录

我已经在 TRAE 中打开了一个文件夹作为课程学习目录。请先在终端运行 pwd 获取当前目录路径，后续所有操作都在这个目录下进行。

## 第一步：安装 uv

uv 是一个 Python 包管理工具，用它来管理 Python 版本和依赖包。

在终端运行：
curl -LsSf https://astral.sh/uv/install.sh | sh

安装完成后，运行以下命令让 uv 生效：
source $HOME/.local/bin/env

然后验证安装成功：
uv --version

## 第二步：在当前目录创建虚拟环境

在当前目录下用 uv 创建虚拟环境（会自动下载 Python 3.12）：

uv venv --python 3.12

然后激活虚拟环境：
source .venv/bin/activate

验证 Python 版本：
python --version

应该显示 Python 3.12.x。

## 第三步：安装依赖包

使用清华镜像源安装以下 6 个包（国内速度更快）：

uv pip install --index-url https://pypi.tuna.tsinghua.edu.cn/simple jupyter pandas numpy matplotlib akshare yfinance

然后安装课程配套的量化交易框架 open-xquant（从 GitHub 安装，尚未发布到 PyPI）：

uv pip install "open-xquant @ git+https://github.com/xingwudao/open-xquant.git"

## 第四步：创建并运行环境检查脚本

请在当前目录下创建文件 check_env.py，内容如下：

"""
XQuant 课程环境检查脚本

使用方法：在激活虚拟环境后运行
    python check_env.py

本脚本检查量化交易课程所需的编程环境是否配置正确。
"""

import sys
import shutil


REQUIRED_PYTHON = (3, 12)

REQUIRED_PACKAGES = [
    ("jupyter", "jupyter"),
    ("pandas", "pandas"),
    ("numpy", "numpy"),
    ("matplotlib", "matplotlib"),
    ("akshare", "akshare"),
    ("yfinance", "yfinance"),
    ("oxq", "open-xquant"),
]

AKSHARE_TEST_FUNC = "fund_etf_hist_em"
AKSHARE_TEST_KWARGS = {"symbol": "510300", "period": "daily", "adjust": "qfq"}

OPEN_XQUANT_INSTALL = 'uv pip install "open-xquant @ git+https://github.com/xingwudao/open-xquant.git"'


def check_python_version():
    v = sys.version_info
    version_str = f"{v.major}.{v.minor}.{v.micro}"
    if (v.major, v.minor) >= REQUIRED_PYTHON:
        return True, f"Python {version_str}"
    return False, f"Python {version_str}（需要 >= {REQUIRED_PYTHON[0]}.{REQUIRED_PYTHON[1]}）"


def check_venv():
    in_venv = sys.prefix != sys.base_prefix
    if in_venv:
        return True, "虚拟环境已激活"
    return False, "未检测到虚拟环境，请先运行 source .venv/bin/activate"


def check_package(import_name, display_name):
    try:
        __import__(import_name)
        return True, display_name
    except ImportError:
        if display_name == "open-xquant":
            return False, f"{display_name} — 未安装，请运行: {OPEN_XQUANT_INSTALL}"
        return False, f"{display_name} — 未安装，请运行: uv pip install {display_name}"


def check_jupyter_command():
    if shutil.which("jupyter"):
        return True, "jupyter 命令可用"
    return False, "jupyter 命令不可用，请运行: uv pip install jupyter"


def check_data_source():
    try:
        import akshare as ak
        func = getattr(ak, AKSHARE_TEST_FUNC)
        df = func(**AKSHARE_TEST_KWARGS)
        if len(df) > 0:
            return True, f"akshare 数据源正常（获取到 {len(df)} 条数据）"
        return False, "akshare 返回了空数据，可能是接口变动"
    except ImportError:
        return False, "akshare 未安装，跳过数据源测试"
    except Exception as e:
        return False, f"akshare 数据获取失败: {e}"


def main():
    print()
    print("=" * 50)
    print("  XQuant 课程环境检查")
    print("=" * 50)
    print()

    results = []

    ok, msg = check_python_version()
    results.append((ok, msg))

    ok, msg = check_venv()
    results.append((ok, msg))

    for import_name, display_name in REQUIRED_PACKAGES:
        ok, msg = check_package(import_name, display_name)
        results.append((ok, msg))

    ok, msg = check_jupyter_command()
    results.append((ok, msg))

    ok, msg = check_data_source()
    results.append((ok, msg))

    passed = 0
    failed = 0
    for ok, msg in results:
        if ok:
            print(f"  [OK]   {msg}")
            passed += 1
        else:
            print(f"  [FAIL] {msg}")
            failed += 1

    print()
    print("-" * 50)

    if failed == 0:
        print(f"  结果: {passed}/{passed} 全部通过!")
        print()
        print("  环境配置完成，可以开始课程了。")
    else:
        print(f"  结果: {passed}/{passed + failed} 通过，{failed} 项需要修复")
        print()
        print("  请把上面的输出结果发给 AI 助手，让它帮你修复失败项。")

    print()
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

文件创建完成后，运行：
python check_env.py

如果所有检查项都显示 [OK]，环境配置就完成了。如果有失败项，请把输出结果发给我，我帮你排查。

## 注意事项
- 如果终端提示 uv: command not found，请先运行 source $HOME/.local/bin/env
- 如果 pip install 很慢或超时，已经指定了清华镜像源，应该不会有问题
- 每次打开新的终端窗口，都需要先激活虚拟环境：source .venv/bin/activate
