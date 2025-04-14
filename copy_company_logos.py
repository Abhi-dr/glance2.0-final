import os
import shutil
import glob

# Source and destination directories
source_dir = r"C:\Users\asus\Downloads\company_logos"
dest_dir = r"demo_static\img\home\company"

# Create destination directory if it doesn't exist
os.makedirs(dest_dir, exist_ok=True)

# Image extensions to look for
image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']

# Get all image files from source directory
image_files = []
for ext in image_extensions:
    image_files.extend(glob.glob(os.path.join(source_dir, f"*{ext}")))

# Sort the files to ensure consistent naming
image_files.sort()

# Copy and rename files
for i, file_path in enumerate(image_files, 1):
    # Get file extension
    _, ext = os.path.splitext(file_path)
    
    # Create new filename
    if i <= 9:
        new_filename = f"company{i}{ext}"
    else:
        # For files 10-15, use company10-company15
        new_filename = f"company1{i-10}{ext}"
    
    # Create destination path
    dest_path = os.path.join(dest_dir, new_filename)
    
    # Copy the file
    try:
        shutil.copy2(file_path, dest_path)
        print(f"Copied {file_path} to {dest_path}")
    except Exception as e:
        print(f"Error copying {file_path}: {e}")

print(f"\nSuccessfully copied and renamed {len(image_files)} company logos")
print("Company logos are now available in the static folder with standardized names.") 