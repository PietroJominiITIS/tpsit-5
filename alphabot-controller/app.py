from flask import Flask, render_template, request, Response
from alphabot import AlphaBot
from sys import argv
import cv2

app = Flask(__name__)

bot = AlphaBot()
bot.stop()

motion_map = dict(
    f=lambda: bot.forward(),
    b=lambda: bot.backward(),
    r=lambda: bot.right(),
    l=lambda: bot.left(),
    s=lambda: bot.stop()
)


@app.route('/motion', methods=['POST'])
def motion():
    d = request.args.get('d')
    d = request.form['d']
    if d in motion_map:
        motion_map[d]()
        return 'OK'
    return 'NOT OK'


def get_frame():
    camera = cv2.VideoCapture(int(argv[1]))
    while True:
        _, frame = camera.read()
        jpg_frame = cv2.imencode('.jpg', frame)[1]
        yield (b'--frame\r\nContent-Type: text/plain\r\n\r\n' +
               jpg_frame.tobytes() + b'\r\n')
    del(camera)


@app.route('/calc')
def calc():
    return Response(get_frame(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, threaded=True)
