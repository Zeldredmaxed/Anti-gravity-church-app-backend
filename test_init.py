import traceback
import sys

try:
    import app.main
    print("Success: app.main imported correctly")
except Exception as e:
    with open('err.log', 'w') as f:
        traceback.print_exc(file=f)
    print("Failed: exception written to err.log")
