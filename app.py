import os
from flask import Flask, request, jsonify, send_from_directory, Response
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", "sqlite:///database.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ================= MODELS =================
class Poll(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(200))

class Option(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(100))
    poll_id = db.Column(db.Integer, db.ForeignKey('poll.id'))

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    option_id = db.Column(db.Integer, db.ForeignKey('option.id'))

# ================= SERVE FILES =================
@app.route("/")
def home():
    return send_from_directory(".", "index.html")

@app.route("/style.css")
def style():
    return send_from_directory(".", "style.css")

# ================= API =================
@app.route("/api/polls")
def get_polls():
    polls = Poll.query.all()
    return jsonify([{"id": p.id, "question": p.question} for p in polls])

@app.route("/api/create_poll", methods=["POST"])
def create_poll():
    data = request.json

    question = data.get("question", "").strip()

    if not question:
        return jsonify({"error": "Poll name required"}), 400

    poll = Poll(question=question)
    db.session.add(poll)
    db.session.commit()

    return jsonify({"id": poll.id})

@app.route("/api/add_option", methods=["POST"])
def add_option():
    data = request.json
    db.session.add(Option(text=data["text"], poll_id=data["poll_id"]))
    db.session.commit()
    return jsonify({"status": "ok"})

@app.route("/api/poll/<int:id>")
def poll(id):
    options = Option.query.filter_by(poll_id=id).all()
    result = []

    for opt in options:
        count = Vote.query.filter_by(option_id=opt.id).count()
        result.append({
            "id": opt.id,
            "text": opt.text,
            "votes": count
        })

    return jsonify(result)

@app.route("/api/vote", methods=["POST"])
def vote():
    data = request.json
    db.session.add(Vote(option_id=data["option_id"]))
    db.session.commit()
    return jsonify({"status": "ok"})

# ================= EXPORT =================
@app.route("/api/export/<int:id>")
def export(id):
    poll = Poll.query.get(id)
    options = Option.query.filter_by(poll_id=id).all()

    content = f"Poll: {poll.question}\n\n"

    for opt in options:
        count = Vote.query.filter_by(option_id=opt.id).count()
        content += f"{opt.text}: {count} votes\n"

    return Response(
        content,
        mimetype="text/plain",
        headers={"Content-Disposition": "attachment;filename=results.txt"}
    )

# ================= DELETE =================
@app.route("/api/delete/<int:id>", methods=["DELETE"])
def delete(id):
    options = Option.query.filter_by(poll_id=id).all()

    for o in options:
        Vote.query.filter_by(option_id=o.id).delete()

    Option.query.filter_by(poll_id=id).delete()
    Poll.query.filter_by(id=id).delete()
    db.session.commit()

    return jsonify({"status": "deleted"})

# ================== Save ================
@app.route("/api/save_poll_name", methods=["POST"])
def save_poll_name():
    data = request.json

    poll = Poll.query.get(data["poll_id"])

    if poll:
        # ✅ Just mark as saved using same question
        poll.saved_name = poll.question
        db.session.commit()

        return jsonify({"status": "saved"})

    return jsonify({"error": "Poll not found"}), 404


# ================= RUN =================
if __name__ == "__main__":
    with app.app_context():
        db.create_all()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(host="0.0.0.0", port=5000)