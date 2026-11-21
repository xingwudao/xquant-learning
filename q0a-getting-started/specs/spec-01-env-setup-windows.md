# spec：Windows 环境配置

> 在当前项目中执行命令，使用本 spec 指定的环境。遵守 TRAE 当前的权限设置；需要额外权限时，先说明原因和访问范围，取得用户确认后再继续，不要求关闭沙箱或启用“完全访问”。

## 上下文

当前在 TRAE 中打开的是一个空目录。本机为 Windows 10 或 11，尚未安装本书所需的 Python 和依赖，当前目录中也没有 `requirements.lock.txt` 和 `check_env.py`。

## 任务目标

在当前目录下完成 Windows 量化编程环境配置，并通过自检脚本确认环境可用。

## 执行要求

### 第 0 步：用 PowerShell 而非 cmd

本 spec 所有命令在 **PowerShell** 中运行，不是 cmd。
打开方法：开始菜单搜索 `PowerShell`，点击“Windows PowerShell”或“PowerShell 7”。
如果不确定打开的是哪个，运行 `$PSVersionTable.PSVersion` 应输出版本号。

### 第 1 步：确认当前目录

在 PowerShell 运行：

```powershell
pwd
```

（PowerShell 的 `pwd` 等价于 mac 的 `pwd`，输出当前目录路径。）记录这个路径。后续命令都从这个目录执行，项目文件和 `.venv` 虚拟环境也在这里创建，不得自行切换工作目录。

### 第 2 步：安装 uv

为什么用 uv：一个工具搞定 Python 安装、虚拟环境、包管理 3 件事。0 编程基础学员不必分别学 3 种不同工具。

仅使用下面列出的 `astral.sh` 官方安装命令，不得替换下载地址或擅自增加管理员权限。

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**装完后关闭并重新打开 PowerShell**——Windows 上 PATH 在当前会话不会自动生效，必须重开窗口。然后验证：

```powershell
uv --version
```

应输出 uv 的版本号。如果提示 `uv 不是可识别的命令`，说明终端没重开，关闭再开一次。

如果安装命令执行失败，保留并输出完整错误信息，不得自行改用其他来源的安装脚本。

### 第 3 步：安装 Python 3.12.11

使用 uv 安装本书验证过的 Python 3.12.11，不修改或替换系统自带的 Python 环境：

```powershell
uv python install 3.12.11
```

### 第 4 步：创建 Python 3.12.11 虚拟环境

在当前目录中创建 `.venv` 虚拟环境：

```powershell
uv venv --python 3.12.11
.venv\Scripts\python.exe --version
```

最后一行应显示 `Python 3.12.11`。

### 第 5 步：创建依赖版本范围文件

为什么用清华镜像：默认 PyPI 源在国内访问可能较慢，清华大学开源软件镜像站通常对国内读者更友好。除从 GitHub 安装的 `open-xquant` 外，其余依赖默认从 `https://pypi.tuna.tsinghua.edu.cn/simple` 安装，不得自行切换到来源不明的镜像。
为什么固定主版本号和次版本号：半年后某个依赖升级可能让本书配套的 Notebook 跑不通。`==X.Y.*` 允许补丁版本更新，但不会跨主版本号或次版本号，因此不是精确版本锁定。安装完成后，还要通过检查脚本记录实际安装版本。

在当前目录下创建文件 `requirements.lock.txt`，内容如下：

```text
jupyter==1.1.*
pandas==3.0.*
numpy==2.4.*
matplotlib==3.10.*
akshare==1.18.*
yfinance==1.2.*
open-xquant @ git+https://github.com/xingwudao/open-xquant.git@11a9702d16c2051dd034281c6d6c48fc05597195
```

`open-xquant` 是本书使用的量化交易框架，从 GitHub 安装并锁定到经过全书实验验证的完整提交哈希 `11a9702d16c2051dd034281c6d6c48fc05597195`。

### 第 6 步：安装依赖包

先检查 Git 是否可用，以及能否访问指定仓库。检查失败时，输出具体原因并提出处理建议，经确认后再继续，不得更换指定提交或数据来源。

按照刚创建的 `requirements.lock.txt`，安装所列 7 个依赖包及其所需的依赖：

```powershell
uv pip install --python .venv\Scripts\python.exe --index-url https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.lock.txt
```

### 第 7 步：创建 check_env.py

为什么需要 check 脚本：环境配置类任务没有图表可看，错误可能延迟暴露，因此需要用检查脚本判断当前环境是否达到入门要求。脚本通过，说明本地 Python 环境、所需依赖和 AkShare 数据通路通过了入口检查。后续实验使用的其他数据通路和具体功能，仍需在相应实验中检查。

在当前目录下创建文件 `check_env.py`，内容如下：

