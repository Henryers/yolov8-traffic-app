"""
更改默认的dataset以及train的存储路径（当自己电脑里有多个YOLO环境时可能会用到）
"""

import ultralytics

# 初始化 SettingsManager
settings = ultralytics.utils.SettingsManager()

# 更新设置
settings.update(runs_dir="D:/MyCode/public_project/yolov8-traffic-app/runs")
settings.update(datasets_dir="D:/MyCode/public_project/yolov8-traffic-app/dataset")

# 打印更新后的设置值
print(settings["runs_dir"])  # 输出：/new/runs/dir
print(settings["datasets_dir"])
