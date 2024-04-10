from PIL import Image, ImageDraw, ImageFont
import json
import os
from properties import resultspath

# Create a folder to store the results if it doesn't exist
results_folder = os.path.join(resultspath, 'images') 
os.makedirs(results_folder, exist_ok=True)

# Load the JSON data from the file
with open('scripts/commitexample.json', 'r', encoding='utf-8') as f:
   data = json.load(f)

# Extract the first entry from the 'Sources' attribute
first_entry = data['Sources'][0]

# Convert the first entry to a formatted string
entry_text = json.dumps(first_entry, indent=4, ensure_ascii=False)

# Determine the size of the image
width, initial_height = 1600, 2000

# Create an image with white background
img = Image.new('RGB', (width, initial_height), color = "white")
draw = ImageDraw.Draw(img)

# Use a standard font available on the system
try:
   font = ImageFont.truetype("DejaVuSans.ttf", 28)
except IOError:
   font = ImageFont.load_default()

# Define colors for attribute names and normal text
attribute_color = "blue"  # attribute names
text_color = "black"  # rest of the text

# Define additional spacing between lines
line_spacing = 12  # Increase the space between lines
padding_widht = 50
padding_height = 20

# Split the entry text into lines and process each line
lines = entry_text.split('\n')
current_height = padding_height
for line in lines:
	# Check if the line contains an attribute name
	if ': ' in line:
		attribute, value = line.split(': ', 1)
		# Draw the attribute name in the attribute color
		draw.text((padding_widht, current_height), attribute + ':', font=font, fill=attribute_color)
		# Calculate the width of the attribute name to position the value text
		attr_width, _ = draw.textsize(attribute + ': ', font=font)
		draw.text((padding_widht + attr_width, current_height), value, font=font, fill=text_color)
	else:
		# Draw regular lines in the text color
		draw.text((padding_widht, current_height), line, font=font, fill=text_color)
	# Move to the next line position, including line spacing
	current_height += font.getsize(line)[1] + line_spacing

# Crop the image to the actual content size plus some padding at the bottom
final_height = current_height + padding_height
img = img.crop((0, 0, width, final_height))

# Save the image as PNG and EPS
output_image_path_png = os.path.join(results_folder, 'JsonFile2.png')
img.save(output_image_path_png)

output_image_path_eps = os.path.join(results_folder, 'JsonFile2.eps')
img.save(output_image_path_eps)