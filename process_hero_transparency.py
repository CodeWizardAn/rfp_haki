import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt, binary_fill_holes
from collections import deque

input_path = "C:/Users/Preethi/.gemini/antigravity-ide/brain/42e3133b-9034-4a9d-b166-4ee2dab01fe3/.user_uploaded/media_1791730122873.png"
output_path = "haki-fmcg-frontend/public/rfp-hero-illustration.png"

img = Image.open(input_path).convert("RGBA")
arr = np.array(img)
h, w, _ = arr.shape

# Background color signature: warm cream/yellow background and its dots
# R >= 240, G >= 230, B in [200, 232], R > B + 18
is_bg_candidate = (
    (arr[:, :, 0] >= 240) &
    (arr[:, :, 1] >= 228) &
    (arr[:, :, 2] >= 200) &
    (arr[:, :, 2] <= 232) &
    (arr[:, :, 0] - arr[:, :, 2] >= 18)
)

# Flood fill from all 4 outer borders so we only mark the exterior background
visited = np.zeros((h, w), dtype=bool)
queue = deque()

for y in range(h):
    for x in [0, w - 1]:
        if is_bg_candidate[y, x] and not visited[y, x]:
            visited[y, x] = True
            queue.append((y, x))

for x in range(w):
    for y in [0, h - 1]:
        if is_bg_candidate[y, x] and not visited[y, x]:
            visited[y, x] = True
            queue.append((y, x))

neighbors = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
while queue:
    cy, cx = queue.popleft()
    for dy, dx in neighbors:
        ny, nx = cy + dy, cx + dx
        if 0 <= ny < h and 0 <= nx < w:
            if not visited[ny, nx] and is_bg_candidate[ny, nx]:
                visited[ny, nx] = True
                queue.append((ny, nx))

# visited is True for all exterior background pixels
# Foreground is ~visited
foreground_mask = ~visited

# Distance from background into foreground for smooth antialiasing
dist_inside = distance_transform_edt(foreground_mask)

# For pixels strictly inside foreground (> 2.0 pixels deep), alpha = 255
# For pixels at boundary (0 to 2.0 pixels), smooth ramp from 0 to 255
ramp_width = 2.2
alpha = np.clip(dist_inside / ramp_width, 0.0, 1.0) * 255.0
alpha_uint8 = alpha.astype(np.uint8)

# Make sure visited pixels have strictly 0 alpha
alpha_uint8[visited] = 0

result_arr = np.array(img)
result_arr[:, :, 3] = alpha_uint8

result_img = Image.fromarray(result_arr, mode="RGBA")
result_img.save(output_path, "PNG", optimize=True)

print("Processed and saved high-quality transparent PNG to", output_path)
print("Dimensions:", result_img.size)
print("Exterior transparent pixels:", np.sum(alpha_uint8 == 0))
print("Antialiased transition pixels:", np.sum((alpha_uint8 > 0) & (alpha_uint8 < 255)))
print("Solid foreground pixels:", np.sum(alpha_uint8 == 255))
