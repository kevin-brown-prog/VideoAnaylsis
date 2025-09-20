import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QFileDialog, QSizePolicy, QScrollArea
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt
import cv2

class VideoPanel(QWidget):
    def enable_stride_mode(self):
        self.stride_mode = True
        self.points = []
       
        self.update()

    def wheelEvent(self, event):
        # Zoom with scroll wheel
        zoom_in = event.angleDelta().y() > 0
        zoom_factor = 1.25 if zoom_in else 0.8
        self.zoom_factor *= zoom_factor
        
        # Limit zoom range
        self.zoom_factor = max(0.1, min(5.0, self.zoom_factor))
        
        if self.original_pixmap:
            self.update_zoom()

    def update_zoom(self):
        if self.original_pixmap:
            scaled_pixmap = self.original_pixmap.scaled(
                self.original_pixmap.size() * self.zoom_factor,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)
            self.image_label.resize(scaled_pixmap.size())

    def mousePressEvent(self, event):
        if hasattr(self, 'stride_mode') and self.stride_mode:
            if event.button() == Qt.LeftButton:
                if self.cap and hasattr(self, 'original_pixmap') and self.original_pixmap:
                    # Get mouse position relative to the scroll area
                    scroll_pos = self.scroll_area.mapFromParent(event.pos())
                    
                    # Get position relative to the image label within scroll area
                    label_pos = self.image_label.mapFromParent(scroll_pos)
                    
                    x = label_pos.x()
                    y = label_pos.y()
                    
                    # Get the current displayed pixmap size (with zoom)
                    current_pixmap = self.image_label.pixmap()
                    if current_pixmap:
                        display_w = current_pixmap.width()
                        display_h = current_pixmap.height()
                        
                        # Get original image dimensions
                        orig_w = self.original_pixmap.width()
                        orig_h = self.original_pixmap.height()
                        
                        # Convert from display coordinates to original image coordinates
                        scale_x = orig_w / display_w
                        scale_y = orig_h / display_h
                        
                        orig_x = int(x * scale_x)
                        orig_y = int(y * scale_y)
                        
                        print(f"Click at display ({x}, {y}) -> original ({orig_x}, {orig_y})")
                        
                        self.points.append((orig_x, orig_y))
                        if len(self.points) == 2:
                            self.stride_mode = False
                            self.draw_stride_lines()
        super().mousePressEvent(event)

    def draw_stride_lines(self):
        if len(self.points) == 2:
            # Get frame
            frame_num = self.frame_pos
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            ret, frame = self.cap.read()
            if ret:
               
                # ...existing code...
                fps = self.cap.get(cv2.CAP_PROP_FPS)
                timestamp = (frame_num - self.sync_frame) / fps if fps else 0
                text = f"{timestamp:.2f} sec"
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 1.0
                color = (255, 0, 0)
                thickness = 2
                position = (10, 40)
                frame = cv2.putText(frame, text, position, font, font_scale, color, thickness, cv2.LINE_AA)
                (x1, y1), (x2, y2) = self.points
                frame = cv2.line(frame, (x1, y1), (x1, y2), (0, 255, 0), 3)
                length = abs(y2 - y1)
                frame = cv2.line(frame, (x1, y1), (x1 + length, y1), (0, 255, 0), 3)
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb.shape
                bytes_per_line = ch * w
                qt_img = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(qt_img)
                self.original_pixmap = pixmap
                self.update_zoom()
    def __init__(self, label_text):
        super().__init__()
        self.layout = QVBoxLayout()
        
        # Create scroll area for zoom functionality
        self.scroll_area = QScrollArea()
        self.image_label = QLabel()
        self.scroll_area.setWidget(self.image_label)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignCenter)
        
        self.layout.addWidget(self.scroll_area)
        self.setLayout(self.layout)
        self.cap = None
        self.frame_pos = 0
        self.total_frames = 0
        self.sync_frame = 0
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.zoom_factor = 1.0
        self.original_pixmap = None

    def load_video(self, path):
        self.cap = cv2.VideoCapture(path)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.frame_pos = 0
        self.show_frame(0)
        self.last_path = path

    def show_frame(self, frame_num):
        if self.cap:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            ret, frame = self.cap.read()
            if ret:
                # Compute timestamp in seconds, zeroed at sync_frame
                fps = self.cap.get(cv2.CAP_PROP_FPS)
                timestamp = (frame_num - self.sync_frame) / fps if fps else 0
                text = f"{timestamp:.2f} sec"
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 1.0
                color = (255, 0, 0)
                thickness = 2
                position = (10, 40)
                frame = cv2.putText(frame, text, position, font, font_scale, color, thickness, cv2.LINE_AA)
                # Draw stride lines if available
                if hasattr(self, 'points') and len(self.points) == 2:
                    (x1, y1), (x2, y2) = self.points
                    frame = cv2.line(frame, (x1, y1), (x1, y2), (0, 255, 0), 3)
                    length = abs(y2 - y1)
                    frame = cv2.line(frame, (x1, y1), (x1 + length, y1), (0, 255, 0), 3)
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb.shape
                bytes_per_line = ch * w
                qt_img = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(qt_img)
                self.original_pixmap = pixmap
                self.update_zoom()
                self.frame_pos = frame_num

