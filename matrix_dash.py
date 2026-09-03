import tkinter as tk
import random
import time

class MatrixDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Matrix Dashboard")
        
        # 1. 窗口全屏与全黑设置
        self.width = self.root.winfo_screenwidth()
        self.height = self.root.winfo_screenheight()
        self.root.geometry(f"{self.width}x{self.height}+0+0")
        self.root.attributes("-fullscreen", True)
        self.root.configure(bg="black")
        
        # 2. 画布与基础配置
        self.canvas = tk.Canvas(root, width=self.width, height=self.height, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        self.font_size = 16
        self.columns = int(self.width / self.font_size)
        self.drops = [random.randint(-self.height // self.font_size, 0) for _ in range(self.columns)]
        self.stream_lengths = [random.randint(8, 28) for _ in range(self.columns)]
        self.matrix_chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        self.matrix_font = ("MS Gothic", self.font_size)
        self.title_font = ("Consolas", 24, "bold")
        self.time_font = ("Consolas", 14)
        self.progress_font = ("Consolas", 12)
        self.todo_font = ("Microsoft YaHei", 12)
        self.footer_font = ("Consolas", 10)
        self.background_color = "#000000"
        self.green_color = "#00FF00"
        self.highlight_color = "#FFFFFF"
        
        # 3. 动态配置区（在这里可以修改你的看板内容）
        self.title_text = "SYSTEM DASHBOARD"
        self.todo_list = [
            "1. 深度优化底层算力模型 (开会摸鱼)",
            "2. 清理系统多余缓存数据 (倒杯咖啡)",
            "3. 部署自动化运行脚本 (准备下班)"
        ]
        
        # 4. 键盘绑定：按 Esc 退出
        self.root.bind("<Escape>", lambda e: self.root.destroy())
        
        # 5. 启动循环
        self.run()

    def get_time_progress(self):
        """计算今天的时间进度条"""
        now = time.localtime()
        passed_seconds = now.tm_hour * 3600 + now.tm_min * 60 + now.tm_sec
        total_seconds = 24 * 3600
        percent = passed_seconds / total_seconds
        
        # 生成进度条视觉效果
        bar_length = 20
        filled_length = int(bar_length * percent)
        bar = "█" * filled_length + "░" * (bar_length - filled_length)
        return f"DAY PROGRESS: [{bar}] {percent*100:.2f}%"

    def draw_matrix(self):
        """绘制黑客帝国数字雨底色"""
        # 使用半透明黑色层覆盖，产生字符拖尾淡出效果
        # 由于 Tkinter 限制，用多次快速刷新模拟淡化
        self.canvas.create_rectangle(0, 0, self.width, self.height, fill=self.background_color, stipple="gray12")
        
        for i in range(len(self.drops)):
            x = i * self.font_size

            for offset in range(self.stream_lengths[i]):
                row = self.drops[i] - offset
                y = row * self.font_size
                if y < -self.font_size or y > self.height:
                    continue

                # 每列绘制一段字符流，最前端字符使用高亮色
                color = self.highlight_color if offset == 0 else self.green_color
                self.canvas.create_text(
                    x,
                    y,
                    text=random.choice(self.matrix_chars),
                    fill=color,
                    font=self.matrix_font,
                    anchor="nw",
                )

            if self.drops[i] * self.font_size > self.height and random.random() > 0.975:
                self.drops[i] = random.randint(-20, 0)
                self.stream_lengths[i] = random.randint(8, 28)
            else:
                self.drops[i] += 1

    def draw_dashboard(self):
        """在屏幕中央渲染高清核心数据面板"""
        cx = self.width // 2
        cy = self.height // 2
        
        # 绘制半透明黑色背景板
        pad_w, pad_h = 280, 160
        self.canvas.create_rectangle(cx - pad_w, cy - pad_h, cx + pad_w, cy + pad_h, fill=self.background_color, outline=self.green_color, width=2)
        
        # 1. 标题
        self.canvas.create_text(cx, cy - 120, text=self.title_text, fill=self.green_color, font=self.title_font)
        
        # 2. 实时系统时间
        current_time = time.strftime("TIME: %Y-%m-%d %H:%M:%S", time.localtime())
        self.canvas.create_text(cx, cy - 70, text=current_time, fill=self.green_color, font=self.time_font)
        
        # 3. 今日进度条
        progress_str = self.get_time_progress()
        self.canvas.create_text(cx, cy - 35, text=progress_str, fill=self.green_color, font=self.progress_font)
        
        # 4. 任务线
        self.canvas.create_line(cx - 240, cy, cx + 240, cy, fill=self.green_color, dash=(4, 4))
        
        # 5. 今日待办事项
        start_y = cy + 25
        for item in self.todo_list:
            self.canvas.create_text(cx - 230, start_y, text=item, fill=self.green_color, font=self.todo_font, anchor="w")
            start_y += 30
            
        # 底部提示
        self.canvas.create_text(cx, cy + 140, text="PRESS [ESC] TO EXIT SYSTEM", fill=self.green_color, font=self.footer_font)

    def run(self):
        """动画主循环"""
        self.canvas.delete("all")
        self.draw_matrix()
        self.draw_dashboard()
        # 约每 80 毫秒刷新一次屏幕，使数字雨下落更流畅
        self.root.after(80, self.run)

if __name__ == "__main__":
    app_root = tk.Tk()
    dashboard = MatrixDashboard(app_root)
    app_root.mainloop()
