from PIL import Image
import sys

fn = sys.argv[1]

img = Image.open(fn)
out = ""
for p in img.getdata():
    assert p[0] == p[1] and p[0] == p[2]
    c = p[0]
    if c < 32 or c >= 128:
        continue
    out += chr(c)
print(out)
