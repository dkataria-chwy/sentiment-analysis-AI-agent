import random, urllib.parse
colors = ['#4285F4', '#EA4335', '#FBBC05', '#34A853']
dots = []
size = 1.5
opacity = 0.3
spacing = 24
svg_size = 120
for y in range(0, svg_size, spacing):
    for x in range(0, svg_size, spacing):
        color = random.choice(colors)
        dots.append(f'<circle cx="{x}" cy="{y}" r="{size}" fill="{color}" fill-opacity="{opacity}"/>')
svg = '<svg width="{}" height="{}" xmlns="http://www.w3.org/2000/svg">{}</svg>'.format(svg_size, svg_size, ''.join(dots))
data_url = "data:image/svg+xml;utf8," + urllib.parse.quote(svg)
print(data_url)
