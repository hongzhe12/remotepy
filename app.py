import pyautogui
from flask import Flask, render_template, Response, request
import io
import time

app = Flask(__name__)

# 配置
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
FRAME_RATE = 10  # 帧率


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
        pyautogui.click(x, y)
        return "success"
    except Exception as e:
        return str(e), 500


def gen():
    while True:
        start_time = time.time()

        # 截图
        screenShotImg = pyautogui.screenshot()

        # 转换为字节流
        imgByteArr = io.BytesIO()
        screenShotImg.save(imgByteArr, format='JPEG', quality=85)  # 调整质量
        imgByteArr = imgByteArr.getvalue()

        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + imgByteArr + b'\r\n')

        # 控制帧率
        elapsed_time = time.time() - start_time
        time.sleep(max(0, 1 / FRAME_RATE - elapsed_time))


@app.route('/video_feed')
def video_feed():
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    app.run(threaded=True, host='0.0.0.0', port=5000)