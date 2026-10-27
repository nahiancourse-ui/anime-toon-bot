# -*- coding: utf-8 -*-
"""
Messenger FAQ Bot - এনিমে ফ্যান ডাবিং টিমের জন্য
শুধু নিচের "সেটিংস" অংশ বদলালেই অন্য পেজের জন্যও ব্যবহার করা যাবে।

চালানোর আগে: pip install flask requests
Environment variable লাগবে: PAGE_ACCESS_TOKEN, VERIFY_TOKEN
"""
import os
import requests
from flask import Flask, request

# ===================== সেটিংস (এখানে বদলান) =====================
TEAM_NAME = "ANIME TOON BANGLA"

WELCOME = (
    f"আসসালামু আলাইকুম! {TEAM_NAME} পেজে স্বাগতম 😊\n"
    "নিচের বাটন থেকে বেছে নিন, অথবা আপনার প্রশ্ন লিখুন।"
)

# মেনু বাটন: (বাটনের লেখা - সর্বোচ্চ ২০ অক্ষর, কোড)
MENU = [
    ("নতুন ডাব / এপিসোড", "NEW"),
    ("কোথায় দেখব?", "WATCH"),
    ("টিমে জয়েন করুন", "JOIN"),
    ("ডাব রিকোয়েস্ট", "REQUEST"),
    ("যোগাযোগ", "CONTACT"),
]

# প্রতিটি কোডের উত্তর
ANSWERS = {
    "NEW": "নতুন এপিসোড সাধারণত প্রতি সপ্তাহে আসে। আপডেটের জন্য পেজ ফলো করে রাখুন এবং সি ফার্স্ট অপশন অন করুন।",
    "WATCH": "আমাদের ডাব দেখতে পারবেন আমাদের YouTube চ্যানেলে: [আপনার চ্যানেলের লিংক] এবং Facebook পেজের ভিডিও সেকশনে।",
    "JOIN": "আমরা ভয়েস আর্টিস্ট, এডিটর, স্ক্রিপ্ট রাইটার ও অনুবাদক খুঁজছি। আপনার ১ মিনিটের ভয়েস স্যাম্পল এবং নাম পাঠান, আমাদের টিম যোগাযোগ করবে।",
    "REQUEST": "কোন এনিমে ডাব চান তার নাম লিখে পাঠান। ভোট বেশি হলে আমরা বিবেচনা করব, তবে সব রিকোয়েস্ট পূরণের নিশ্চয়তা দিতে পারি না।",
    "CONTACT": "সরাসরি কথা বলতে চাইলে আপনার প্রশ্ন লিখে রাখুন, অ্যাডমিন সুবিধামতো সময়ে উত্তর দেবে।",
}

# কিওয়ার্ড দিয়ে অটো উত্তর (বাংলা ও ইংরেজি দুটোই দিন, ছোট হাতের অক্ষরে)
KEYWORDS = {
    "NEW": ["new", "episode", "ep", "নতুন", "এপিসোড", "কবে", "release", "upload"],
    "WATCH": ["watch", "link", "youtube", "কোথায়", "লিংক", "দেখব", "দেখা"],
    "JOIN": ["join", "voice", "artist", "জয়েন", "ভয়েস", "টিমে", "যোগ"],
    "REQUEST": ["request", "রিকোয়েস্ট", "dub korben", "ডাব করবেন", "চাই"],
    "CONTACT": ["admin", "contact", "যোগাযোগ", "অ্যাডমিন", "এডমিন"],
}

FALLBACK = "দুঃখিত, আমি এটা বুঝতে পারিনি 😅 নিচের মেনু থেকে বেছে নিন। অ্যাডমিন পরে আপনাকে উত্তর দেবে।"
# ================================================================

PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN", "")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "change_this_verify_token")
GRAPH_URL = "https://graph.facebook.com/v19.0/me/messages"

app = Flask(__name__)


def send(psid, text, with_menu=True):
    """ইউজারকে মেসেজ পাঠায়, চাইলে মেনু বাটনসহ।"""
    message = {"text": text}
    if with_menu:
        message["quick_replies"] = [
            {"content_type": "text", "title": title, "payload": code}
            for title, code in MENU
        ]
    payload = {"recipient": {"id": psid}, "messaging_type": "RESPONSE", "message": message}
    try:
        requests.post(
            GRAPH_URL,
            params={"access_token": PAGE_ACCESS_TOKEN},
            json=payload,
            timeout=10,
        )
    except requests.RequestException as e:
        print("Send error:", e)


def find_code(text):
    """মেসেজে কোন কিওয়ার্ড আছে খোঁজে।"""
    text = text.lower()
    for code, words in KEYWORDS.items():
        if any(w in text for w in words):
            return code
    return None


def handle_event(event):
    psid = event["sender"]["id"]

    # "Get Started" বাটন বা মেনু পোস্টব্যাক
    if "postback" in event:
        payload = event["postback"].get("payload", "")
        if payload == "GET_STARTED":
            send(psid, WELCOME)
        elif payload in ANSWERS:
            send(psid, ANSWERS[payload])
        return

    message = event.get("message")
    if not message or message.get("is_echo"):
        return

    # কুইক রিপ্লাই বাটনে চাপ দিলে
    qr = message.get("quick_reply")
    if qr and qr.get("payload") in ANSWERS:
        send(psid, ANSWERS[qr["payload"]])
        return

    text = message.get("text", "")
    if not text:
        send(psid, "ধন্যবাদ! আপনার মেসেজ পেয়েছি, অ্যাডমিন দেখে উত্তর দেবে।", with_menu=False)
        return

    if text.strip().lower() in ["hi", "hello", "hey", "হাই", "হ্যালো", "সালাম", "assalamualaikum"]:
        send(psid, WELCOME)
        return

    code = find_code(text)
    send(psid, ANSWERS[code] if code else FALLBACK)


@app.route("/webhook", methods=["GET"])
def verify():
    """Meta এই লিংক দিয়ে ওয়েবহুক যাচাই করে।"""
    if (
        request.args.get("hub.mode") == "subscribe"
        and request.args.get("hub.verify_token") == VERIFY_TOKEN
    ):
        return request.args.get("hub.challenge", ""), 200
    return "Forbidden", 403


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True) or {}
    if data.get("object") == "page":
        for entry in data.get("entry", []):
            for event in entry.get("messaging", []):
                handle_event(event)
    return "OK", 200


@app.route("/")
def home():
    return "Bot is running."


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
