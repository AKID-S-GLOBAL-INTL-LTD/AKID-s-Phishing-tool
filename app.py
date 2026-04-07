#!/usr/bin/env python3
"""AKID Phishing Simulation Toolkit — AKID Global"""

from flask import Flask, render_template, request, jsonify, redirect, send_from_directory
import json, os, uuid, hashlib, re
from datetime import datetime
from urllib.parse import urlparse
import urllib.request

app = Flask(__name__)
app.secret_key = "akid-global-2024"

DATA_FILE   = "data/data.json"
CLONES_DIR  = "cloned_pages"
UPLOADS_DIR = "uploads/templates"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            return json.load(f)
    return {"campaigns": [], "templates": [], "events": []}

def save_data(d):
    os.makedirs("data", exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(d, f, indent=2)

def now():
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

def short_id():
    return uuid.uuid4().hex[:8]

def clone_page(url):
    parsed = urlparse(url)
    base   = f"{parsed.scheme}://{parsed.netloc}"
    headers = {"User-Agent": "Mozilla/5.0 (compatible; AKIDBot/1.0)"}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as r:
        html = r.read().decode("utf-8", errors="replace")
    inject = """
<script>
document.addEventListener('submit', function(e){
  var fd = new FormData(e.target), payload = {};
  fd.forEach(function(v,k){ payload[k]=v; });
  fetch('/track/submit',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({cid:window._AKID_CID||'',data:payload})}).catch(function(){});
},true);
</script>
<div style="position:fixed;bottom:0;left:0;right:0;z-index:999999;background:#0a0c10;
color:#00d4ff;font-family:monospace;font-size:11px;padding:6px 16px;display:flex;
align-items:center;gap:12px;border-top:1px solid #252d3d;">
<span style="background:#00d4ff;color:#000;padding:1px 6px;border-radius:3px;font-weight:700;">AKID SIM</span>
<span>Authorized phishing simulation by AKID Global. For testing purposes only.</span></div>"""
    html = re.sub(
        r'(src|href|action)=["\'](?!https?://|data:|javascript:|mailto:|#)(/[^"\']*)["\']',
        lambda m: f'{m.group(1)}="{base}{m.group(2)}"', html)
    html = re.sub(r'</body>', inject + "</body>", html, flags=re.IGNORECASE) if "</body>" in html.lower() else html + inject
    os.makedirs(CLONES_DIR, exist_ok=True)
    fname = short_id() + ".html"
    with open(os.path.join(CLONES_DIR, fname), "w", encoding="utf-8") as f:
        f.write(html)
    return fname

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/stats")
def api_stats():
    d = load_data()
    ev = d["events"]
    clicks  = [e for e in ev if e["type"] == "click"]
    opens   = [e for e in ev if e["type"] == "open"]
    submits = [e for e in ev if e["type"] == "submit"]
    campaigns = d["campaigns"]
    total_targets = sum(c.get("targets", 0) for c in campaigns)
    return jsonify({
        "campaigns": len(campaigns),
        "active":    sum(1 for c in campaigns if c["status"] == "active"),
        "opens":     len(opens),
        "clicks":    len(clicks),
        "submits":   len(submits),
        "open_rate": round(len(opens) / max(1, total_targets) * 100, 1),
        "click_rate":round(len(clicks) / max(1, len(opens)) * 100, 1) if opens else 0,
        "submit_rate":round(len(submits) / max(1, len(clicks)) * 100, 1) if clicks else 0,
    })

@app.route("/api/campaigns", methods=["GET"])
def get_campaigns():
    return jsonify(load_data()["campaigns"])

@app.route("/api/campaigns", methods=["POST"])
def create_campaign():
    d = load_data()
    body = request.json
    cid  = short_id()
    c = {"id": cid, "name": body.get("name","Unnamed"), "target_domain": body.get("target_domain",""),
         "template": body.get("template",""), "clone_file": body.get("clone_file",""),
         "targets": int(body.get("targets", 0)), "status": "draft",
         "created": now(), "track_url": f"/sim/{cid}"}
    d["campaigns"].append(c)
    save_data(d)
    return jsonify(c), 201

@app.route("/api/campaigns/<cid>/status", methods=["PATCH"])
def update_status(cid):
    d = load_data()
    for c in d["campaigns"]:
        if c["id"] == cid:
            c["status"] = request.json.get("status", c["status"])
            save_data(d)
            return jsonify(c)
    return jsonify({"error": "not found"}), 404

@app.route("/api/campaigns/<cid>", methods=["DELETE"])
def delete_campaign(cid):
    d = load_data()
    d["campaigns"] = [c for c in d["campaigns"] if c["id"] != cid]
    save_data(d)
    return jsonify({"ok": True})

@app.route("/api/templates", methods=["GET"])
def get_templates():
    return jsonify(load_data()["templates"])

@app.route("/api/templates", methods=["POST"])
def create_template():
    d = load_data()
    body = request.json
    t = {"id": short_id(), "name": body.get("name","Unnamed"), "subject": body.get("subject",""),
         "body": body.get("body",""), "created": now()}
    d["templates"].append(t)
    save_data(d)
    return jsonify(t), 201

@app.route("/api/templates/<tid>", methods=["DELETE"])
def delete_template(tid):
    d = load_data()
    d["templates"] = [t for t in d["templates"] if t["id"] != tid]
    save_data(d)
    return jsonify({"ok": True})

@app.route("/api/templates/upload", methods=["POST"])
def upload_template():
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "no file"}), 400
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    fname = short_id() + "_" + f.filename
    fpath = os.path.join(UPLOADS_DIR, fname)
    f.save(fpath)
    content = open(fpath, encoding="utf-8", errors="replace").read()
    d = load_data()
    t = {"id": short_id(), "name": f.filename, "subject": "(from file)", "body": content, "created": now()}
    d["templates"].append(t)
    save_data(d)
    return jsonify(t), 201

