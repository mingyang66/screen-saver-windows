# Matrix Dashboard

基于 PySide6 的 Windows Matrix 风格屏幕保护程序，提供绿色数字雨、当前时间、当天进度条和待办事项面板。

## 环境

- Windows 10/11
- Python 3.10+
- PySide6
- PyInstaller（仅打包时需要）

```powershell
python -m pip install PySide6 pyinstaller
```

## 运行

直接运行全屏屏保：

```powershell
python matrix_dash.py /s
```

普通模式下按任意键、点击鼠标或移动鼠标退出。鼠标移动需要至少 5 像素才会触发退出。

打开配置窗口：

```powershell
python matrix_dash.py /c
```

配置包括标题、待办事项、数字雨字号和动画刷新间隔。配置保存到：

```text
%APPDATA%\MatrixDashboard\config.json
```

Windows 屏保预览由系统调用：

```text
matrix_dash.scr /p <窗口句柄>
```

预览模式会嵌入系统提供的预览窗口，不会全屏，也不会因输入事件退出。

## 打包为 Windows 屏幕保护程序

### 1. 安装依赖

在项目目录打开 PowerShell，执行：

```powershell
python -m pip install PySide6 pyinstaller
```

确认主程序可以启动：

```powershell
python matrix_dash.py /s
```

程序全屏显示后，可以按任意键或移动鼠标退出。

### 2. 使用 PyInstaller 构建

项目中的 `matrix_dash.spec` 已经指定入口文件为 `matrix_dash.py`，并关闭控制台窗口。执行：

```powershell
pyinstaller --noconfirm matrix_dash.spec
```

生成：

```text
dist\matrix_dash.exe
```

如果不使用 spec 文件，也可以直接构建：

```powershell
pyinstaller --onefile --noconsole --name matrix_dash matrix_dash.py
```

### 3. 转换为 `.scr` 文件

Windows 屏幕保护程序本质上是使用 `.scr` 扩展名的可执行文件。将：

```text
dist\matrix_dash.exe
```

复制一份并重命名为：

```text
matrix_dash.scr
```

建议先在资源管理器中打开：

```text
查看 → 显示 → 文件扩展名
```

确认最终文件名是：

```text
matrix_dash.scr
```

不要生成以下错误名称：

```text
matrix_dash.scr.exe
matrix_dash.scr.scr
```

### 4. 安装到 Windows

推荐使用固定目录保存屏保文件，例如：

```text
C:\Program Files\MatrixDashboard\matrix_dash.scr
```

也可以复制到系统屏保目录：

```text
C:\Windows\System32\matrix_dash.scr
```

复制到 `C:\Windows\System32` 通常需要管理员权限。使用固定目录可以避免系统更新或清理临时目录时丢失文件。

### 5. 在 Windows 中启用

使用快捷键 `Win + R` 打开运行窗口，执行：

```text
control desk.cpl,,@screensaver
```

然后：

1. 在“屏幕保护程序”下拉框中选择 `matrix_dash`。
2. 设置“等待”时间，例如 `1` 分钟。
3. 根据需要勾选“在恢复时显示登录屏幕”。
4. 点击“应用”。
5. 点击“预览”测试屏保效果。

Windows 11 也可以通过以下路径打开：

```text
设置 → 个性化 → 锁屏界面 → 屏幕保护程序
```

### 6. 配置屏保内容

在安装 `.scr` 文件之前或之后，都可以运行配置模式：

```powershell
python matrix_dash.py /c
```

如果已经只有打包后的程序，可以使用：

```powershell
matrix_dash.exe /c
```

配置内容包括：

- 看板标题
- 待办事项
- 数字雨字号
- 动画刷新间隔

配置保存到当前用户目录：

```text
%APPDATA%\MatrixDashboard\config.json
```

屏保启动时会自动读取该配置。

### 7. 预览参数说明

Windows 屏保设置窗口会自动传入预览窗口句柄：

```text
matrix_dash.scr /p <窗口句柄>
```

当前程序支持：

```text
/s                  全屏运行
/c                  打开配置窗口
/p <窗口句柄>       嵌入 Windows 预览窗口
```

不建议手动伪造 `/p` 句柄。通过 Windows 屏幕保护程序设置中的“预览”按钮测试即可。

### 8. 更新已安装版本

修改源代码后，重新执行：

```powershell
pyinstaller --noconfirm matrix_dash.spec
```

然后使用新生成的 `dist\matrix_dash.exe` 替换已安装的 `matrix_dash.scr`。如果文件正在被 Windows 屏保使用，请先在屏幕保护程序设置中选择“无”，再替换文件。

日志默认保存到：

```text
%APPDATA%\MatrixDashboard\matrix_dash.log
```

## matrix_cpu.py：硬件指标版

`matrix_cpu.py` 是独立变体，把数字雨字符替换为实时硬件指标文本，并在面板中新增 SYSTEM LOAD 区块（负载历史折线、CPU / GPU / MEM 进度条、网速与温度）。运行方式与 `matrix_dash.py` 相同：

```powershell
python matrix_cpu.py /s
```

额外依赖：

- psutil：CPU / 内存占用、网速（必需）
- nvidia-ml-py：NVIDIA 显卡负载 / 温度 / 显存（可选）
- pywin32：通过 WMI 读取 ACPI 热区温度（显示为 ZONE，取最热热区，可选）

```powershell
python -m pip install psutil
python -m pip install nvidia-ml-py pywin32
```

缺少可选依赖时对应指标显示为 `N/A`，不影响屏保运行。打包使用 `matrix_cpu.spec`：

```powershell
pyinstaller --noconfirm matrix_cpu.spec
```

两个版本共用同一份配置（`%APPDATA%\MatrixDashboard\config.json`）。

## 当前实现

- `/s` 模式为每个显示器创建一个全屏窗口
- `/p` 使用 Win32 `SetParent` 嵌入预览容器，并定期同步尺寸
- `/c` 提供可保存的配置界面
- 数字雨使用缓存字符和 `QElapsedTimer`，刷新间隔限制为 90~120ms
- 时间和当天进度每秒更新一次
- 面板、字体、进度条和待办布局根据窗口尺寸缩放
- 超长待办事项使用省略号显示
- 英文和中文字体具有回退方案

## 限制

`.scr` 是运行在当前用户桌面上的普通程序，不会替换 `Win + L` 的安全锁屏界面。勾选“在恢复时显示登录屏幕”后，屏保退出时可以要求重新登录。
