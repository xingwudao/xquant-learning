# Spec: macOS 环境配置

> 所有命令在沙箱外（真实终端）运行。如果 TRAE 提示选择运行环境，请选择「在终端中运行」或「沙箱外运行」。

## 上下文

学员刚在 TRAE 中打开了一个空目录作为课程学习根目录。本机是 macOS，尚未安装 Python 或任何依赖。这是课程的第一份 spec——后续 35 份 spec 都依赖这一份装出的环境。

## 任务

在当前目录下完成 macOS 量化课程编程环境配置：装 uv → 用 uv 创建 Python 3.12 虚拟环境 → 装 7 个依赖包 → 创建并跑通 `check_env.py` 自检脚本。

## 要求

### 第 1 步：确认当前目录

在终端运行：

```bash
pwd
```

记录输出的路径——后续所有操作都在这个目录下进行。不要 cd 切换到别的目录。

### 第 2 步：安装 uv

为什么用 uv：一个工具搞定 Python 安装、虚拟环境、包管理三件事。0 编程基础学员不必分别学三种不同工具。

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
uv --version
```

最后一行应输出 uv 的版本号。如果提示 `uv: command not found`，说明 PATH 还没生效，重新运行 `source $HOME/.local/bin/env`。

### 第 3 步：创建 Python 3.12 虚拟环境

uv 会自动下载并使用 Python 3.12，不需要先单独装 Python。

```bash
uv venv --python 3.12
source .venv/bin/activate
python --version
```

最后一行应显示 `Python 3.12.x`。

### 第 4 步：安装依赖包

为什么用清华镜像：默认 PyPI 源在国内延迟高，清华镜像几秒钟搞定。
为什么锁版本号到 minor：半年后某个依赖升级可能让课程 notebook 跑不通，锁到 `==X.Y.*` 既允许 patch 升级又不会跨 minor。

```bash
uv pip install --index-url https://pypi.tuna.tsinghua.edu.cn/simple \
  jupyter==1.1.* pandas==3.0.* numpy==2.4.* matplotlib==3.10.* \
  akshare==1.18.* yfinance==1.2.*

uv pip install "open-xquant @ git+https://github.com/xingwudao/open-xquant.git@v0.1.0"
```

`open-xquant` 是课程配套的量化交易框架，从 GitHub 安装并锁到 `v0.1.0` 版本。

### 第 5 步：创建 check_env.py

为什么需要 check 脚本：环境配置类任务没有图表可看、错误会延迟暴露，只能靠机械检查判断成功。这份脚本是后续所有 spec 的入口检查——它通过了，整门课就能跑通。

在当前目录下创建文件 `check_env.py`，内容如下：

```python
"""XQuant 课程环境检查脚本

使用方法：在激活虚拟环境后运行
    python check_env.py
"""

import sys
import shutil


REQUIRED_PYTHON = (3, 12)

PACKAGES = [
    ("jupyter", "jupyter", "uv pip install jupyter==1.1.*"),
    ("pandas", "pandas", "uv pip install pandas==3.0.*"),
    ("numpy", "numpy", "uv pip install numpy==2.4.*"),
    ("matplotlib", "matplotlib", "uv pip install matplotlib==3.10.*"),
    ("akshare", "akshare", "uv pip install akshare==1.18.*"),
    ("yfinance", "yfinance", "uv pip install yfinance==1.2.*"),
    ("oxq", "open-xquant",
     'uv pip install "open-xquant @ git+https://github.com/xingwudao/open-xquant.git@v0.1.0"'),
]

ACTIVATE_HINT = (
    ".venv\\Scripts\\activate" if sys.platform == "win32"
    else "source .venv/bin/activate"
)


def check_python():
    v = sys.version_info
    ok = (v.major, v.minor) >= REQUIRED_PYTHON
    msg = f"Python {v.major}.{v.minor}.{v.micro}"
    if not ok:
        msg += f"（需要 >= {REQUIRED_PYTHON[0]}.{REQUIRED_PYTHON[1]}）"
    return ok, msg


def check_venv():
    in_venv = sys.prefix != sys.base_prefix
    if in_venv:
        return True, "虚拟环境已激活"
    return False, f"虚拟环境未激活；运行 {ACTIVATE_HINT}"


def check_pkg(import_name, display, install_cmd):
    try:
        __import__(import_name)
        return True, display
    except ImportError:
        return False, f"{display} 未安装；运行: {install_cmd}"


def check_jupyter_cmd():
    if shutil.which("jupyter"):
        return True, "jupyter 命令可用"
    return False, "jupyter 命令不可用；运行: uv pip install jupyter==1.1.*"


def check_akshare_data():
    try:
        import akshare as ak
        df = ak.fund_etf_hist_em(symbol="510300", period="daily", adjust="qfq")
        if len(df) > 0:
            return True, f"akshare 数据源连通（获取到 {len(df)} 条数据）"
        return False, "akshare 返回空数据，可能接口变动"
    except ImportError:
        return False, "akshare 未安装；跳过数据源测试"
    except Exception as e:
        return False, f"akshare 数据获取失败: {e}"


def main():
    print()
    print("=" * 50)
    print("  XQuant 课程环境检查")
    print("=" * 50)
    print()

    results = [check_python(), check_venv()]
    for name, display, install in PACKAGES:
        results.append(check_pkg(name, display, install))
    results.append(check_jupyter_cmd())
    results.append(check_akshare_data())

    passed = sum(1 for ok, _ in results if ok)
    total = len(results)

    for ok, msg in results:
        print(f"  [{'OK  ' if ok else 'FAIL'}] {msg}")

    print()
    print("-" * 50)
    if passed == total:
        print(f"  结果: {total}/{total} 全部通过！")
        print("  环境配置完成，可以开始课程。")
    else:
        print(f"  结果: {passed}/{total} 通过，{total - passed} 项需修复")
        print("  把上面输出复制给 AI 助手，让它帮你排查。")
    print()
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
```

### 第 6 步：运行 check_env.py

```bash
python check_env.py
```

## 结果呈现

1. `python check_env.py` 最末两行输出：
   ```
   结果: 11/11 全部通过！
   环境配置完成，可以开始课程。
   ```
2. 命令退出码为 0
3. 当前目录下存在 `.venv/` 目录与 `check_env.py` 文件

如果有任何检查项显示 `[FAIL]`，把 `check_env.py` 的完整输出复制给 AI 助手排查。

## 故障恢复

| 现象 | 处理 |
|---|---|
| `uv: command not found` | 运行 `source $HOME/.local/bin/env` 让 PATH 生效 |
| pip install 慢 / 超时 | 已用清华镜像；仍超时把报错完整复制给 AI |
| 任何其他报错 | 把终端完整输出（含命令 + 报错）复制给 AI 助手排查，**不要自己改命令重试** |
| 每次打开新终端 | 先运行 `source .venv/bin/activate` 激活虚拟环境 |
