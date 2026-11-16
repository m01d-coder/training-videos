"""
每天由 GitHub Actions 執行：讀 playlists.json 裡的播放清單，
用 YouTube Data API 抓所有影片，寫進 videos.json。
需要 GitHub Secret：YT_API_KEY
"""
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

API = "https://www.googleapis.com/youtube/v3/playlistItems"
TAIPEI = timezone(timedelta(hours=8))


def fetch_playlist(playlist_id, key):
    items, token = [], None
    while True:
        params = {"part": "snippet,contentDetails", "playlistId": playlist_id,
                  "maxResults": 50, "key": key}
        if token:
            params["pageToken"] = token
        with urllib.request.urlopen(API + "?" + urllib.parse.urlencode(params), timeout=30) as r:
            data = json.load(r)
        items += data.get("items", [])
        token = data.get("nextPageToken")
        if not token:
            return items


def main():
    key = os.environ.get("YT_API_KEY")
    if not key:
        sys.exit("找不到 YT_API_KEY，請到 GitHub 的 Settings → Secrets and variables → Actions 新增")

    with open("playlists.json", encoding="utf-8") as f:
        playlists = json.load(f)

    out = []
    for subject, pid in playlists.items():
        for it in fetch_playlist(pid, key):
            published = it["contentDetails"].get("videoPublishedAt")
            if not published:  # 私人或已刪除的影片
                continue
            d = datetime.fromisoformat(published.replace("Z", "+00:00")).astimezone(TAIPEI)
            out.append([subject, it["contentDetails"]["videoId"],
                        d.strftime("%Y-%m-%d"), it["snippet"]["title"]])
        print(f"{subject}: 完成")

    with open("videos.json", "w", encoding="utf-8") as f:  # 一支影片一行，方便在 GitHub 上看差異
        f.write("[\n" + ",\n".join(json.dumps(v, ensure_ascii=False) for v in out) + "\n]\n")
    print(f"共 {len(out)} 支影片")


if __name__ == "__main__":
    main()
