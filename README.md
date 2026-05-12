# Calc · Pratt Parser 计算器

一个用 Pratt 解析器实现的全功能命令行计算器。

## 🖥️ 网页版（手机可用）

👉 **https://lorrydong.github.io/calc-pratt-parser/**

打开浏览器即可使用，手机优化，支持所有功能。

## 🪟 Windows 版

### 方法一：直接运行 Python（推荐）

1. 安装 [Python 3](https://www.python.org/downloads/)（安装时勾选 "Add Python to PATH"）
2. 下载本仓库或直接下载 `calc.py`：
   ```
   curl -O https://raw.githubusercontent.com/lorrydong/calc-pratt-parser/main/calc.py
   ```
3. 命令行运行：
   ```
   python calc.py
   ```
   或双击 `calc.bat`（已包含在仓库中）

### 方法二：双击运行

下载 `calc.bat`，双击即可进入交互模式。

### 支持的功能

| 类别 | 操作 |
|------|------|
| 基本 | `+ - * /` |
| 取模/整除 | `% //` |
| 幂运算 | `**` 或 `^` |
| 括号 | `( )` |
| 一元负号 | `-5`, `-(2+3)` |
| 阶乘 | `5! = 120` |
| 函数 | `sqrt()`, `sin()`, `cos()`, `tan()`, `log()`, `ln()`, `abs()`, `floor()`, `ceil()`, `round()` |
| 常量 | `pi`, `e`, `tau` |
| 隐式乘法 | `2(3+4)`, `2pi`, `2sin(x)` |
| 表达式 | `calc "2 + 3 * 4"` |

### 测试

```
python -m unittest test_calc -v
```

53 个测试用例如下，全部通过。

---

Built with <a href="https://github.com/lorrydong">@lorrydong</a> using DeepSeek TUI.
