# -*-coding:utf8-*-
import datetime, json, os, re, requests, time, datetime

VERSION = "260108"
print(f"ver.{VERSION}")
#debug用，1開啟 0關閉
debug = 0
#強制全部執行用，1開啟 0關閉
force = 0
# 不傳到TG，1開啟 0關閉
no_send_tg = 0

RootPath = os.path.dirname(os.path.abspath(__file__))
BotToken = os.environ.get("BOT_TOKEN")
BotTokenWM = os.environ.get("BOT_TOKEN_WM")
TG_HOST = os.environ.get("TG_HOST")
ChatID = os.environ.get("CHAT_ID")
UA = os.environ.get("UA")
HTTP_HEADERS = {'User-Agent': f"{UA}/v{VERSION}", 'X-Program-Id': '{UA}'}
ABEMA_API = os.environ.get("ABEMA_3RD_API")

#test
if debug:
    print("Debugging")
    ChatID = os.environ.get("CHAT_ID_TEST")

def get_timeline(url):
    j = requests.get(url, headers=HTTP_HEADERS).json()
    # use local file for test
    # with open("./abema.json") as f:
    #     j = json.loads(f.read())
    file_title = RootPath + "/abema_timeline.txt"
    for i in j:
        startAt = i.get("startAt", "")
        dates = startAt.split("T")
        date = dates[0]
        # date_obj = datetime.datetime.strptime(date, "%Y-%m-%d").date()
        # today = datetime.date.today()
        # tomorrow = today + datetime.timedelta(days=1)
        # if today > date_obj or date_obj > tomorrow:
        #     continue
        time = dates[1][0:5]
        id = i.get("id", "")
        channelId = i.get("channelId", "")
        programId = i.get("programId", "")
        seasonTitle = i.get("seasonTitle", "")
        tag = re.sub(u"([^\u4e00-\u9fa5\u3040-\u309F\u30A0-\u30FF\u0030-\u0039\u0041-\u005a\u0061-\u007a])", "", seasonTitle)
        if tag != "":
            tag = "#" + tag.replace("・", "")
        fullTitle = i.get("fullTitle", "")
        thumbnail = i.get("thumbnail", "")
        freeReservableEndAt = i.get("freeReservableEndAt", "")
        # print(f"{date} {time} {seasonTitle} {fullTitle}")
        check = f"{id}||{programId}||{date}||{time}||{fullTitle}"
        print(check)
        with open(file_title, "r", encoding="utf-8") as f:
            old = f.read()
            if check not in old:
                send_txt = f"[{date} {time}] <a href=\"https://abema.tv/channels/{channelId}/slots/{id}\">{fullTitle}</a> [<a href=\"https://abema.tv/video/episode/{programId}\">AltLink</a>][<a href=\"{thumbnail}\">Cover</a>]"
                if freeReservableEndAt != "":
                    if freeReservableEndAt == "1970-01-01T00:00:00+00:00":
                        pass
                    else:
                        end_dates = freeReservableEndAt.split("T")
                        end_date = end_dates[0]
                        end_time = end_dates[1][0:5]
                        send_txt += f"\n無料視聴期限: {end_date} {end_time}"
                send_txt += f"\n{tag}"
                send_tg_photo_retry(BotToken, ChatID, thumbnail, send_txt)
                with open(file_title, "a", encoding="utf-8") as f2:
                    f2.write(f"{check}\n")

def send_tg_photo_retry(token, chatid, photo, caption, retry=0):
    if retry >= 3:
        return
    if no_send_tg:
        return
    r = requests.post(
        f"https://api.telegram.org/bot{token}/sendphoto",
        data={"chat_id": chatid,
              "caption": caption,
              "photo": photo,
              "parse_mode": "HTML"
            }
    )
    if r.status_code != 200:
        print(photo)
        print(r.json())
        time.sleep(30)
        send_tg_photo_retry(chatid, photo, caption, retry + 1)

def send_tg_photo_thread_retry(chatid, thread_id, photo, text, parse_mode="Markdown", retry=0):
    if retry > 3:
        return
    url = f"{TG_HOST}/bot{BotTokenWM}/sendPhoto"
    data = {
        "chat_id": chatid,
        "message_thread_id": thread_id,
        "photo": photo,
        "caption": text,
        "parse_mode": parse_mode,
        "link_preview_options": json.dumps({"is_disabled": 1}),
    }
    try:
        a = requests.post(url, data=data)
        if '{"ok":true' not in a.text and '{"ok": true' not in a.text:
            send_tg_photo_thread_retry(chatid, thread_id, photo, text, parse_mode, retry + 1)
        else:
            return
    except:
        time.sleep(30)
        send_tg_photo_thread_retry(chatid, thread_id, photo, text, parse_mode, retry + 1)


today = datetime.date.today()
tomorrow = today + datetime.timedelta(days=1)
get_timeline(f"{ABEMA_API}?date={today.strftime('%Y%m%d')}")
get_timeline(f"{ABEMA_API}?date={tomorrow.strftime('%Y%m%d')}")
