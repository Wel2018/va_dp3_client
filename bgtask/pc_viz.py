import random
import threading
import numpy as np
from toolbox.qt import qtbase
from toolbox.core.file_op import yaml_load
from toolbox.cam3d.cam3d_base import Camera3DBase
from abc import abstractmethod, ABC


import sys
import numpy as np
import matplotlib
matplotlib.use('Qt5Agg')  # 使用Qt5作为matplotlib的后端
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas # type: ignore
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar # type: ignore
from matplotlib.widgets import Slider
from matplotlib.ticker import FixedLocator, FormatStrFormatter
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel)
from PySide6.QtCore import QTimer, Qt


from toolbox.cam3d.cam3d_base import Camera3DBase
from toolbox.robot.franka_arm_client import FrankaArmClient
from toolbox.cam3d.pointcloud_op import PointCloudProcessor
from toolbox.cam3d.pointcloud_op import PointCloudDownSampler
from toolbox.robot.unit_converter import Cam3dCoordTrans


class PointCloudCanvas(FigureCanvas):
    """点云绘制画布，负责点云的绘制与更新"""
    def __init__(self, parent=None, width=8, height=6, dpi=300):
        # 创建matplotlib图形和轴
        self.fig = plt.figure(figsize=(width, height), dpi=dpi)
        self.ax = self.fig.add_subplot(111, projection='3d')
        
        # 初始化散点对象（用于后续更新）
        self.scatter = None
        
        # 初始化坐标轴参数（与原函数保持一致）
        self.init_axes()
        
        super().__init__(self.fig)
        self.setParent(parent)
        self.setMinimumSize(600, 400)  # 设置最小尺寸


    def init_axes(self):
        """初始化坐标轴范围、刻度等参数"""
        # 设置坐标轴比例和范围
        self.ax.set_box_aspect([1.6, 2.2, 1]) # type: ignore
        self.ax.set_xlim(0.1, 0.8)
        self.ax.set_ylim(-0.3, 0.3)
        self.ax.set_zlim(0.0, 0.4) # type: ignore
        
        # 设置刻度
        x_ticks = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
        y_ticks = [-0.3, -0.2, -0.1, 0, 0.1, 0.2, 0.3]
        z_ticks = [0.1, 0.2, 0.3, 0.4]
        
        self.ax.tick_params(axis='both', which='major', labelsize=8)
        self.ax.xaxis.set_major_locator(FixedLocator(x_ticks))
        self.ax.yaxis.set_major_locator(FixedLocator(y_ticks))
        self.ax.zaxis.set_major_locator(FixedLocator(z_ticks)) # type: ignore
        
        # 设置刻度格式
        formatter = FormatStrFormatter('%.1f')
        self.ax.xaxis.set_major_formatter(formatter)
        self.ax.yaxis.set_major_formatter(formatter)
        self.ax.zaxis.set_major_formatter(formatter) # type: ignore


    def update_point_cloud(self, points, elev=30, azim=45):
        """更新点云数据并重新绘制
        
        Args:
            points (np.ndarray): (N, 6) 点云数组 (XYZRGB)
            elev (float, optional): 仰角，为None则保持当前视角
            azim (float, optional): 方位角，为None则保持当前视角
        """
        # 清除现有散点（如果存在）
        if self.scatter:
            self.scatter.remove()
        
        # 提取坐标和颜色
        xyz = points[:, :3]
        rgb = points[:, 3:] / 255.0  # RGB归一化到0-1范围
        
        # 绘制新散点
        self.scatter = self.ax.scatter(
            xyz[:, 0], xyz[:, 1], xyz[:, 2],
            c=rgb, marker='.', s=10  # 点大小与原函数一致 # type: ignore
        )
        
        # 更新视角（如果指定）
        if elev is not None and azim is not None:
            self.ax.view_init(elev=elev, azim=azim) # type: ignore
        
        # 刷新画布
        self.fig.canvas.draw_idle()


class PointCloudVizTask(qtbase.QAsyncTask):
    sig_data = qtbase.Signal(dict)
    
    def __init__(self, cfg: dict, cam: Camera3DBase):
        super().__init__(cfg)
        self.cam = cam
        self.down = PointCloudDownSampler()
        self.cam3d_trans = Cam3dCoordTrans(cam)
        self.pcp = PointCloudProcessor(self.down, self.cam3d_trans)
        
    def obs_process(self, points): # -> dict[Any, Any]:
        points = self.pcp.world(points)
        cfgpath = "/home/dell/code/phimate/.cache/pointcloud_op.yaml"
        group = "L515_crop"
        points = self.pcp.crop(points, cfgpath, group)
        # # print(f"crop by workspace = {pc.shape}")
        # pc = self.pcp.farthest_point_sampling(pc, use_cuda=1, num_points=4096)
        # points = self.pcp.down.random_downsample_to_N(pc, 1024)
        points = self.pcp.fps(points, use_cuda=1, num_points=1024)
        return points
    
    def run(self):
        # while 1:
        self.msleep(50)
        cam_data = self.cam._cam_data
        pc = cam_data['pointcloud']
        pc = self.obs_process(pc)
        self.sig_data.emit({
            "ret": 1,
            "pc": pc,
        })


