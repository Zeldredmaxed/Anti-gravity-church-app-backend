"""Script to generate a developer-mock KJV Bible JSON for testing.

The full KJV JSON is 4.5MB. For this MVP/development environment,
we are generating a sample with Genesis 1 and John 3. 

Users can replace `kjv.json` with a full KJV json database in production.
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent
KJV_FILE = DATA_DIR / "kjv.json"

def generate_dev_bible():
    print("Generating dev-mode KJV Bible data...")
    
    bible = {
        "Genesis": {
            "1": {
                "1": "In the beginning God created the heaven and the earth.",
                "2": "And the earth was without form, and void; and darkness was upon the face of the deep. And the Spirit of God moved upon the face of the waters.",
                "3": "And God said, Let there be light: and there was light."
            }
        },
        "John": {
            "3": {
                "16": "For God so loved the world, that he gave his only begotten Son, that whosoever believeth in him should not perish, but have everlasting life.",
                "17": "For God sent not his Son into the world to condemn the world; but that the world through him might be saved."
            }
        }
    }
    
    with open(KJV_FILE, "w", encoding="utf-8") as f:
        json.dump(bible, f, indent=2, ensure_ascii=False)
        
    print(f"Successfully saved dev KJV data to {KJV_FILE}")

if __name__ == "__main__":
    generate_dev_bible()
