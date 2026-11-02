"""Play with RoboArm in a browser. The physics and rendering run on this machine.

    python play_web.py            then open http://localhost:8765
    MUJOCO_GL=egl is used so it works over SSH with no display.

Over SSH, forward the port from your own computer:
    ssh -L 8765:localhost:8765 <user>@<this machine>
"""
import io
import json
import math
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

os.environ.setdefault('MUJOCO_GL', 'egl')
import mujoco  # noqa: E402
from PIL import Image  # noqa: E402

HERE = Path(__file__).parent
HOST = os.environ.get('ROBOARM_HOST', '127.0.0.1')   # set to a VPN address to share it there
PORT = 8765
WIDTH, HEIGHT = 960, 640
HOME = [0, 15, 0, 0, 0, 50]            # degrees, gripper opening in mm
JOINTS = [
    ('J1 base', -167, 167, '°'),
    ('J2 shoulder', -35, 90, '°'),
    ('J3 elbow', -80, 80, '°'),
    ('J4 wrist', -110, 110, '°'),
    ('J5 twist', -145, 145, '°'),
    ('J6 gripper', 0, 50, ' mm'),
]


class Sim:
    def __init__(self):
        self.lock = threading.Lock()
        self.frame = b''
        self.seq = 0
        self.state = {}
        self.target = list(HOME)
        self.reset_flag = False
        self.cam = dict(azimuth=135.0, elevation=-22.0, distance=1.25)

    def ctrl(self, d):
        for i, v in enumerate(self.target[:5]):
            goal = math.radians(v)
            step = math.radians(90) * 1 / 500       # slew limit, like the stepper planner
            d.ctrl[i] += max(-step, min(step, goal - d.ctrl[i]))
        d.ctrl[5] = self.target[5] / 2000           # mm of opening to metres per finger

    def run(self):
        m = mujoco.MjModel.from_xml_path(str(HERE / 'roboarm.xml'))
        d = mujoco.MjData(m)
        renderer = mujoco.Renderer(m, HEIGHT, WIDTH)
        cam = mujoco.MjvCamera()
        cam.lookat[:] = (0.1, 0, 0.2)

        def start():
            mujoco.mj_resetData(m, d)
            d.ctrl[1] = math.radians(HOME[1])
            d.ctrl[5] = HOME[5] / 2000
            d.joint('j2').qpos[0] = d.ctrl[1]
            d.joint('j6_a').qpos[0] = d.joint('j6_b').qpos[0] = d.ctrl[5]
            mujoco.mj_forward(m, d)

        start()
        while True:
            t0 = time.time()
            with self.lock:
                if self.reset_flag:
                    self.reset_flag = False
                    self.target = list(HOME)
                    start()
                for _ in range(16):
                    self.ctrl(d)
                    mujoco.mj_step(m, d)
                cam.azimuth, cam.elevation, cam.distance = self.cam['azimuth'], self.cam['elevation'], self.cam['distance']
            renderer.update_scene(d, cam)
            buf = io.BytesIO()
            Image.fromarray(renderer.render()).save(buf, 'JPEG', quality=80)
            limits = [float(x) for x in m.actuator_forcerange[:, 1]]
            force = [float(x) for x in d.actuator_force]
            tool = d.site('tool').xpos
            low = min(float(d.geom(n).xpos[2]) for n in ('finger_a', 'finger_b', 'palm'))
            state = dict(
                load=[round(abs(f) / l, 2) for f, l in zip(force, limits)],
                torque=[round(f, 2) for f in force],
                tool=[round(float(v) * 1000) for v in tool],
                low=round(low * 1000),
            )
            with self.lock:
                self.frame = buf.getvalue()
                self.seq += 1
                self.state = state
            time.sleep(max(0, 1 / 30 - (time.time() - t0)))


SIM = Sim()

