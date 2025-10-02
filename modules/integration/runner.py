import importlib, json, sys, traceback
def main():
    try:
        payload = json.load(sys.stdin)
        module = payload["module"]; call = payload["callable"]; kwargs = payload.get("kwargs", {})
        mod = importlib.import_module(module)
        fn = getattr(mod, call.split(".")[-1]) if "." in call else getattr(mod, call)
        res = fn(**kwargs); print(json.dumps({"ok": True, "result": res}))
    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e), "trace": traceback.format_exc()})); sys.exit(1)
if __name__ == "__main__": main()
