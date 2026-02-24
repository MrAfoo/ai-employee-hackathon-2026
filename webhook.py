from flask import Flask, request

app = Flask(__name__)
VERIFY_TOKEN = "myhackathonverifytoken"

@app.route("/webhook/whatsapp", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200
        else:
            return "Forbidden", 403
    else:
        print(request.json)  # log incoming messages
        return "Event received", 200

if __name__ == "__main__":
    app.run(port=3000)
