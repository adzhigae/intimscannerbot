# gender_check.py
import sys
from insightface.app import FaceAnalysis
from PIL import Image
import numpy as np

app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
app.prepare(ctx_id=0)

def check_gender(path):
    img = np.array(Image.open(path).convert("RGB"))
    faces = app.get(img)
    if not faces:
        return "no_face"
    return "female" if faces[0].gender == 0 else "male"

if __name__ == "__main__":
    path = sys.argv[1]
    result = check_gender(path)
    print(result)
