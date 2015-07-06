# Prettify input json file: indent, sort
import json
import sys
for arg in sys.argv[1:]:
    print("Reading " + arg)
    input = {}
    try:
        with open(arg, "r") as f:
            input = json.loads(f.read())
            f.close()
    except:
        pass

    out = arg + ".out"
    print("Writing " + out)
    with open(out, "w") as f:
        f.write(json.dumps(input, indent=1, sort_keys=True))
        f.close()

