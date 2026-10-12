from PIL import Image, ImageFilter
import numpy as np
from collections import deque

input_path = "haki-fmcg-frontend/public/rfp-hero-illustration.png"
output_path = "haki-fmcg-frontend/public/rfp-hero-illustration.png"
test_output_path = "C:/Users/Preethi/.gemini/antigravity-ide/brain/42e3133b-9034-4a9d-b166-4ee2dab01fe3/scratch/transparent_hero.png"

img = Image.open(input_path).convert("RGBA")
arr = np.array(img, dtype=np.float32)
h, w, _ = arr.shape

bg_color = np.array([255.0, 249.0, 221.0])
color_diff = np.linalg.norm(arr[:, :, :3] - bg_color, axis=2)
is_yellow_tint = (arr[:, :, 0] - arr[:, :, 2]) >= 15

# Candidate background pixels
is_candidate_bg = (color_diff <= 38.0) & is_yellow_tint

# BFS from image perimeter
visited = np.zeros((h, w), dtype=bool)
queue = deque()

# Add all perimeter pixels that match candidate background
for y in range(h):
    for x in [0, w - 1]:
        if is_candidate_bg[y, x] and not visited[y, x]:
            visited[y, x] = True
            queue.append((y, x))

for x in range(w):
    for y in [0, h - 1]:
        if is_candidate_bg[y, x] and not visited[y, x]:
            visited[y, x] = True
            queue.append((y, x))

# 8-connectivity BFS
neighbors = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
while queue:
    cy, cx = queue.popleft()
    for dy, dx in neighbors:
        ny, nx = cy + dy, cx + dx
        if 0 <= ny < h and 0 <= nx < w:
            if not visited[ny, nx] and is_candidate_bg[ny, nx]:
                visited[ny, nx] = True
                queue.append((ny, nx))

# visited is True for outer background pixels
# Let's create an alpha mask
# Initialize alpha = 255
alpha = np.ones((h, w), dtype=np.float32) * 255.0
alpha[visited] = 0.0

# Soften the boundary transition by blurring the alpha mask slightly (radius 1)
alpha_img = Image.fromarray(alpha.astype(np.uint8), mode='L')
alpha_blurred = alpha_img.filter(ImageFilter.GaussianBlur(radius=1.2))
alpha_arr = np.array(alpha_blurred, dtype=np.uint8)

# Wherever visited was true and deep in background, keep 0
alpha_arr[visited & (color_diff < 15.0)] = 0

# Apply alpha channel
result_arr = np.array(img)
result_arr[:, :, 3] = alpha_arr

result_img = Image.fromarray(result_arr, mode='RGBA')
result_img.save(test_output_path)
result_img.save(output_path)
print("Saved transparent image successfully to", output_path)
print("Background pixels made transparent:", np.sum(alpha_arr == 0))