class MainWindow(QMainWindow):
    def draw_stride_lines(self):
        self.left_panel.enable_stride_mode()
    def save_jack_file(self):
        path, _ = QFileDialog.getSaveFileName(self, 'Save .jack File', filter='Jack Files (*.jack)')
        if path:
            data = {
                'left_video': getattr(self.left_panel, 'last_path', ''),
                'right_video': getattr(self.right_panel, 'last_path', ''),
                'offset': self.frame_offset
            }
            import json
            with open(path, 'w') as f:
                json.dump(data, f)

    def load_jack_file(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Open .jack File', filter='Jack Files (*.jack)')
        if path:
            import json
            with open(path, 'r') as f:
                data = json.load(f)
            left_video = data.get('left_video', '')
            right_video = data.get('right_video', '')
            offset = data.get('offset', 0)
            if left_video:
                self.left_panel.load_video(left_video)
            if right_video:
                self.right_panel.load_video(right_video)
            self.frame_offset = offset
            self.sync = offset != 0
            self.left_panel.show_frame(self.left_panel.frame_pos)
            self.right_panel.show_frame(self.left_panel.frame_pos - self.frame_offset)
    def left_next_frame(self, ctrl=False):
        step = 10 if ctrl else 1
        new_frame = min(self.left_panel.total_frames - 1, self.left_panel.frame_pos + step)
        self.left_panel.show_frame(new_frame)
        if self.sync:
            self.right_panel.show_frame(min(self.right_panel.total_frames - 1, new_frame - self.frame_offset))

    def left_prev_frame(self, ctrl=False):
        step = 10 if ctrl else 1
        new_frame = max(0, self.left_panel.frame_pos - step)
        self.left_panel.show_frame(new_frame)
        if self.sync:
            self.right_panel.show_frame(max(0, new_frame - self.frame_offset))
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Baseball Pitcher Video Analysis')
        self.left_panel = VideoPanel('Pitcher 1')
        self.right_panel = VideoPanel('Pitcher 2')
        self.sync = False
        self.frame_offset = 0
        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        video_layout = QHBoxLayout()
        video_layout.addWidget(self.left_panel)
        video_layout.addWidget(self.right_panel)
        main_layout.addLayout(video_layout)

        controls_layout = QHBoxLayout()
        load_left_btn = QPushButton('Load Pitcher 1 Video')
        load_right_btn = QPushButton('Load Pitcher 2 Video')
        left_prev_btn = QPushButton('Left Previous Frame')
        left_next_btn = QPushButton('Left Next Frame')
        right_prev_btn = QPushButton('Right Previous Frame')
        right_next_btn = QPushButton('Right Next Frame')
        sync_btn = QPushButton('Sync (Compute Offset)')
        save_jack_btn = QPushButton('Save .jack')
        load_jack_btn = QPushButton('Load .jack')
        draw_stride_btn = QPushButton('Draw Stride Lines')

        controls_layout.addWidget(load_left_btn)
        controls_layout.addWidget(load_right_btn)
        controls_layout.addWidget(left_prev_btn)
        controls_layout.addWidget(left_next_btn)
        controls_layout.addWidget(right_prev_btn)
        controls_layout.addWidget(right_next_btn)
        controls_layout.addWidget(sync_btn)
        controls_layout.addWidget(save_jack_btn)
        controls_layout.addWidget(load_jack_btn)
        controls_layout.addWidget(draw_stride_btn)
        main_layout.addLayout(controls_layout)

        load_left_btn.clicked.connect(self.load_left_video)
        load_right_btn.clicked.connect(self.load_right_video)
        left_prev_btn.pressed.connect(lambda: self.left_prev_frame(ctrl=QApplication.keyboardModifiers() & Qt.ControlModifier))
        left_next_btn.pressed.connect(lambda: self.left_next_frame(ctrl=QApplication.keyboardModifiers() & Qt.ControlModifier))
        right_prev_btn.pressed.connect(lambda: self.right_prev_frame(ctrl=QApplication.keyboardModifiers() & Qt.ControlModifier))
        right_next_btn.pressed.connect(lambda: self.right_next_frame(ctrl=QApplication.keyboardModifiers() & Qt.ControlModifier))
        sync_btn.clicked.connect(self.compute_sync_offset)
        save_jack_btn.clicked.connect(self.save_jack_file)
        load_jack_btn.clicked.connect(self.load_jack_file)
        draw_stride_btn.clicked.connect(self.draw_stride_lines)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    def load_left_video(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Open Pitcher 1 Video')
        if path:
            self.left_panel.load_video(path)

    def load_right_video(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Open Pitcher 2 Video')
        if path:
            self.right_panel.load_video(path)
        load_left_btn = QPushButton('Load Pitcher 1 Video')
        load_right_btn = QPushButton('Load Pitcher 2 Video')
        left_prev_btn = QPushButton('Left Previous Frame')
        left_next_btn = QPushButton('Left Next Frame')
        right_prev_btn = QPushButton('Right Previous Frame')
        right_next_btn = QPushButton('Right Next Frame')
        sync_btn = QPushButton('Sync (Compute Offset)')
        self.left_panel.show_frame(min(self.left_panel.total_frames - 1, self.left_panel.frame_pos + 1))
        if self.sync:
            self.right_panel.show_frame(min(self.right_panel.total_frames - 1, self.left_panel.frame_pos - self.frame_offset))

    def right_prev_frame(self, ctrl=False):
        step = 10 if ctrl else 1
        new_frame = max(0, self.right_panel.frame_pos - step)
        self.right_panel.show_frame(new_frame)
        if self.sync:
            self.left_panel.show_frame(max(0, new_frame + self.frame_offset))

    def right_next_frame(self, ctrl=False):
        step = 10 if ctrl else 1
        new_frame = min(self.right_panel.total_frames - 1, self.right_panel.frame_pos + step)
        self.right_panel.show_frame(new_frame)
        if self.sync:
            self.left_panel.show_frame(min(self.left_panel.total_frames - 1, new_frame + self.frame_offset))

    def compute_sync_offset(self):
        # Compute offset between current left and right frame
        self.frame_offset = self.left_panel.frame_pos - self.right_panel.frame_pos
        self.sync = True
        # Set sync_frame for both panels
        self.left_panel.sync_frame = self.left_panel.frame_pos
        self.right_panel.sync_frame = self.right_panel.frame_pos
        # Show synced frames
        self.left_panel.show_frame(self.left_panel.frame_pos)
        self.right_panel.show_frame(self.left_panel.frame_pos - self.frame_offset)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
