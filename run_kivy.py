import sys
import traceback

try:
    from main import LitUpFocusApp
    LitUpFocusApp().run()
except Exception as e:
    with open("crash.txt", "w") as f:
        traceback.print_exc(file=f)