PAGE = '''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>RoboArm simulator</title>
<meta name="viewport" content="width=device-width, initial-scale=1"><style>
body{margin:0;background:#F3F5F7;color:#16202A;font-family:system-ui,sans-serif;display:flex;flex-wrap:wrap;min-height:100vh}
main{flex:999 1 500px;min-width:0;display:flex;align-items:center;justify-content:center}
img{max-width:100%;cursor:grab;user-select:none;touch-action:none}
aside{flex:1 1 300px;box-sizing:border-box;padding:18px;background:#fff;border-left:1px solid #C9D2DB;display:flex;flex-direction:column;gap:8px}
h1{font-size:22px;margin:0}p{margin:0;font-size:14px;line-height:20px;color:#4A5763}
label{display:flex;justify-content:space-between;font-size:15px;font-weight:600}
input{width:100%;height:30px}.bar{height:6px;background:#E3E8ED;border-radius:3px;overflow:hidden}.bar div{height:100%;background:#1F6FEB;width:0}
button{height:44px;font:inherit;font-weight:600;background:#fff;border:1px solid #7D8A96;border-radius:8px;cursor:pointer;flex:1}
.row{display:flex;gap:8px}</style></head><body>
<main><img id="v" src="/stream" alt="RoboArm simulation" draggable="false"></main>
<aside><h1>RoboArm simulator</h1><p>Move the sliders. Drag the picture to look around, scroll to zoom. The bar under each joint shows how hard its motor is working.</p>
<div id="s"></div><div class="row"><button id="r">Reset</button><button id="p">Over the cube</button></div>
<p id="i"></p></aside>
<script>
const J=__JOINTS__,H=__HOME__,s=document.getElementById('s'),ins=[],bars=[];
J.forEach((j,n)=>{const w=document.createElement('div');w.innerHTML=`<label for="j${n}"><span>${j[0]}</span><span id="t${n}"></span></label><input id="j${n}" type="range" min="${j[1]}" max="${j[2]}" value="${H[n]}"><div class="bar"><div id="b${n}"></div></div>`;s.appendChild(w);
const i=w.querySelector('input');ins.push(i);const t=w.querySelector('#t'+n);bars.push(w.querySelector('#b'+n));const up=()=>t.textContent=i.value+j[3];up();
i.oninput=()=>{up();fetch(`/set?i=${n}&v=${i.value}`)}});
const put=a=>a.forEach((v,n)=>{ins[n].value=v;ins[n].oninput()});
document.getElementById('r').onclick=()=>{fetch('/reset');H.forEach((v,n)=>{ins[n].value=v;document.getElementById('t'+n).textContent=v+J[n][3]})};
document.getElementById('p').onclick=()=>put([0,48,4,38,0,50]);
setInterval(async()=>{const d=await (await fetch('/state')).json();if(!d.load)return;d.load.forEach((l,n)=>{bars[n].style.width=Math.min(100,l*100)+'%';bars[n].style.background=l>=.98?'#D9580B':'#1F6FEB'});
document.getElementById('i').textContent=`Gripper at x ${d.tool[0]}, y ${d.tool[1]}, z ${d.tool[2]} mm`+(d.load.slice(0,5).some(l=>l>=.98)?'. A motor is at its limit.':'')},300);
const v=document.getElementById('v');let drag=null;
v.onpointerdown=e=>{drag=[e.clientX,e.clientY];v.setPointerCapture(e.pointerId)};v.onpointerup=()=>drag=null;
v.onpointermove=e=>{if(!drag)return;const dx=e.clientX-drag[0],dy=e.clientY-drag[1];drag=[e.clientX,e.clientY];fetch(`/cam?a=${-dx*.4}&e=${-dy*.4}&d=0`)};
v.onwheel=e=>{e.preventDefault();fetch(`/cam?a=0&e=0&d=${e.deltaY*.001}`)};
</script></body></html>'''


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def reply(self, body, kind='text/plain'):
        self.send_response(200)
        self.send_header('Content-Type', kind)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(url.query).items()}
        if url.path == '/':
            page = PAGE.replace('__JOINTS__', json.dumps(JOINTS)).replace('__HOME__', json.dumps(HOME))
            return self.reply(page.encode(), 'text/html; charset=utf-8')
        if url.path == '/stream':
            return self.stream()
        if url.path == '/state':
            with SIM.lock:
                return self.reply(json.dumps(SIM.state).encode(), 'application/json')
        if url.path == '/set':
            i, value = int(q['i']), float(q['v'])
            if 0 <= i < len(JOINTS):
                _, low, high, _ = JOINTS[i]
                with SIM.lock:
                    SIM.target[i] = max(low, min(high, value))
        elif url.path == '/reset':
            with SIM.lock:
                SIM.reset_flag = True
        elif url.path == '/cam':
            with SIM.lock:
                c = SIM.cam
                c['azimuth'] += float(q['a'])
                c['elevation'] = max(-89, min(-2, c['elevation'] + float(q['e'])))
                c['distance'] = max(0.4, min(3, c['distance'] + float(q['d'])))
        self.reply(b'ok')

    def stream(self):
        self.send_response(200)
        self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=f')
        self.end_headers()
        last = -1
        try:
            while True:
                with SIM.lock:
                    seq, frame = SIM.seq, SIM.frame
                if seq == last:
                    time.sleep(0.005)
                    continue
                last = seq
                self.wfile.write(b'--f\r\nContent-Type: image/jpeg\r\nContent-Length: %d\r\n\r\n' % len(frame) + frame + b'\r\n')
        except (BrokenPipeError, ConnectionResetError):
            pass


def main():
    threading.Thread(target=SIM.run, daemon=True).start()
    print(f'RoboArm simulator at http://{HOST}:{PORT}', flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()


if __name__ == '__main__':
    main()
