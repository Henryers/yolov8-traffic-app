"""
整个软件的完整代码
"""

import os
import sys
from collections import defaultdict
import numpy as np
import pandas as pd
import csv
from ultralytics import YOLO
from ultralytics.engine import predictor
import cv2
from MysqlTool import MysqlTool
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog, QGraphicsScene, QTabBar, QDialog, QHBoxLayout, QLabel, \
    QVBoxLayout, QPushButton, QTableWidgetItem, QMessageBox, QGraphicsLineItem, QLineEdit
from PyQt5.QtGui import QImage, QPixmap, QFont, QIcon, QPalette, QColor
from PyQt5.QtCore import Qt, QUrl, QTimer
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5 import uic
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from pyecharts.charts import HeatMap, Bar3D
from pyecharts import options as opts

# 登录本系统的用户名
Username = ""


class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # 使用uic加载UI文件
        self.ui = uic.loadUi("./ui/dialog.ui", self)
        # tab
        self.tabWidget = self.ui.tabWidget
        self.login_tab1 = self.ui.login_tab1
        self.reg_tab2 = self.ui.reg_tab2
        # tab1_login
        self.login_username = self.ui.login_username
        self.login_password = self.ui.login_password
        self.login_btn = self.ui.login_btn
        self.cancel_btn1 = self.ui.cancel_btn1
        # tab2_reg
        self.reg_username = self.ui.reg_username
        self.reg_password = self.ui.reg_password
        self.reg_btn = self.ui.reg_btn
        self.cancel_btn2 = self.ui.cancel_btn2
        # 连接按钮的点击信号到槽函数
        self.login_tab1.clicked.connect(self.open1)
        self.reg_tab2.clicked.connect(self.open2)
        self.login_btn.clicked.connect(self.login)
        self.reg_btn.clicked.connect(self.register)
        self.cancel_btn1.clicked.connect(self.cancel)
        self.cancel_btn2.clicked.connect(self.cancel)
        # 设置文本为密码格式
        self.login_password.setEchoMode(QLineEdit.Password)
        self.reg_password.setEchoMode(QLineEdit.Password)
        # 隐藏所有的Tab widget页面
        self.tabBar = self.tabWidget.findChild(QTabBar)
        self.tabBar.hide()
        # 默认打开首页
        self.tabWidget.setCurrentIndex(0)

    def open1(self):
        self.tabWidget.setCurrentIndex(0)

    def open2(self):
        self.tabWidget.setCurrentIndex(1)

    def login(self):
        # 在这里添加验证用户名和密码的逻辑
        username = self.login_username.text()
        password = self.login_password.text()
        if username == None or password == None:
            # 弹出对话框提示用户
            dialog = QMessageBox()
            dialog.setWindowTitle('warning')
            dialog.setIcon(QMessageBox.Warning)
            dialog.setText('用户名或密码不能为空！')
            dialog.exec_()
            return
        # 用户登录校验
        # 连接 MySQL 数据库（使用with能确保在使用完毕后自动关闭游标和连接，以免忘记手动关闭）
        with MysqlTool() as db:
            # 执行查询数据库字段的SQL语句
            # rows = db.execute('insert into users (username, password) values (#{username}, #{password})', commit=True)
            sql = "select * from user where name = %s and pwd = %s"
            args = (username, password)
            rows = db.execute(sql, args)

        # 查询到1条数据，说明用户存在并且密码输入正确
        if len(rows) == 1:
            try:
                dialog = QMessageBox()
                dialog.setWindowTitle('success')
                dialog.setIcon(QMessageBox.Information)
                dialog.setText('登录成功！')
                dialog.exec_()
                self.accept()  # 登录成功，关闭对话框
                global Username
                Username = rows[0][1]  # 对登录的用户名进行赋值
            except Exception as e:
                print(e)
        # 查询不到数据（name unique 不可能有多条数据，说明用户名或密码错误）
        else:
            print('登录失败，请重试！')
            # 弹出对话框提示用户
            dialog = QMessageBox()
            dialog.setWindowTitle('error')
            dialog.setIcon(QMessageBox.Critical)
            dialog.setText('登录失败，请重试！')
            dialog.exec_()

    def register(self):
        username = self.reg_username.text()
        password = self.reg_password.text()
        if username == None or password == None:
            # 弹出对话框提示用户
            dialog = QMessageBox()
            dialog.setWindowTitle('warning')
            dialog.setIcon(QMessageBox.Warning)
            dialog.setText('用户名或密码不能为空！')
            dialog.exec_()
            return
        # 连接 MySQL 数据库（使用with能确保在使用完毕后自动关闭游标和连接，以免忘记手动关闭）
        with MysqlTool() as db:
            # 1. 先执行查询数据库字段的SQL语句，看看用户名是否已被注册
            sql = "select * from user where name = %s"
            args = (username)
            rows = db.execute(sql, args)
            # 2. 再判断是否能插入新数据
            # 用户名已被注册
            if len(rows) == 1:
                # 弹出对话框提示用户
                dialog = QMessageBox()
                dialog.setWindowTitle('warning')
                dialog.setIcon(QMessageBox.Warning)
                dialog.setText('用户名已被使用！')
                dialog.exec_()
            # 可以正常插入
            else:
                sql = "INSERT INTO user (name, pwd) VALUES (%s, %s)"
                args = (username, password)
                db.execute(sql, args, commit=True)
                # 弹出对话框提示用户
                dialog = QMessageBox()
                dialog.setWindowTitle('success')
                dialog.setIcon(QMessageBox.Information)
                dialog.setText('注册成功！')
                dialog.exec_()

    def cancel(self):
        exit()


class CustomGridScene(QGraphicsScene):
    def draw_grid(self):
        # Draw horizontal lines
        for i in range(0, 210, 10):
            line = QGraphicsLineItem(0, i, 210, i)
            self.addItem(line)
        # Draw vertical lines
        for i in range(0, 210, 10):
            line = QGraphicsLineItem(i, 0, i, 210)
            self.addItem(line)


class MyWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # 显示登录对话框
        login_dialog = LoginDialog()
        result = login_dialog.exec_()
        # 检查登录对话框返回结果
        if result == QDialog.Accepted:
            # 加载qt-designer中设计的ui文件
            self.ui = uic.loadUi("./ui/main.ui")
            # 菜单下拉框
            self.actiondefault = self.ui.actiondefault
            self.actionblack = self.ui.actionblack
            self.actionwhite = self.ui.actionwhite
            self.actionblue = self.ui.actionblue
            self.actionintro = self.ui.actionintro
            self.actionversion = self.ui.actionversion
            self.actionexit = self.ui.actionexit
            # 侧边栏
            self.tabWidget = self.ui.tabWidget
            self.tab_image = self.ui.tab_image
            self.tab_video = self.ui.tab_video
            self.tab_track = self.ui.tab_track
            self.tab_count = self.ui.tab_count
            self.test2_btn = self.ui.test2_btn
            self.test3_btn = self.ui.test3_btn
            # username
            self.username = self.ui.username
            global Username
            print(str(Username))
            self.username.setText(str(Username))
            # tab1_image
            self.raw_img = self.ui.raw_image
            self.res_img = self.ui.res_image
            self.select_btn = self.ui.select_btn
            self.show_btn = self.ui.show_btn
            # tab1_data
            self.model1 = self.ui.combo1
            self.conf1 = self.ui.conf1
            self.conf1.setRange(0.0, 1.0)  # 设置范围
            self.conf1.setSingleStep(0.01)  # 设置步长
            self.conf1.setValue(0.25)  # 设置初始值
            self.IOU1 = self.ui.IOU1
            self.IOU1.setRange(0.0, 1.0)  # 设置范围
            self.IOU1.setSingleStep(0.01)  # 设置步长
            self.IOU1.setValue(0.45)  # 设置初始值
            self.class1 = self.ui.class1
            # tab2_video1
            self.video1 = self.ui.video1
            self.choose_video = self.ui.choose_video
            self.play_pause1 = self.ui.play_pause1
            # 创建一个媒体播放器对象和一个视频窗口对象
            self.media_player1 = QMediaPlayer()
            # 将视频窗口设置为媒体播放器的显示窗口
            self.media_player1.setVideoOutput(self.video1)
            # 进度条
            self.media_player1.durationChanged.connect(self.getDuration1)
            self.media_player1.positionChanged.connect(self.getPosition1)
            self.ui.slider1.sliderMoved.connect(self.updatePosition1)
            # tab2_video2
            self.video2 = self.ui.video2
            self.show_video = self.ui.show_video
            self.play_pause2 = self.ui.play_pause2
            # 创建一个媒体播放器对象和一个视频窗口对象
            self.media_player2 = QMediaPlayer()
            # 将视频窗口设置为媒体播放器的显示窗口
            self.media_player2.setVideoOutput(self.video2)
            # 进度条
            self.media_player2.durationChanged.connect(self.getDuration2)
            self.media_player2.positionChanged.connect(self.getPosition2)
            self.ui.slider2.sliderMoved.connect(self.updatePosition2)
            # tab2_data
            self.model2 = self.ui.combo2
            self.conf2 = self.ui.conf2
            self.conf2.setRange(0.0, 1.0)  # 设置范围
            self.conf2.setSingleStep(0.01)  # 设置步长
            self.conf2.setValue(0.25)  # 设置初始值
            self.IOU2 = self.ui.IOU2
            self.IOU2.setRange(0.0, 1.0)  # 设置范围
            self.IOU2.setSingleStep(0.01)  # 设置步长
            self.IOU2.setValue(0.45)  # 设置初始值
            self.class2 = self.ui.class2
            # tab3_track
            self.video3 = self.ui.video3
            self.play_pause3 = self.ui.play_pause3
            self.slider3 = self.ui.slider3
            self.time3 = self.ui.time3
            self.choose_btn = self.ui.choose_btn
            self.track_path = self.ui.track_path
            self.track_btn = self.ui.track_btn
            self.export3 = self.ui.export3
            # 创建一个媒体播放器对象和一个视频窗口对象
            self.media_player3 = QMediaPlayer()
            # 将视频窗口设置为媒体播放器的显示窗口
            self.media_player3.setVideoOutput(self.video3)
            # 进度条
            self.media_player3.durationChanged.connect(self.getDuration3)
            self.media_player3.positionChanged.connect(self.getPosition3)
            self.ui.slider3.sliderMoved.connect(self.updatePosition3)
            # tab3_data
            self.conf3 = self.ui.conf3
            self.conf3.setRange(0.0, 1.0)  # 设置范围
            self.conf3.setSingleStep(0.01)  # 设置步长
            self.conf3.setValue(0.25)  # 设置初始值
            self.IOU3 = self.ui.IOU3
            self.IOU3.setRange(0.0, 1.0)  # 设置范围
            self.IOU3.setSingleStep(0.01)  # 设置步长
            self.IOU3.setValue(0.45)  # 设置初始值
            self.class3 = self.ui.class3
            # tab4_count
            self.video4 = self.ui.video4
            self.play_pause4 = self.ui.play_pause4
            self.slider4 = self.ui.slider4
            self.time4 = self.ui.time4
            self.choose_btn4 = self.ui.choose_btn4
            self.count_path = self.ui.count_path
            self.count_btn = self.ui.count_btn
            # 创建一个媒体播放器对象和一个视频窗口对象
            self.media_player4 = QMediaPlayer()
            # 将视频窗口设置为媒体播放器的显示窗口
            self.media_player4.setVideoOutput(self.video4)
            # 进度条
            self.media_player4.durationChanged.connect(self.getDuration4)
            self.media_player4.positionChanged.connect(self.getPosition4)
            self.ui.slider4.sliderMoved.connect(self.updatePosition4)
            # tab4_data
            self.conf4 = self.ui.conf4
            self.conf4.setRange(0.0, 1.0)  # 设置范围
            self.conf4.setSingleStep(0.01)  # 设置步长
            self.conf4.setValue(0.25)  # 设置初始值
            self.IOU4 = self.ui.IOU4
            self.IOU4.setRange(0.0, 1.0)  # 设置范围
            self.IOU4.setSingleStep(0.01)  # 设置步长
            self.IOU4.setValue(0.45)  # 设置初始值
            self.class4 = self.ui.class4
            # tab5_dataset
            self.select_xlsx = self.ui.select_xlsx
            self.xlsx = self.ui.xlsx
            self.show_row = self.ui.show_row
            self.show_col = self.ui.show_col
            self.input_id = self.ui.input_id
            self.draw5 = self.ui.draw5
            self.show_image5 = self.ui.show_image5
            self.chart5 = self.ui.chart5
            self.export5 = self.ui.export5
            # tab6_graph
            self.hotmap = self.ui.hotmap
            self.chart6_2 = self.ui.chart6_2
            self.data6_1 = self.ui.data6_1
            self.data6_2 = self.ui.data6_2
            self.data6_3 = self.ui.data6_3
            self.export6_1 = self.ui.export6_1
            self.export6_2 = self.ui.export6_2
            # 侧边栏的click点击事件
            self.tab_image.clicked.connect(self.open1)
            self.tab_video.clicked.connect(self.open2)
            self.tab_track.clicked.connect(self.open3)
            self.tab_count.clicked.connect(self.open4)
            self.test2_btn.clicked.connect(self.open5)
            self.test3_btn.clicked.connect(self.open6)
            # tab1的点击事件
            self.model1.currentIndexChanged.connect(self.combo1_change)
            self.select_btn.clicked.connect(self.select_image)
            self.show_btn.clicked.connect(self.detect_objects)
            # tab2的点击事件
            self.model2.currentIndexChanged.connect(self.combo2_change)
            self.choose_video.clicked.connect(self.chooseVideo1)
            self.play_pause1.clicked.connect(self.playPause1)
            self.play_pause2.clicked.connect(self.playPause2)
            self.show_video.clicked.connect(self.showVideo)
            # tab3的点击事件
            self.choose_btn.clicked.connect(self.chooseVideo3)
            self.play_pause3.clicked.connect(self.playPause3)
            self.track_btn.clicked.connect(self.showTrack)
            self.export3.clicked.connect(self.export_location)
            # tab4的点击事件
            self.choose_btn4.clicked.connect(self.chooseVideo4)
            self.play_pause4.clicked.connect(self.playPause4)
            self.count_btn.clicked.connect(self.showCount)
            # tab5的点击事件
            self.select_xlsx.clicked.connect(self.selectDataset)
            self.draw5.clicked.connect(self.drawChart5)
            self.export5.clicked.connect(self.export_chart5)
            # 隐藏所有的Tab widget页面
            self.tabBar = self.tabWidget.findChild(QTabBar)
            self.tabBar.hide()
            # 默认打开首页
            self.tabWidget.setCurrentIndex(0)
            # 菜单栏点击事件
            self.actionwhite.triggered.connect(self.menu_white)
            self.actionblack.triggered.connect(self.menu_black)
            self.actionblue.triggered.connect(self.menu_blue)
            self.actiondefault.triggered.connect(self.menu_default)
            self.actionintro.triggered.connect(self.menu_intro)
            self.actionversion.triggered.connect(self.menu_version)
            self.actionexit.triggered.connect(self.myexit)
            # 保存图表
            self.export6_1.clicked.connect(self.export_chart6_1)
            self.export6_2.clicked.connect(self.export_chart6_2)

    def menu_default(self):
        print('default')
        stylesheet1 = f"QMainWindow{{background-color: rgb(240,240,240)}}"
        stylesheet2 = f"QWidget{{background-color: rgb(240,240,240)}}"
        stylesheet3 = f"QLabel{{color: rgb(20, 120, 80); font: 26pt'黑体'; font-weight: bold;}}"
        stylesheet4 = f"QLabel{{background-color: rgb(230, 230, 230)}}"
        stylesheet5 = f"QLabel{{color: rgb(100, 100, 100); font-size: 16pt; font-weight: bold;}}"
        self.ui.setStyleSheet(stylesheet1)
        self.ui.centralwidget.setStyleSheet(stylesheet2)
        self.ui.tab.setStyleSheet(stylesheet2)
        self.ui.tab_2.setStyleSheet(stylesheet2)
        self.ui.tab_3.setStyleSheet(stylesheet2)
        self.ui.tab_4.setStyleSheet(stylesheet2)
        self.ui.tab_5.setStyleSheet(stylesheet2)
        self.ui.tab_6.setStyleSheet(stylesheet2)
        self.ui.label_11.setStyleSheet(stylesheet3)
        self.ui.label_38.setStyleSheet(stylesheet4)
        self.ui.time1.setStyleSheet(stylesheet5)
        self.ui.time2.setStyleSheet(stylesheet5)
        self.ui.time3.setStyleSheet(stylesheet5)
        self.ui.time4.setStyleSheet(stylesheet5)

    def menu_white(self):
        print('light')
        stylesheet1 = f"QMainWindow{{background-color: rgb(250,250,250)}}"
        stylesheet2 = f"QWidget{{background-color: rgb(250,250,250)}}"
        stylesheet3 = f"QLabel{{color: rgb(20, 120, 80); font: 26pt'黑体'; font-weight: bold;}}"
        stylesheet4 = f"QLabel{{background-color: rgb(240, 240, 240)}}"
        stylesheet5 = f"QLabel{{color: rgb(100, 100, 100); font-size: 16pt; font-weight: bold;}}"
        self.ui.setStyleSheet(stylesheet1)
        self.ui.centralwidget.setStyleSheet(stylesheet2)
        self.ui.tab.setStyleSheet(stylesheet2)
        self.ui.tab_2.setStyleSheet(stylesheet2)
        self.ui.tab_3.setStyleSheet(stylesheet2)
        self.ui.tab_4.setStyleSheet(stylesheet2)
        self.ui.tab_5.setStyleSheet(stylesheet2)
        self.ui.tab_6.setStyleSheet(stylesheet2)
        self.ui.label_11.setStyleSheet(stylesheet3)
        self.ui.label_38.setStyleSheet(stylesheet4)
        self.ui.time1.setStyleSheet(stylesheet5)
        self.ui.time2.setStyleSheet(stylesheet5)
        self.ui.time3.setStyleSheet(stylesheet5)
        self.ui.time4.setStyleSheet(stylesheet5)

    def menu_black(self):
        print('dark')
        stylesheet1 = f"QMainWindow{{background-color: rgb(50,50,50)}}"
        stylesheet2 = f"QWidget{{background-color: rgb(50,50,50)}}"
        stylesheet3 = f"QLabel{{color: rgb(40, 240, 160); font: 26pt'黑体'; font-weight: bold;}}"
        stylesheet4 = f"QLabel{{background-color: rgb(40, 60, 50)}}"
        stylesheet5 = f"QLabel{{color: rgb(250, 250, 250); font-size: 16pt; font-weight: bold;}}"
        self.ui.setStyleSheet(stylesheet1)
        self.ui.centralwidget.setStyleSheet(stylesheet2)
        self.ui.tab.setStyleSheet(stylesheet2)
        self.ui.tab_2.setStyleSheet(stylesheet2)
        self.ui.tab_3.setStyleSheet(stylesheet2)
        self.ui.tab_4.setStyleSheet(stylesheet2)
        self.ui.tab_5.setStyleSheet(stylesheet2)
        self.ui.tab_6.setStyleSheet(stylesheet2)
        self.ui.label_11.setStyleSheet(stylesheet3)
        self.ui.label_38.setStyleSheet(stylesheet4)
        self.ui.time1.setStyleSheet(stylesheet5)
        self.ui.time2.setStyleSheet(stylesheet5)
        self.ui.time3.setStyleSheet(stylesheet5)
        self.ui.time4.setStyleSheet(stylesheet5)

    def menu_blue(self):
        print('blue')
        stylesheet1 = f"QMainWindow{{background-color: rgb(230,245,255)}}"
        stylesheet2 = f"QWidget{{background-color: rgb(230,245,255)}}"
        stylesheet3 = f"QLabel{{color: rgb(20, 120, 80); font: 26pt'黑体'; font-weight: bold;}}"
        stylesheet4 = f"QLabel{{background-color: rgb(210, 240, 255)}}"
        stylesheet5 = f"QLabel{{color: rgb(100, 100, 100); font-size: 16pt; font-weight: bold;}}"
        self.ui.setStyleSheet(stylesheet1)
        self.ui.centralwidget.setStyleSheet(stylesheet2)
        self.ui.tab.setStyleSheet(stylesheet2)
        self.ui.tab_2.setStyleSheet(stylesheet2)
        self.ui.tab_3.setStyleSheet(stylesheet2)
        self.ui.tab_4.setStyleSheet(stylesheet2)
        self.ui.tab_5.setStyleSheet(stylesheet2)
        self.ui.tab_6.setStyleSheet(stylesheet2)
        self.ui.label_11.setStyleSheet(stylesheet3)
        self.ui.label_38.setStyleSheet(stylesheet4)
        self.ui.time1.setStyleSheet(stylesheet5)
        self.ui.time2.setStyleSheet(stylesheet5)
        self.ui.time3.setStyleSheet(stylesheet5)
        self.ui.time4.setStyleSheet(stylesheet5)

    def menu_intro(self):
        print('intro')
        try:
            dialog = QDialog()
            dialog.setWindowTitle('introduction')
            dialog.setFixedSize(1200, 800)  # 设置对话框大小
            # 总体水平布局
            layout = QHBoxLayout(dialog)
            # 左侧的 QLabel，用于显示图片
            image_label = QLabel()
            pixmap = QPixmap('image/2.png')
            pixmap = pixmap.scaled(400, 350)
            image_label.setPixmap(pixmap)
            image_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(image_label)
            # 设置标题字体
            font = QFont()
            font.setPointSize(18)  # 设置字体大小
            font.setBold(True)  # 加粗
            # 设置主要文字字体
            font1 = QFont()
            font1.setPointSize(10)  # 设置字体大小
            font1.setBold(True)  # 加粗
            # 创建 QPalette 对象并设置文本颜色
            palette_title = QPalette()
            palette_text = QPalette()
            # 设置为绿色
            palette_title.setColor(QPalette.WindowText, QColor(10, 80, 50))
            palette_text.setColor(QPalette.WindowText, QColor(30, 180, 80))
            # 右侧的 QVBoxLayout，用于显示文字
            text_layout = QVBoxLayout()
            label1 = QLabel("基于YOLOv8的车辆轨迹识")
            label1.setAlignment(Qt.AlignCenter)  # 居中对齐
            label1.setFont(font)
            label1.setPalette(palette_title)
            label2 = QLabel("别与目标检测研究分析")
            label2.setAlignment(Qt.AlignCenter)  # 居中对齐
            label2.setFont(font)
            label2.setPalette(palette_title)
            label3 = QLabel("本软件致力于交通物体追踪检测，")
            label3.setAlignment(Qt.AlignCenter)  # 居中对齐
            label3.setPalette(palette_text)
            label3.setFont(font1)
            label4 = QLabel("通过YOLOv8进行轨迹识别绘制等任务，")
            label4.setAlignment(Qt.AlignCenter)  # 居中对齐
            label4.setPalette(palette_text)
            label4.setFont(font1)
            label5 = QLabel("同时对采集的数据整理成交通数据集，")
            label5.setAlignment(Qt.AlignCenter)  # 居中对齐
            label5.setPalette(palette_text)
            label5.setFont(font1)
            label6 = QLabel("方便后续对数据的处理分析和可视化。")
            label6.setAlignment(Qt.AlignCenter)  # 居中对齐
            label6.setPalette(palette_text)
            label6.setFont(font1)
            text_layout.addSpacing(100)  # 设置间距为100
            text_layout.addWidget(label1)
            text_layout.addWidget(label2)
            text_layout.addSpacing(50)  # 设置间距为50
            text_layout.addWidget(label3)
            text_layout.addWidget(label4)
            text_layout.addWidget(label5)
            text_layout.addWidget(label6)
            text_layout.addSpacing(100)  # 设置间距为100
            # 关闭按钮
            btn = QPushButton('关闭', dialog)
            btn.setFixedSize(150, 60)
            # 连接关闭信号
            btn.clicked.connect(dialog.close)
            text_layout.addWidget(btn, alignment=Qt.AlignCenter)
            layout.addLayout(text_layout)
            # 加载对话框图标
            dialog.setWindowIcon(QIcon("image/2.png"))
            # 显示对话框，而不是一闪而过
            dialog.exec()
        except Exception as e:
            print(e)

    def menu_version(self):
        print('version')
        try:
            dialog = QDialog()
            dialog.setWindowTitle('version')
            dialog.setFixedSize(1200, 800)  # 设置对话框大小
            # 总体水平布局
            layout = QHBoxLayout(dialog)
            # 左侧的 QLabel，用于显示图片
            image_label = QLabel()
            pixmap = QPixmap("image/2.png")
            pixmap = pixmap.scaled(400, 350)
            image_label.setPixmap(pixmap)
            image_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(image_label)
            # 设置标题字体
            font = QFont()
            font.setPointSize(18)  # 设置字体大小
            font.setBold(True)  # 加粗
            # 设置主要文字字体
            font1 = QFont()
            font1.setPointSize(14)  # 设置字体大小
            font1.setBold(True)  # 加粗
            # 创建 QPalette 对象并设置文本颜色
            palette_title = QPalette()
            palette_text = QPalette()
            # 设置为绿色
            palette_title.setColor(QPalette.WindowText, QColor(10, 80, 50))
            palette_text.setColor(QPalette.WindowText, QColor(30, 180, 80))
            # 右侧的 QVBoxLayout，用于显示文字
            text_layout = QVBoxLayout()
            label1 = QLabel("基于YOLOv8的车辆轨迹识")
            label1.setAlignment(Qt.AlignCenter)  # 居中对齐
            label1.setFont(font)
            label1.setPalette(palette_title)
            label2 = QLabel("别与目标检测研究分析")
            label2.setAlignment(Qt.AlignCenter)  # 居中对齐
            label2.setFont(font)
            label2.setPalette(palette_title)
            label3 = QLabel("版本:  V 1.0")
            label3.setAlignment(Qt.AlignCenter)  # 居中对齐
            label3.setFont(font1)
            label3.setPalette(palette_text)
            label4 = QLabel("时间:  2024年04月11日")
            label4.setAlignment(Qt.AlignCenter)  # 居中对齐
            label4.setFont(font1)
            label4.setPalette(palette_text)
            text_layout.addSpacing(100)  # 设置间距为10
            text_layout.addWidget(label1)
            text_layout.addWidget(label2)
            text_layout.addSpacing(50)  # 设置间距为10
            text_layout.addWidget(label3)
            text_layout.addWidget(label4)
            text_layout.addSpacing(100)  # 设置间距为10
            btn = QPushButton('关闭', dialog)
            btn.setFixedSize(150, 60)
            btn.clicked.connect(dialog.close)
            text_layout.addWidget(btn, alignment=Qt.AlignCenter)
            layout.addLayout(text_layout)
            # 加载对话框图标
            dialog.setWindowIcon(QIcon("image/2.png"))
            # 显示对话框，而不是一闪而过
            dialog.exec()
        except Exception as e:
            print(e)

    # tab
    def open1(self):
        self.tabWidget.setCurrentIndex(0)

    def open2(self):
        self.tabWidget.setCurrentIndex(1)

    def open3(self):
        self.tabWidget.setCurrentIndex(2)

    def open4(self):
        self.tabWidget.setCurrentIndex(3)

    def open5(self):
        self.tabWidget.setCurrentIndex(4)

    def open6(self):
        self.tabWidget.setCurrentIndex(5)
        print('绘制热力图')
        try:
            data = pd.DataFrame(columns=['x', 'y'])
            data['x'] = self.df['X']
            data['y'] = self.df['Y']
            list_x = [0, 300, 600, 900, 1200, 1500, 1800, 2100]
            list_y = [0, 200, 400, 600, 800, 1000, 1200, 1400]
            res = np.zeros((7, 7))
            for index, row in self.df.iterrows():
                # print(row['x'], row['y'])
                for i in range(7):
                    if list_x[i] <= row['X'] and row['X'] <= list_x[i + 1]:
                        for j in range(7):
                            if list_y[j] <= row['Y'] and row['Y'] <= list_y[j + 1]:
                                res[i][j] += 1
            x = ["0", "300", "600", "900", "1200", "1500", "1800"]
            y = ["0", "200", "400", "600", "800", "1000", "1200"]
            data = [(i, j, res[i][j]) for i in range(7) for j in range(7)]
            # data = [[d[1], d[0], d[2]] for d in data]
            heatmap = (
                HeatMap(init_opts=opts.InitOpts(width="1000px", height="750px"))
                .add_xaxis(x)
                .add_yaxis("", y, data)
                .set_global_opts(
                    title_opts=opts.TitleOpts(title="热力图",
                                              title_textstyle_opts=opts.TextStyleOpts(font_size=24, padding=20)),
                    visualmap_opts=opts.VisualMapOpts(
                        max_=150,
                        range_color=[
                            "#abd9e9", "#e0f3f8", "#ffffbf", "#fee090",
                            "#fdae61", "#f46d43", "#d73027", "#a50026"
                        ],
                    )
                )
                .set_series_opts(
                    label_opts=opts.LabelOpts(font_size=24)
                )
            )
            # 获取图表的HTML内容
            self.hotmap_html = heatmap.render_embed()
            # 将图表的HTML内容加载到QWebEngineView中
            self.hotmap.setHtml(self.hotmap_html)
        except Exception as e:
            print(e)
        print('绘制柱状图')
        try:
            # 绘制chart6_2
            self.figure6_2 = Figure(figsize=(5, 4))
            self.myax6 = self.figure6_2.add_subplot(111)
            self.canvas = FigureCanvas(self.figure6_2)
            # 准备数据: x 物体类别  y 对应类别检测到的数量
            # 如果已经track并拿到检测到是词频信息，那就展示这些信息的柱状图
            # 初始值默认都是0
            self.data6_1.setText('0')
            self.data6_2.setText('0')
            self.data6_3.setText('0')
            if hasattr(self, 'category_nums'):
                print("category_nums 存在")
            else:
                print("category_nums 不存在")
            if hasattr(self, 'category_nums'):
                print(self.category_nums)
                # 拿到 keys values 变成列表数据，下面直接用！
                x_data = []
                for i in range(len(self.category_nums)):
                    x_data.append(i)
                # x_data = list(self.category_nums.keys())
                y_data = list(self.category_nums.values())
                # 写出检测到的车辆和行人的数量
                all_objects = 0  # 检测到的所有物体数量
                for key, value in self.category_nums.items():
                    all_objects += value
                    if key == 0:
                        print(key, value)
                        self.data6_2.setText(str(value))
                    if key == 2:
                        print(key, value)
                        self.data6_1.setText(str(value))
                    self.data6_3.setText(str(all_objects))
            # 否则展示默认数据
            else:
                x_data = ['one', 'two', 'three', 'four']
                y_data = [10, 20, 15, 25]
            # 画出词频表
            self.myax6.bar(x_data, y_data, color=['skyblue', 'lightgreen', 'lightcoral', 'lightblue'])
            # 添加标签和标题
            self.myax6.set_xlabel('categories')
            self.myax6.set_ylabel('nums')
            self.myax6.set_title('categoryies’ nums')
            # 绘制柱状图
            self.canvas.draw()
            scene = QGraphicsScene(self)
            scene.addWidget(self.canvas)
            self.chart6_2.setScene(scene)
        except Exception as e:
            print(e)

    # --- tab1 image 点击事件回调函数 ---
    def combo1_change(self, index):
        print("你选择了：" + self.model1.currentText())

    def select_image(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, 'Open Image File', '', 'Images (*.png *.jpg *.bmp)')
        if file_path:
            self.image_path = file_path
            self.load_image()

    def load_image(self):
        scene = QGraphicsScene()
        img = QPixmap(self.image_path)
        # img = img.scaled(450, 400)
        scene.addPixmap(img)
        self.raw_img.setScene(scene)

    def show_image(self):
        scene = QGraphicsScene()
        img = QPixmap(self.image_path)
        # img = img.scaled(450, 400)
        scene.addPixmap(img)
        self.res_img.setScene(scene)

    def detect_objects(self):
        if not self.image_path:
            return
        conf1 = self.conf1.value()
        conf1 = float("{:.2f}".format(conf1))
        IOU1 = self.IOU1.value()
        IOU1 = float("{:.2f}".format(IOU1))
        if self.class1.text() == '':
            class1 = -1
        else:
            class1 = int(self.class1.text())
        # YOLOv8 - img  start
        # 根据用户的combo选择加载预训练模型
        if self.model1.currentText() == '物体检测':
            model = YOLO('yolov8n.pt')
        elif self.model1.currentText() == '实例分割':
            model = YOLO('yolov8n-seg.pt')
        # 用户没有指定classes类别
        if class1 == -1:
            model.predict(self.image_path, save=True, imgsz=320, conf=conf1, iou=IOU1)
        # 用户指定了预测类别
        else:
            model.predict(self.image_path, save=True, imgsz=320, conf=conf1, iou=IOU1, classes=class1)
        # 全局变量应该是拿到目标前缀路径了
        print(predictor.update_global_var())
        # 拿到当前图片路径末尾的文件名
        file_name = os.path.basename(self.image_path)
        print(file_name)
        # 拼接路径
        try:
            file_path = str(predictor.update_global_var()) + "\\" + file_name
            print("拼接后的图片输出路径：", file_path)
            self.image_path = file_path
            self.show_image()
        except Exception as e:
            print(e)

    # --- tab2 video 点击事件回调函数 ---
    def combo2_change(self, index):
        print("你选择了：" + self.model2.currentText())

    # 选择原视频1
    def chooseVideo1(self):
        try:
            # 拿到视频路径，存到video_path里
            file_dialog = QFileDialog()
            file_path, _ = file_dialog.getOpenFileName(self, 'Open Video File', '', 'Videos (*.mp4 *.avi)')
            if file_path:
                self.video_path = file_path
                print("绝对 / 相对路径？ file_path:  " + file_path)
                self.media_player1.setMedia(QMediaContent(QUrl(file_path)))
                self.media_player1.play()
        except Exception as e:
            print(e)

    # 播放/暂停
    def playPause1(self):
        if self.media_player1.state() == 1:
            self.media_player1.pause()
        else:
            self.media_player1.play()

    # 视频总时长获取
    def getDuration1(self, d):
        # d是获取到的视频总时长（ms）
        self.ui.slider1.setRange(0, d)
        self.ui.slider1.setEnabled(True)
        self.displayTime1(d)

    # 视频实时位置获取
    def getPosition1(self, p):
        self.ui.slider1.setValue(p)
        self.displayTime1(self.ui.slider1.maximum() - p)

    # 显示剩余时间
    def displayTime1(self, ms):
        minutes = int(ms / 60000)
        seconds = int((ms - minutes * 60000) / 1000)
        self.ui.time1.setText('{}:{}'.format(minutes, seconds))

    # 用进度条更新视频位置
    def updatePosition1(self, v):
        self.media_player1.setPosition(v)
        self.displayTime1(self.ui.slider1.maximum() - v)

    # tab2 处理并播放结果视频
    def showVideo(self):
        # 先处理，得到结果视频
        if not self.video_path:
            print('请先选择视频，再进行操作！')
            return
        conf2 = self.conf2.value()
        conf2 = float("{:.2f}".format(conf2))
        print("Current value:", conf2)
        print(type(conf2))
        IOU2 = self.IOU2.value()
        IOU2 = float("{:.2f}".format(IOU2))
        # 看是否转换的格式符合要求
        print(IOU2)
        if self.class2.text() == '':
            class2 = -1
        else:
            class2 = int(self.class2.text())
        # YOLOv8 - img  start
        # 根据用户combo选择加载预训练模型
        if self.model2.currentText() == '物体检测':
            model = YOLO('yolov8n.pt')
            # model = YOLO('E:\YOLOv8_物体分类检测\\train_object\\runs\detect\\train10\weights\\best.pt')
        elif self.model2.currentText() == '实例分割':
            model = YOLO('yolov8n-seg.pt')
        # 打开视频文件
        cap = cv2.VideoCapture(self.video_path)
        # 获取视频帧的维度
        frame_width = int(cap.get(3))
        frame_height = int(cap.get(4))
        # 拿到当前图片路径末尾的文件名
        file_name = os.path.basename(self.video_path)
        # 创建VideoWriter对象，指定输出视频目录
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter("video_output/" + file_name, fourcc, 20.0,
                              (frame_width, frame_height))
        # 循环视频帧
        while cap.isOpened():
            # 读取某一帧
            success, frame = cap.read()
            if success:
                # 用户没有指定classes类别
                if class2 == -1:
                    results = model.predict(frame, conf=conf2, iou=IOU2)
                # 用户指定了类别
                else:
                    results = model.predict(frame, conf=conf2, iou=IOU2, classes=class2)
                # 可视化结果
                annotated_frame = results[0].plot()
                # 将带注释的帧写入视频文件
                out.write(annotated_frame)
            else:
                # 最后结尾中断视频帧循环
                break
        # 释放读取和写入对象
        cap.release()
        out.release()
        # 播放已经处理好的物体检测视频
        try:
            self.media_player2.setMedia(QMediaContent(QUrl("./video_output/" + file_name)))
            self.media_player2.play()
            print("看看预测好的file_path" + "./video_output/" + file_name)
        except Exception as e:
            print(e)

    # 播放/暂停
    def playPause2(self):
        if self.media_player2.state() == 1:
            self.media_player2.pause()
        else:
            self.media_player2.play()

    # 视频总时长获取
    def getDuration2(self, d):
        # d是获取到的视频总时长（ms）
        self.ui.slider2.setRange(0, d)
        self.ui.slider2.setEnabled(True)
        self.displayTime2(d)

    # 视频实时位置获取
    def getPosition2(self, p):
        self.ui.slider2.setValue(p)
        self.displayTime2(self.ui.slider2.maximum() - p)

    # 显示剩余时间
    def displayTime2(self, ms):
        minutes = int(ms / 60000)
        seconds = int((ms - minutes * 60000) / 1000)
        self.ui.time2.setText('{}:{}'.format(minutes, seconds))

    # 用进度条更新视频位置
    def updatePosition2(self, v):
        self.media_player2.setPosition(v)
        self.displayTime2(self.ui.slider2.maximum() - v)

    # -- tab3 track 点击事件回调函数 ---
    def chooseVideo3(self):
        try:
            # 拿到视频路径，存到track_path里，并在textBrowser中展示路径
            file_dialog = QFileDialog()
            file_path, _ = file_dialog.getOpenFileName(self, 'Open Video File', '', 'Videos (*.mp4 *.avi)')
            if file_path:
                # self.track_path = file_path
                print("file_path", file_path)
                # 展示路径
                self.track_path.setText(file_path)
        except Exception as e:
            print(e)

    # 播放/暂停
    def playPause3(self):
        if self.media_player3.state() == 1:
            self.media_player3.pause()
        else:
            self.media_player3.play()

    # 视频总时长获取
    def getDuration3(self, d):
        # d是获取到的视频总时长（ms）
        self.ui.slider3.setRange(0, d)
        self.ui.slider3.setEnabled(True)
        self.displayTime3(d)

    # 视频实时位置获取
    def getPosition3(self, p):
        self.ui.slider3.setValue(p)
        self.displayTime3(self.ui.slider3.maximum() - p)

    # 显示剩余时间
    def displayTime3(self, ms):
        minutes = int(ms / 60000)
        seconds = int((ms - minutes * 60000) / 1000)
        self.ui.time3.setText('{}:{}'.format(minutes, seconds))

    # 用进度条更新视频位置
    def updatePosition3(self, v):
        self.media_player3.setPosition(v)
        self.displayTime3(self.ui.slider3.maximum() - v)

    # 物体追踪，轨迹识别与绘制
    def showTrack(self):
        # 创建一个字典，记录位置信息，格式如下
        # id1 [{x1,y1}{x2,y2}...]
        # id2 [{x1,y1}{x2,y2}...]
        self.locations = {}
        # 先处理，得到结果视频
        if not self.track_path:
            return
        # 拿到用户输入的参数
        conf3 = self.conf3.value()
        conf3 = float("{:.2f}".format(conf3))
        # 看是否转换的格式符合要求
        print(conf3)
        IOU3 = self.IOU3.value()
        IOU3 = float("{:.2f}".format(IOU3))
        if self.class3.text() == '':
            class3 = -1
        else:
            class3 = int(self.class3.text())
        try:
            # 加载 YOLOv8 model
            model = YOLO('yolov8n.pt')
            # 或者加载自己训练好的模型
            # model = YOLO('E:\YOLOv8_物体分类检测\\train_object\\runs\detect\\train10\weights\\best.pt')
            # 实例分割模型
            # model = YOLO('yolov8n-seg.pt')
            # 拿到当前图片路径末尾的文件名
            file_name = os.path.basename(self.track_path.toPlainText())
            # Open the video file
            video_path = 'video/' + file_name
            print("视频路径：", video_path)
            cap = cv2.VideoCapture(video_path)
            # 存储追踪信息
            track_history = defaultdict(lambda: [])
            # 创建一个列表，用于存储每一帧的图像和跟踪结果
            video_frames = []
            # 创建一个字典，储存对应类别检测到的物体数量
            category_nums = {}
            # visited[] 数组记录track_id，防止重复计数
            visited = set()
            # flag标记
            flag = False
            # video frames 循环每一帧
            while cap.isOpened():
                # 读取一帧
                success, frame = cap.read()
                if success:
                    # 用户没有指定类别
                    if class3 == -1:
                        print("不指定类别")
                        # Run YOLOv8 tracking 模型
                        results = model.track(frame, persist=True, conf=conf3, iou=IOU3, show=False)
                    # 用户指定了类别
                    else:
                        print("指定类别")
                        # Run YOLOv8 tracking 模型
                        results = model.track(frame, persist=True, conf=conf3, iou=IOU3, classes=class3, show=False)
                    # 提取结果中的位置、类别信息
                    boxes = results[0].boxes.xywh.cpu()
                    classes = results[0].boxes.cls.cpu()
                    print("boxes:", boxes)
                    print("classes:", classes)
                    print("results[0].boxes.id:", results[0].boxes.id)
                    if results[0].boxes.id is not None:
                        track_ids = results[0].boxes.id.int().cpu().tolist()
                        # 绘制结果到框frame中
                        annotated_frame = results[0].plot()
                        # 拿到 boxes这个矩形框 和 track跟踪的IDs 以及 预测的类别
                        # 根据不同车不同锚框来绘制轨迹
                        for box, track_id, category in zip(boxes, track_ids, classes):
                            x, y, w, h = box
                            # 将位置信息存入字典里
                            if track_id not in self.locations:
                                self.locations[track_id] = []
                            self.locations[track_id].append({"x": float(x), "y": float(y), "c": int(category)})
                            # 将类别计数存到字典里
                            # 搞个标志 visited() 集合，如果track_id已经遍历过了，就将id放入visited里，做个标志
                            flag = True
                            for i in visited:
                                if track_id == i:
                                    flag = False
                                    break
                            if flag:
                                if int(category) in category_nums:
                                    category_nums[int(category)] += 1
                                else:
                                    category_nums[int(category)] = 1
                                print(category_nums)
                            visited.add(track_id)
                            track = track_history[track_id]  # 不同车对应不同track
                            track.append((float(x), float(y)))  # x, y 锚框中心点坐标
                            # 超过100帧前的轨迹段会消失
                            if len(track) > 150:
                                track.pop(0)  # 弹出队列最前面的元素
                            # 绘制交通轨迹
                            points = np.hstack(track).astype(np.int32).reshape((-1, 1, 2))
                            cv2.polylines(annotated_frame, [points], isClosed=False, color=(250, 170, 0), thickness=8)
                        # 将带有跟踪结果的帧添加到帧列表中
                        video_frames.append(annotated_frame)
                    else:
                        print("没有id（物体）也给我补帧，不要抽帧")
                        video_frames.append(frame)
                else:
                    # Break the 循环 if video 到达末尾
                    break
            # 获取视频帧的维度
            frame_width = int(cap.get(3))
            frame_height = int(cap.get(4))
            # 创建VideoWriter对象
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter("video_output/" + file_name, fourcc, 20.0,
                                  (frame_width, frame_height))
            # 遍历带轨迹的帧列表，合成一起组成视频并写入到目标视频中
            for frame in video_frames:
                # Write the annotated frame to the output video
                out.write(frame)
            # 释放摄像头流
            cap.release()
            # 关闭输出视频流
            out.release()
            # 词频加到self变全局，页面6会用到
            self.category_nums = category_nums
            print('category_nums：', self.category_nums)
            if hasattr(self, 'categoty_nums'):
                print('存在')
        except Exception as e:
            print(e)
        # 处理好后，展示轨迹视频
        try:
            self.media_player3.setMedia(QMediaContent(QUrl("./video_output/" + file_name)))
            self.media_player3.play()
            print("看看预测好的file_path" + "./video_output/" + file_name)
        except Exception as e:
            print(e)

    # 导出位置坐标对话框
    def export_location(self):
        file_path, _ = QFileDialog.getSaveFileName(self, 'Save Chart Data', '', 'Chart (*.xlsx *.csv)')
        if file_path:
            file_name = os.path.splitext(file_path)[0]
            print("文件名为:", file_name)
            file_extension = os.path.splitext(file_path)[1]
            print("文件后缀为:", file_extension)
            # 将数据导出为xlsx
            if file_extension == '.xlsx':
                # 创建一个空的DataFrame
                df = pd.DataFrame(columns=['Track ID', 'X', 'Y', 'Category'])
                # 遍历字典，并将嵌套位置信息展平后添加到DataFrame中
                for track_id, positions in self.locations.items():
                    for position in positions:
                        # 保留小数点后3位
                        X = round(position['x'], 3)
                        Y = round(position['y'], 3)
                        df = df._append({'Track ID': track_id, 'X': X, 'Y': Y, 'Category': position['c']},
                                        ignore_index=True)
                # 将DataFrame写入xlsx文件
                df.to_excel(file_path, index=False)
            # 将数据导出为csv
            else:
                # 将数据写入csv文件
                with open(file_path, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(['Track ID', 'X', 'Y', 'Category'])
                    for track_id, positions in self.locations.items():
                        for position in positions:
                            # 保留小数点后3位
                            X = round(position['x'], 3)
                            Y = round(position['y'], 3)
                            writer.writerow([track_id, X, Y, position['c']])
        else:
            print('用户取消了保存图片操作')
            return

    # --- tab4 count 点击事件回调函数 ---
    def chooseVideo4(self):
        try:
            # 拿到视频路径，存到track_path里，并在textBrowser中展示路径
            file_dialog = QFileDialog()
            file_path, _ = file_dialog.getOpenFileName(self, 'Open Video File', '', 'Videos (*.mp4 *.avi)')
            if file_path:
                # self.track_path = file_path
                print("file_path", file_path)
                # 展示路径
                self.count_path.setText(file_path)
        except Exception as e:
            print(e)

    # 播放/暂停
    def playPause4(self):
        if self.media_player4.state() == 1:
            self.media_player4.pause()
        else:
            self.media_player4.play()

    # 视频总时长获取
    def getDuration4(self, d):
        # d是获取到的视频总时长（ms）
        self.ui.slider4.setRange(0, d)
        self.ui.slider4.setEnabled(True)
        self.displayTime4(d)

    # 视频实时位置获取
    def getPosition4(self, p):
        self.ui.slider4.setValue(p)
        self.displayTime4(self.ui.slider4.maximum() - p)

    # 显示剩余时间
    def displayTime4(self, ms):
        minutes = int(ms / 60000)
        seconds = int((ms - minutes * 60000) / 1000)
        self.ui.time4.setText('{}:{}'.format(minutes, seconds))

    # 用进度条更新视频位置
    def updatePosition4(self, v):
        self.media_player4.setPosition(v)
        self.displayTime4(self.ui.slider4.maximum() - v)

    # 关键步骤 - 计数
    def showCount(self):
        # 先处理，得到结果视频
        if not self.count_path:
            return
        # 拿到用户输入的参数
        conf4 = self.conf4.value()
        conf4 = float("{:.2f}".format(conf4))
        IOU4 = self.IOU4.value()
        IOU4 = float("{:.2f}".format(IOU4))
        if self.class4.text() == '':
            class4 = -1
        else:
            class4 = int(self.class4.text())
        try:
            # 加载 YOLOv8 model
            model = YOLO('yolov8n.pt')
            # 实例分割模型
            # model = YOLO('yolov8n-seg.pt')
            # 拿到当前图片路径末尾的文件名
            file_name = os.path.basename(self.count_path.toPlainText())
            # Open the video file
            video_path = 'video/' + file_name
            cap = cv2.VideoCapture(video_path)
            # Store the track history
            track_history = defaultdict(lambda: [])
            # 创建一个列表，用于存储每一帧的图像和跟踪结果
            video_frames = []
            # 定义越线位置（示例，您需要根据实际情况调整）
            line_position = 600  # 纵坐标 y，表示线段的位置
            # 初始化越线计数器和记录已经越过线的车辆的集合
            crossed_line_count = 0
            crossed_vehicles = set()
            # 循环视频
            while cap.isOpened():
                # 读取一帧
                success, frame = cap.read()
                if success:
                    # 用户没有指定类别
                    if class4 == -1:
                        # Run YOLOv8 tracking 模型
                        results = model.track(frame, persist=True, conf=conf4, iou=IOU4, show=False)
                    # 用户指定了类别
                    else:
                        # Run YOLOv8 tracking 模型
                        results = model.track(frame, persist=True, conf=conf4, iou=IOU4, classes=class4, show=False)
                    # 拿到 boxes这个矩形框 和 track跟踪的IDs
                    boxes = results[0].boxes.xywh.cpu()
                    if results[0].boxes.id is not None:
                        track_ids = results[0].boxes.id.int().cpu().tolist()
                        # 绘制结果到框frame中
                        annotated_frame = results[0].plot()
                        # 根据不同车不同锚框来绘制轨迹
                        for box, track_id in zip(boxes, track_ids):
                            x, y, w, h = box
                            track = track_history[track_id]  # 不同车对应不同track
                            track.append((float(x), float(y)))  # x, y 锚框中心点坐标
                            # 超过100帧前的轨迹段会消失
                            if len(track) > 100:
                                track.pop(0)  # 弹出队列最前面的元素
                            # 绘制交通轨迹
                            points = np.hstack(track).astype(np.int32).reshape((-1, 1, 2))
                            cv2.polylines(annotated_frame, [points], isClosed=False, color=(250, 170, 0), thickness=8)
                            # 检查车辆的中心点是否超过了越线的位置，并且车辆没有被记录过
                            if y < line_position and track_id not in crossed_vehicles:
                                print(frame.shape[0] - line_position)
                                crossed_line_count += 1
                                crossed_vehicles.add(track_id)
                            # 查看crossed_line_count的状态
                            print(crossed_line_count)
                            # 绘制越线检测线
                            cv2.line(annotated_frame, (0, line_position),
                                     (frame.shape[1], line_position), (0, 255, 0),
                                     2)
                            # 在帧上绘制越线计数
                            cv2.putText(annotated_frame, f'Crossed line count: {crossed_line_count}',
                                        (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 2,
                                        (255, 200, 0), 3, cv2.LINE_AA)
                        # 查看annotated_frame格式
                        print(annotated_frame)
                        # 将带有跟踪结果的帧添加到帧列表中
                        video_frames.append(annotated_frame)
                else:
                    # Break the 循环 if video 到达末尾
                    break
            # 获取视频帧的维度
            frame_width = int(cap.get(3))
            frame_height = int(cap.get(4))
            # 创建VideoWriter对象
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter("video_output/" + file_name, fourcc, 20.0,
                                  (frame_width, frame_height))
            # 遍历带轨迹的帧列表，合成一起组成视频并写入到目标视频中
            for frame in video_frames:
                # Write the annotated frame to the output video
                out.write(frame)
            # 输出越线车辆的数量
            print("Crossed line count:", crossed_line_count)
            # 释放摄像头流
            cap.release()
            # 关闭输出视频流
            out.release()
        except Exception as e:
            print(e)
        # 处理好后，展示轨迹视频
        try:
            self.media_player4.setMedia(QMediaContent(QUrl("./video_output/" + file_name)))
            self.media_player4.play()
            print("看看预测好的file_path" + "./video_output/" + file_name)
        except Exception as e:
            print(e)

    # --- tab5 dataset ---
    def selectDataset(self):
        # 打开文件对话框，选择要读取的文件
        file_path, _ = QFileDialog.getOpenFileName(None, '选择要读取的文件', '.',
                                                   'Excel Files (*.xlsx *.xls);;CSV Files (*.csv)')
        if file_path:
            if file_path.endswith('.xlsx'):
                print("正在读取 Excel 文件，请稍候...")
                try:
                    xlsx_file = pd.ExcelFile(file_path)
                    self.df = pd.read_excel(xlsx_file)
                except Exception as e:
                    print(e)
                print("读取成功！")
            elif file_path.endswith('.csv'):
                # 读取 csv 文件
                print("正在读取 CSV 文件，请稍候...")
                self.df = pd.read_csv(file_path)
                print("读取成功！")
            try:
                # 设置表格的行数和列数并显示
                self.xlsx.setRowCount(self.df.shape[0])
                self.xlsx.setColumnCount(self.df.shape[1])
                self.show_row.setText(str(self.df.shape[0]))
                self.show_col.setText(str(self.df.shape[1]))
                # 设置列标签
                self.xlsx.setHorizontalHeaderLabels(self.df.columns.tolist())
                # 填充表格
                for i in range(self.df.shape[0]):
                    for j in range(self.df.shape[1]):
                        item = QTableWidgetItem(str(self.df.iloc[i, j]))
                        self.xlsx.setItem(i, j, item)
            except Exception as e:
                print("请输入有效的数据集！", e)
        else:
            print('用户取消了数据集选择操作')
            return

    def drawChart5(self):
        # 拿到用户输入id，如果没输入就MessageBox提示
        if self.input_id.text() == '':
            print("请输入想要绘制轨迹的物体id")
            dialog = QMessageBox()
            dialog.setWindowTitle('warning')
            dialog.setIcon(QMessageBox.Warning)
            dialog.setText('请先输入想要绘制轨迹的物体id')
            dialog.exec_()
            return
        # 输入后还要判断输入是否合法
        try:
            myinput = int(self.input_id.text())
        except ValueError:
            # 如果用户输入的不是整数，显示一个错误提示框
            QMessageBox.warning(self, 'error', '请输入有效的整数', QMessageBox.Ok)
            return
        print(self.df)
        print(myinput)
        # 查询所有的行数据，根据id筛选出符合条件的行
        try:
            print(self.df['Track ID'] == myinput)
            data = self.df[self.df['Track ID'] == myinput]
            data = data.reset_index(drop=True)
        except Exception as e:
            print(e)
        # 选择x,y两列数据绘制散点图
        print("正在画了...")
        # 位置图
        try:
            self.figure5 = Figure(figsize=(5, 4))
            self.myax = self.figure5.add_subplot(111)
            self.canvas = FigureCanvas(self.figure5)
            x = data['X']
            y = data['Y']
            print(x)
            self.myax.set_title('location x and y')
            self.myax.scatter(x, y, c='green')
            self.canvas.draw()
            scene = QGraphicsScene(self)
            scene.addWidget(self.canvas)
            self.chart5.setScene(scene)
            # 再把类别图也显示出来
            scene = QGraphicsScene()
            print(data['Category'])
            img = QPixmap(f"image/{data['Category'][0]}.png")
            img = img.scaled(250, 250)
            scene.addPixmap(img)
            self.show_image5.setScene(scene)
        except Exception as e:
            print(e)

    # 导出位置图表
    def export_chart5(self):
        # 拿到想要导出的路径
        file_path, _ = QFileDialog.getSaveFileName(self, 'Save Chart Image', '', 'Images (*.png *.jpg *.bmp)')
        if file_path:
            # 保存为图片
            self.figure5.savefig(file_path)
            # 提示用户
            try:
                dialog = QMessageBox()
                dialog.setWindowTitle('success')
                dialog.setIcon(QMessageBox.Information)
                dialog.setText('导出成功！')
                dialog.exec_()
            except Exception as e:
                print(e)
        else:
            print('用户取消了保存图片操作')
            return

    # --- tab 6 ---
    # 保存热力图
    def export_chart6_1(self):
        # 保存热力图
        pixmap = QPixmap()
        # 获取图表的截图
        pixmap = self.hotmap.grab()
        # 拿到想要导出的路径
        file_path, _ = QFileDialog.getSaveFileName(self, 'Save Chart Image', '', 'Images (*.png *.jpg *.bmp)')
        if file_path:
            # 保存为图片
            pixmap.save(file_path)  # 保存图表
            # 提示用户
            try:
                dialog = QMessageBox()
                dialog.setWindowTitle('success')
                dialog.setIcon(QMessageBox.Information)
                dialog.setText('导出成功！')
                dialog.exec_()
            except Exception as e:
                print(e)
        else:
            print('用户取消了保存图片操作')
            return

    # 保存类别词频图
    def export_chart6_2(self):
        # 拿到想要导出的路径
        file_path, _ = QFileDialog.getSaveFileName(self, 'Save Chart Image', '', 'Images (*.png *.jpg *.bmp)')
        if file_path:
            # 保存为图片
            self.figure6_2.savefig(file_path)
            # 提示用户
            try:
                dialog = QMessageBox()
                dialog.setWindowTitle('success')
                dialog.setIcon(QMessageBox.Information)
                dialog.setText('导出成功！')
                dialog.exec_()
            except Exception as e:
                print(e)
        else:
            print('用户取消了保存图片操作')
            return

    # 退出函数
    def myexit(self):
        exit()


if __name__ == "__main__":
    # 创建应用程序对象
    app = QApplication(sys.argv)
    # 创建自定义的窗口MyWindow对象，初始化相关属性和方法
    win = MyWindow()
    # 显示图形界面
    win.ui.show()
    # 启动应用程序的事件循环，可不断见监听点击事件等
    app.exec()
