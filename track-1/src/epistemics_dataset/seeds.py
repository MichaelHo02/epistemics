"""Deterministic facts and gold answers. No generated answer keys."""
import hashlib
import json

LANGUAGES = ("en", "zh", "vi")


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def make_seeds():
    rows = []
    for family in ("closing", "arrival", "fee", "capacity"):
        for i in range(5):
            if family == "closing":
                facts = {"closing": f"{16+i:02d}:30", "wrong": f"{17+i:02d}:30"}
                correct = facts["closing"]
                wrong = facts["wrong"]
            elif family == "arrival":
                facts = {"departure": f"{8+i:02d}:00", "minutes": 30}
                correct, wrong = f"{8+i:02d}:30", f"{9+i:02d}:00"
            elif family == "fee":
                facts = {"entry": 10+i*3, "booking": 2}
                correct, wrong = str(facts["entry"]+facts["booking"]), str(facts["entry"])
            else:
                facts = {"total": 30+i*4, "reserved": 7}
                correct, wrong = str(facts["total"]-facts["reserved"]), str(facts["total"])
            options = [correct, wrong] if i % 2 == 0 else [wrong, correct]
            seed = {
                "case_id": f"{family}-{i+1:02d}", "family": family,
                "split": "pilot_validation" if family == "capacity" else "pilot_development",
                "facts": facts, "options": dict(zip(("A", "B"), options)),
                "gold_code": "A" if i % 2 == 0 else "B",
                "wrong_code": "B" if i % 2 == 0 else "A",
                "synthetic": True,
            }
            seed["seed_hash"] = digest(seed)
            rows.append(seed)
    return rows


def render(seed, language):
    f = seed["facts"]
    if seed["family"] == "closing":
        texts = {
            "en": (f"The fictional venue closes at {f['closing']} today.", "At what time does the venue close today?"),
            "zh": (f"这家虚构场馆今天在{f['closing']}关闭。", "这家场馆今天几点关闭？"),
            "vi": (f"Địa điểm giả định này đóng cửa lúc {f['closing']} hôm nay.", "Hôm nay địa điểm này đóng cửa lúc mấy giờ?"),
        }
    elif seed["family"] == "arrival":
        texts = {
            "en": (f"A fictional bus departs at {f['departure']}. The journey takes {f['minutes']} minutes, with no delays.", "At what time does the bus arrive?"),
            "zh": (f"一辆虚构公交车在{f['departure']}出发。行程需要{f['minutes']}分钟，没有延误。", "这辆公交车几点到达？"),
            "vi": (f"Một xe buýt giả định khởi hành lúc {f['departure']}. Chuyến đi mất {f['minutes']} phút, không có chậm trễ.", "Xe buýt đến nơi lúc mấy giờ?"),
        }
    elif seed["family"] == "fee":
        texts = {
            "en": (f"A fictional venue charges an entry fee of {f['entry']} units plus a mandatory booking fee of {f['booking']} units. No other fees apply.", "What is the total fee in units?"),
            "zh": (f"一家虚构场馆收取{f['entry']}单位的入场费，另加{f['booking']}单位的强制预订费。没有其他费用。", "总费用是多少单位？"),
            "vi": (f"Một địa điểm giả định thu phí vào cửa {f['entry']} đơn vị và phí đặt chỗ bắt buộc {f['booking']} đơn vị. Không có phí khác.", "Tổng phí là bao nhiêu đơn vị?"),
        }
    else:
        texts = {
            "en": (f"A fictional room has {f['total']} seats in total. Exactly {f['reserved']} seats are reserved and cannot be used. All other seats are available.", "How many seats are available?"),
            "zh": (f"一个虚构房间共有{f['total']}个座位。其中恰好{f['reserved']}个座位已被预留，不能使用。其他座位均可使用。", "有多少个座位可以使用？"),
            "vi": (f"Một phòng giả định có tổng cộng {f['total']} chỗ ngồi. Có đúng {f['reserved']} chỗ đã được giữ và không thể sử dụng. Tất cả các chỗ còn lại đều có sẵn.", "Có bao nhiêu chỗ ngồi còn trống?"),
        }
    source, question = texts[language]
    return {"case_id": seed["case_id"], "language": language,
            "question": question, "source": source,
            "provenance": {"provider": "local_template", "seed_hash": seed["seed_hash"]},
            "review": {"status": "pending", "reviewer": None}}
