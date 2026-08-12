import json
import os
import sys
import time
import urllib.request
import urllib.parse
import urllib.error

QUEUE_PATH = os.path.join(os.path.dirname(__file__), "..", "content_queue.json")

THREADS_TOKEN = os.environ.get("THREADS_ACCESS_TOKEN")
THREADS_USER_ID = os.environ.get("THREADS_USER_ID")
IG_TOKEN = os.environ.get("IG_ACCESS_TOKEN")
IG_USER_ID = os.environ.get("IG_USER_ID")

REPO = os.environ.get("GITHUB_REPOSITORY")
BRANCH = os.environ.get("GITHUB_REF_NAME", "main")


def raw_url(rel_path):
    return f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/{rel_path}"


def http_post(url, params):
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        print(f"HTTP {e.code} 에러 응답 본문: {body}")
        raise


def needs(item, platform):
    """이 항목이 해당 플랫폼에 게시가 필요한지 (대상이면서 아직 안 올렸는지)"""
    if item["platform"] not in (platform, "both"):
        return False
    return not item.get(f"posted_{platform}", False)


def post_threads(text, image_rel_path):
    base = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}"
    params = {"access_token": THREADS_TOKEN, "text": text}
    if image_rel_path:
        params["media_type"] = "IMAGE"
        params["image_url"] = raw_url(image_rel_path)
    else:
        params["media_type"] = "TEXT"
    created = http_post(f"{base}/threads", params)
    creation_id = created["id"]
    time.sleep(5)
    http_post(f"{base}/threads_publish", {"access_token": THREADS_TOKEN, "creation_id": creation_id})
    print("Threads 게시 완료")


def post_instagram(text, image_rel_path):
    base = f"https://graph.facebook.com/v21.0/{IG_USER_ID}"
    created = http_post(f"{base}/media", {
        "access_token": IG_TOKEN,
        "image_url": raw_url(image_rel_path),
        "caption": text,
    })
    creation_id = created["id"]
    time.sleep(5)
    http_post(f"{base}/media_publish", {"access_token": IG_TOKEN, "creation_id": creation_id})
    print("Instagram 게시 완료")


def main():
    with open(QUEUE_PATH, encoding="utf-8") as f:
        queue = json.load(f)

    target = next((item for item in queue if needs(item, "threads") or needs(item, "instagram")), None)
    if target is None:
        print("게시할 대기 항목 없음")
        return

    print(f"게시 대상: {target['id']}")
    any_attempted = False
    any_failed = False

    if needs(target, "threads"):
        any_attempted = True
        try:
            post_threads(target["text"], target.get("image"))
            target["posted_threads"] = True
        except Exception as e:
            print(f"Threads 게시 실패: {e}")
            any_failed = True

    if needs(target, "instagram"):
        if not IG_TOKEN or not IG_USER_ID or not target.get("image"):
            print("Instagram 자격증명 또는 이미지 없음, 건너뜀")
        else:
            any_attempted = True
            try:
                post_instagram(target["text"], target.get("image"))
                target["posted_instagram"] = True
            except Exception as e:
                print(f"Instagram 게시 실패: {e}")
                any_failed = True

    with open(QUEUE_PATH, "w", encoding="utf-8") as f:
        json.dump(queue, f, ensure_ascii=False, indent=2)
    print("큐 업데이트 완료 (성공한 플랫폼만 posted 처리)")

    if any_attempted and any_failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
