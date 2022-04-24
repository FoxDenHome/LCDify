from traceback import print_exc

def critical_call(func):
    try:
        return func()
    except Exception:
        print("Fatal exception happened!")
        print_exc()
        exit(1)