@app.route("/api/clone", methods=["POST"])
def api_clone():
    url = (request.json or {}).get("url", "").strip()
    if not url.startswith("http"):
        return jsonify({"error": "Invalid URL — must start with http/https"}), 400
    try:
        fname = clone_page(url)
        return jsonify({"file": fname, "preview": f"/clones/{fname}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/clones/<fname>")
def serve_clone(fname):
    return send_from_directory(CLONES_DIR, fname)

@app.route("/sim/<cid>")
def sim_link(cid):
    d = load_data()
    campaign = next((c for c in d["campaigns"] if c["id"] == cid), None)
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    d["events"].append({"id": short_id(), "cid": cid, "type": "click",
        "ip": hashlib.md5(ip.encode()).hexdigest()[:8],
        "ua": request.user_agent.string[:80], "ts": now()})
    save_data(d)
    if campaign and campaign.get("clone_file"):
        return redirect(f"/clones/{campaign['clone_file']}")
    return "<h2 style='font-family:monospace;padding:40px;color:#00d4ff;background:#0a0c10'>AKID SIM — Click tracked.</h2>"

@app.route("/track/submit", methods=["POST"])
def track_submit():
    body = request.json or {}
    d = load_data()
    d["events"].append({"id": short_id(), "cid": body.get("cid",""), "type": "submit",
        "fields": list(body.get("data",{}).keys()), "ts": now()})
    save_data(d)
    return jsonify({"ok": True})

@app.route("/api/events")
def get_events():
    d  = load_data()
    ev = d["events"]
    cid = request.args.get("cid")
    if cid:
        ev = [e for e in ev if e["cid"] == cid]
    return jsonify(list(reversed(ev[-300:])))

@app.route("/api/events/clear", methods=["POST"])
def clear_events():
    d = load_data()
    d["events"] = []
    save_data(d)
    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(debug=True, port=5050)
