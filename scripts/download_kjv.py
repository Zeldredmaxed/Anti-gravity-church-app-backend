"""Download the complete KJV Bible (66 books) and write to app/data/kjv.json."""

import json
import urllib.request
import os

# Per-book JSON files from the public domain aruljohn/Bible-kjv repo
BASE = "https://raw.githubusercontent.com/aruljohn/Bible-kjv/master"
BOOKS_LIST_URL = f"{BASE}/Books.json"

OUTPUT = os.path.join(os.path.dirname(__file__), "..", "app", "data", "kjv.json")


def download():
    print("Fetching book list...")
    with urllib.request.urlopen(BOOKS_LIST_URL) as resp:
        book_names = json.loads(resp.read().decode("utf-8"))

    print(f"Found {len(book_names)} books. Downloading each...")
    bible = {}

    for i, book_name in enumerate(book_names, 1):
        # GitHub repo filenames have NO spaces (e.g., "1Samuel.json", "SongofSolomon.json")
        url_name = book_name.replace(" ", "")
        url = f"{BASE}/{url_name}.json"
        print(f"  [{i}/{len(book_names)}] {book_name}...")
        try:
            with urllib.request.urlopen(url) as resp:
                book_data = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            print(f"    ERROR: {e} ({url})")
            continue

        chapters = {}
        for ch_obj in book_data.get("chapters", []):
            ch_str = str(ch_obj["chapter"])
            verses = {}
            for v_obj in ch_obj["verses"]:
                verses[str(v_obj["verse"])] = v_obj["text"]
            chapters[ch_str] = verses
        bible[book_name] = chapters

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(bible, f, ensure_ascii=False)

    total_verses = sum(len(vs) for chs in bible.values() for vs in chs.values())
    size_mb = os.path.getsize(OUTPUT) / (1024 * 1024)
    print(f"\nDone! {len(bible)} books, {total_verses} verses, {size_mb:.1f} MB => {OUTPUT}")


if __name__ == "__main__":
    download()
