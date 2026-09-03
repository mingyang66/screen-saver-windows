# Matrix Dashboard

Matrix Dashboard 是一个基于 PySide6 的全屏 Matrix 风格信息看板，使用绿色数字雨作为背景，并在中央显示：

- 系统当前时间
- 当天时间进度条
- 今日待办事项
- Matrix 风格的深色界面

程序支持直接运行，也可以打包为 Windows 屏幕保护程序。按 `Esc` 可以退出全屏看板。

## 文件说明

| 文件 | 作用 |
| --- | --- |
| `matrix_dash_v2.py` | PySide6 主程序 |
| `matrix_dash.py` | Tkinter 旧版程序，保留用于参考 |
| `matrix_dash.spec` | PyInstaller 打包配置 |
| `dist/` | PyInstaller 生成的可执行文件目录 |
| `build/` | PyInstaller 构建临时文件目录 |

## 环境要求

- Windows 10 或 Windows 11
- Python 3.10 或更高版本
- PySide6
- PyInstaller（仅打包时需要）

安装依赖：

```powershell
python -m pip install PySide6 pyinstaller
```

## 直接运行

在项目目录打开 PowerShell，执行：

```powershell
python matrix_dash_v2.py
```

程序会以全屏方式启动。按 `Esc` 退出。

## 打包为 EXE

### 方式一：使用项目配置文件

项目中已有 `matrix_dash.spec`，其中已经指定主程序为 `matrix_dash_v2.py`，并关闭控制台窗口。执行：

```powershell
pyinstaller matrix_dash.spec
```

生成文件：

```text
dist\matrix_dash.exe
```

### 方式二：直接使用命令行

如果不使用 `.spec` 文件，可以执行：

```powershell
pyinstaller --onefile --noconsole --name matrix_dash matrix_dash_v2.py
```

生成文件同样位于：

```text
dist\matrix_dash.exe
```

如果修改了 Python 源码，需要重新打包，并用新生成的文件替换旧文件。测试 EXE 时可以先双击运行，确认程序能够全屏显示并能用 `Esc` 退出。

## 设置为 Windows 屏幕保护程序

### 1. 修改文件扩展名

将打包后的文件：

```text
dist\matrix_dash.exe
```

复制一份并重命名为：

```text
matrix_dash.scr
```

确认文件不是以下错误名称：

```text
matrix_dash.scr.exe
matrix_dash.scr.scr
```

如果看不到扩展名，在文件资源管理器中打开：

```text
查看 → 显示 → 文件扩展名
```

### 2. 放置屏幕保护程序文件

将 `matrix_dash.scr` 复制到：

```text
C:\Windows\System32
```

复制时可能需要管理员权限。也可以把文件放在其他固定目录，然后在屏幕保护程序设置窗口中使用“浏览”选择它；放入 `System32` 通常更容易在屏保列表中找到。

### 3. 从控制面板设置

1. 打开“控制面板”。
2. 选择“外观和个性化”。
3. 点击“更改屏幕保护程序”。
4. 在“屏幕保护程序”下拉框中选择 `matrix_dash`。
5. 设置“等待”时间，例如 `1` 分钟。
6. 可选：勾选“在恢复时显示登录屏幕”。
7. 点击“应用”，再点击“确定”。
8. 点击“预览”确认屏幕保护程序可以启动。

也可以直接按 `Win + R`，执行：

```text
control desk.cpl,,@screensaver
```

Windows 11 还可以从以下位置进入：

```text
设置 → 个性化 → 锁屏界面 → 屏幕保护程序
```

## 屏保启动参数

Windows 启动屏幕保护程序时通常会传入 `/s` 参数。当前程序入口支持以下参数：

```text
/s  全屏运行
/c  配置入口（当前与全屏运行相同）
/p  预览入口（当前与全屏运行相同）
```

如果传入其他参数，程序会直接退出。这是为了避免 Windows 或其他程序使用非屏保参数启动时误运行看板。

## 屏幕保护程序不自动启动时

预览成功只表示 `.scr` 文件可以运行，不代表 Windows 的空闲计时一定正常。可以按以下顺序检查：

1. 打开屏幕保护程序设置，确认下拉框不是“无”，等待时间已保存。
2. 设置时间后不要移动鼠标、触摸板，也不要按键盘；建议等待超过设置时间 30 秒。
3. 打开“设置 → 系统 → 电源和电池”，临时将关闭屏幕和睡眠时间设为“从不”，避免电脑先关屏或睡眠。
4. 拔掉外接鼠标、键盘、扩展坞后再测试，部分设备会持续产生输入活动。
5. 关闭视频播放、远程控制、演示模式以及可能阻止休眠的工具。
6. 按 `Win + L` 测试的是 Windows 系统锁屏，不会启动自定义屏幕保护程序。

如果连 Windows 自带的屏幕保护程序也不生效，问题通常是系统策略或空闲检测，而不是本项目。Windows 专业版可以运行 `gpedit.msc`，检查：

```text
用户配置 → 管理模板 → 控制面板 → 个性化
```

确认“启用屏幕保护程序”和“屏幕保护程序超时”没有被设置为“已禁用”。公司、学校电脑的策略可能由管理员控制。

## 重要限制

屏幕保护程序不等同于 Windows 的真正锁屏界面：

- `.scr` 程序是在当前用户桌面中运行的。
- `Win + L` 仍然使用 Windows 自己的安全锁屏界面。
- 勾选“在恢复时显示登录屏幕”后，退出屏保可以要求重新登录。
- 普通 EXE 或 `.scr` 无法直接替换 Windows 的 `Win + L` 锁屏界面。

如果需要真正的无人值守锁屏，应使用 Windows 的 `Win + L`、自动锁屏策略或企业级 kiosk 配置，而不是依赖普通屏幕保护程序。