class RealTimePointCloudViewer(QWidget):
    """实时点云可视化主窗口"""
    
    def __init__(self, cam: Camera3DBase):
        super().__init__()
        # self.setWindowTitle("实时点云可视化")
        self.setGeometry(100, 100, 1000, 800)  # 窗口位置和大小
        # self.task.start()
        self.cam = cam
        
        # 初始化点云数据（空数据）
        self.point_cloud_data = np.zeros((0, 6))  # (N, 6) 格式
        
        # 创建中心部件和布局
        self.main_layout = QVBoxLayout(self)
        
        # 添加点云画布和导航工具栏
        self.init_canvas()
        
        # 添加控制组件（按钮、视角调整等）
        # self.init_controls()
        
        # 初始化定时器（用于模拟实时数据更新）
        # self.timer = QTimer(self)
        # self.timer.timeout.connect(self.generate_random_point_cloud)  # 定时生成随机点云
        # self.is_updating = False  # 标记是否正在实时更新

    def init_canvas(self):
        """初始化点云绘制画布和导航工具栏"""
        # 创建点云画布
        self.canvas = PointCloudCanvas(self, width=8, height=6, dpi=100)
        
        # 添加matplotlib导航工具栏（支持旋转、缩放等交互）
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        # 将画布和工具栏添加到布局
        # self.main_layout.addWidget(self.toolbar)
        self.main_layout.addWidget(self.canvas)

    def init_controls(self):
        """初始化控制组件（按钮、状态显示等）"""
        # 创建控制区布局
        control_layout = QHBoxLayout()
        
        # 实时更新按钮
        self.start_btn = QPushButton("开始实时更新")
        self.start_btn.clicked.connect(self.toggle_real_time_update)
        control_layout.addWidget(self.start_btn)
        
        # 手动更新按钮
        self.update_btn = QPushButton("手动更新点云")
        self.update_btn.clicked.connect(self.generate_random_point_cloud)
        control_layout.addWidget(self.update_btn)
        
        # 状态标签
        self.status_label = QLabel("状态：就绪")
        control_layout.addWidget(self.status_label)
        
        # 添加控制区到主布局
        self.main_layout.addLayout(control_layout)

    def toggle_real_time_update(self):
        """切换实时更新状态（开始/停止）"""
        # if self.is_updating:
        #     # 停止实时更新
        #     self.timer.stop()
        #     self.start_btn.setText("开始实时更新")
        #     self.status_label.setText("状态：已停止")
        #     self.is_updating = False
        # else:
        #     # 开始实时更新（每500ms更新一次）
        #     self.timer.start(500)  # 500ms = 0.5秒
        #     self.start_btn.setText("停止实时更新")
        #     self.status_label.setText("状态：实时更新中...")
        #     self.is_updating = True
        ...

    def update_point_cloud_bg(self):
        self.task = PointCloudVizTask(cfg={}, cam=self.cam)
        self.task.sig_data.connect(self._update_point_cloud)
        self.task.start()
        
    def _update_point_cloud(self, data):
        self.canvas.update_point_cloud(data['pc'])
        
    def generate_random_point_cloud(self):
        """生成随机点云数据（模拟实时输入）"""
        # 生成随机点云 (N, 6)：XYZ在指定范围内，RGB随机
        num_points = 4000  # 点数量
        
        # XYZ范围与坐标轴范围匹配（确保点在可视范围内）
        x = np.random.uniform(0.1, 0.8, num_points)  # x在[0.1, 0.8]
        y = np.random.uniform(-0.3, 0.3, num_points)  # y在[-0.3, 0.3]
        z = np.random.uniform(0.0, 0.4, num_points)  # z在[0.0, 0.4]
        
        # RGB随机颜色（0-255）
        r = np.random.randint(0, 256, num_points)
        g = np.random.randint(0, 256, num_points)
        b = np.random.randint(0, 256, num_points)
        
        # 组合为(N, 6)数组
        self.point_cloud_data = np.column_stack((x, y, z, r, g, b))
        
        # 更新画布（随机调整视角增加动态效果）
        # random_elev = np.random.uniform(20, 40)  # 仰角在20-40度
        # random_azim = np.random.uniform(30, 60)  # 方位角在30-60度
        self.canvas.update_point_cloud(
            self.point_cloud_data,
            # elev=random_elev,
            # azim=random_azim
        )