```python
r"""XQuant 环境检查脚本

使用方法：直接使用虚拟环境中的解释器运行
    .venv\Scripts\python.exe check_env.py
"""

import sys
import shutil
import subprocess
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path


REQUIRED_PYTHON = (3, 12, 11)

PACKAGES = [
    ("jupyter", "jupyter", "uv pip install jupyter==1.1.*"),
    ("pandas", "pandas", "uv pip install pandas==3.0.*"),
    ("numpy", "numpy", "uv pip install numpy==2.4.*"),
    ("matplotlib", "matplotlib", "uv pip install matplotlib==3.10.*"),
    ("akshare", "akshare", "uv pip install akshare==1.18.*"),
    ("yfinance", "yfinance", "uv pip install yfinance==1.2.*"),
    ("oxq", "open-xquant",
     'uv pip install "open-xquant @ git+https://github.com/xingwudao/open-xquant.git@11a9702d16c2051dd034281c6d6c48fc05597195"'),
]

VENV_PYTHON_HINT = (
    r".venv\Scripts\python.exe check_env.py" if sys.platform == "win32"
    else ".venv/bin/python check_env.py"
)


def check_python():
    v = sys.version_info
    actual = (v.major, v.minor, v.micro)
    ok = actual == REQUIRED_PYTHON
    msg = f"Python {v.major}.{v.minor}.{v.micro}"
    if not ok:
        required = ".".join(map(str, REQUIRED_PYTHON))
        msg += f"（需要 {required}）"
    return ok, msg


def check_venv():
    in_venv = sys.prefix != sys.base_prefix
    project_venv = Path(__file__).resolve().parent / ".venv"
    try:
        is_project_venv = in_venv and Path(sys.prefix).samefile(project_venv)
    except OSError:
        is_project_venv = False
    if is_project_venv:
        return True, f"正在使用本项目的虚拟环境（解释器：{sys.executable}）"
    return False, (
        f"当前解释器不是本项目 .venv 中的 Python（解释器：{sys.executable}）。"
        f"请在项目目录中运行 {VENV_PYTHON_HINT}"
    )


def check_uv():
    uv_path = shutil.which("uv")
    if not uv_path:
        return False, "uv 命令不可用。请重新安装 uv 并确认 PATH 已生效"
    try:
        result = subprocess.run(
            [uv_path, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except Exception as e:
        return False, f"uv 版本读取失败: {e}"
    output = (result.stdout or result.stderr).strip()
    if result.returncode == 0 and output:
        return True, output
    return False, f"uv 命令执行失败: {output or '无输出'}"


def check_pkg(import_name, display, install_cmd):
    try:
        __import__(import_name)
        try:
            installed_version = version(display)
            return True, f"{display} {installed_version}"
        except PackageNotFoundError:
            return True, display
    except ImportError:
        return False, f"{display} 未安装。运行: {install_cmd}"


def check_jupyter_cmd():
    try:
        result = subprocess.run(
            [sys.executable, "-m", "jupyter", "--version"],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    except Exception as e:
        return False, f"当前 Python 环境中的 Jupyter 命令检查失败: {e}"
    output = (result.stdout or result.stderr).strip()
    if result.returncode == 0 and output:
        return True, "当前 Python 环境中的 Jupyter 命令可用"
    return False, (
        f"当前 Python 环境中的 Jupyter 命令不可用: {output or '无输出'}。"
        f'请运行: uv pip install --python "{sys.executable}" jupyter==1.1.*'
    )


def check_akshare_data():
    try:
        import akshare as ak
        df = ak.stock_zh_index_daily(symbol="sh000300")
        if len(df) > 0:
            return True, f"akshare 数据接口连通（获取到 {len(df)} 条数据）"
        return False, "akshare 返回空数据，可能接口变动"
    except ImportError:
        return False, "akshare 未安装。跳过数据接口测试"
    except Exception as e:
        return False, f"akshare 数据获取失败: {e}"


def main():
    print()
    print("=" * 50)
    print("  XQuant 环境检查")
    print("=" * 50)
    print()

    results = [check_python(), check_venv(), check_uv()]
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
        print("  环境配置完成，可以开始本书的实验。")
    else:
        print(f"  结果: {passed}/{total} 通过，{total - passed} 项需修复")
        print("  把上面输出复制给 AI 助手，让它帮你排查。")
    print()
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
```

### 第 8 步：运行 check_env.py

```powershell
.venv\Scripts\python.exe check_env.py
```

### 故障恢复

| 现象 | 处理 |
|---|---|
| `uv 不是可识别的命令` | 关闭并重新打开 PowerShell（让 PATH 生效） |
| pip install 慢 / 超时 | 已用清华镜像。仍超时把报错完整复制给 AI |
| 用户名是中文（如 `C:\Users\张三\`） | uv 或 pip 可能在路径处理上报编码错误。在 D 盘等英文路径下创建学习目录（如 `D:\quant-learning\`），把 TRAE 重新指向那里 |
| 任何其他报错 | 把终端完整输出（含命令 + 报错）复制给 AI 助手排查，**不要自己改命令重试** |
| 每次打开新 PowerShell | 无需激活虚拟环境。直接运行 `.venv\Scripts\python.exe check_env.py` |

## 验收标准

1. `.venv\Scripts\python.exe check_env.py` 最末 2 行输出：
   ```
   结果: 12/12 全部通过！
   环境配置完成，可以开始本书的实验。
   ```
2. 命令退出码为 0
3. 当前目录下存在 `.venv\` 目录、`requirements.lock.txt` 与 `check_env.py` 文件
4. 检查结果中输出实际使用的 `uv` 版本、Python 版本，以及 7 个依赖包的实际安装版本
5. 检查脚本输出的 Python 解释器路径位于当前目录的 `.venv` 中
6. Jupyter 命令使用上述 Python 解释器检查，不以其他环境中的同名命令作为通过依据

如果有任何检查项显示 `[FAIL]`，把 `check_env.py` 的完整输出复制给 AI 助手排查。
