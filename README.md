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

## 打包

```powershell
pyinstaller --noconfirm matrix_dash.spec
```

生成：

```text
dist\matrix_dash.exe
```

将其复制并重命名为 `matrix_dash.scr`，再通过“屏幕保护程序设置”选择。确认资源管理器已显示文件扩展名，避免生成 `matrix_dash.scr.exe`。

日志默认保存到：

```text
%APPDATA%\MatrixDashboard\matrix_dash.log
```

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
