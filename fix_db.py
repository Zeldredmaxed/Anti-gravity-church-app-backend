import glob
import os

for filepath in glob.glob("app/routers/*.py"):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    if "await db.flush()" in content:
        content = content.replace("await db.flush()", "await db.commit()")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Updated {filepath}")
