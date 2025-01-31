from flask import Flask, render_template, Response, request
import io
import time
import mss
import mss.tools
from PIL import Image

app = Flask(__name__)

# 配置
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
INITIAL_FRAME_RATE = 10  # 初始帧率
MIN_FRAME_RATE = 10       # 最小帧率
MAX_FRAME_RATE = 30      # 最大帧率
FRAME_RATE = INITIAL_FRAME_RATE  # 当前帧率

import threading

# 创建线程局部存储
thread_local = threading.local()

def get_mss_instance():
    if not hasattr(thread_local, "mss_instance"):
        thread_local.mss_instance = mss.mss()
    return thread_local.mss_instance

def gen():
    global FRAME_RATE
    monitor = {"top": 0, "left": 0, "width": SCREEN_WIDTH, "height": SCREEN_HEIGHT}

    while True:
        try:
            start_time = time.time()

            # 获取当前线程的 mss 实例
            sct = get_mss_instance()

            # 使用 mss 截图
            sct_img = sct.grab(monitor)

            # 将 mss 截图转换为 PIL 图像
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

            # 转换为字节流
            imgByteArr = io.BytesIO()
            img.save(imgByteArr, format='JPEG', quality=75)  # 适当降低质量以提高性能
            imgByteArr = imgByteArr.getvalue()

            # 生成视频帧
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + imgByteArr + b'\r\n')

            # 计算本次帧的处理时间
            elapsed_time = time.time() - start_time

            # 动态调整帧率
            if elapsed_time > 1 / FRAME_RATE:
                # 如果处理时间超过当前帧率的间隔，降低帧率
                FRAME_RATE = max(MIN_FRAME_RATE, FRAME_RATE - 5)  # 降低帧率幅度增大
            else:
                # 如果处理时间较短，尝试提高帧率
                FRAME_RATE = min(MAX_FRAME_RATE, FRAME_RATE + 1)

            # 控制帧率
            sleep_time = max(0, 1 / FRAME_RATE - elapsed_time)
            time.sleep(sleep_time)

        except Exception as e:
            print(f"Error in gen(): {e}")
            time.sleep(0.1)  # 防止频繁出错，减少 sleep 时间


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/pointer')
def pointer():
    try:
        xrate = float(request.args.get("xrate", 0))
        yrate = float(request.args.get("yrate", 0))

        # 验证输入
        if not (0 <= xrate <= 1 and 0 <= yrate <= 1):
            return "Invalid input", 400

        x = int(xrate * SCREEN_WIDTH)
        y = int(yrate * SCREEN_HEIGHT)

        # 执行点击操作
        import pyautogui
        pyautogui.click(x, y)
        return "success"
    except Exception as e:
        return str(e), 500


@app.route('/adjust_frame_rate')
def adjust_frame_rate():
    global FRAME_RATE
    latency = float(request.args.get("latency", 0))
    if latency > 200:  # 如果延迟大于200ms，降低帧率
        FRAME_RATE = max(MIN_FRAME_RATE, FRAME_RATE - 5)  # 降低帧率幅度增大
    else:
        FRAME_RATE = min(MAX_FRAME_RATE, FRAME_RATE + 1)
    return {"frameRate": FRAME_RATE}  # 返回帧率信息


@app.route('/ping')
def ping():
    return "pong"


@app.route('/video_feed')
def video_feed():
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    app.run(threaded=True, host='0.0.0.0', port=5000)