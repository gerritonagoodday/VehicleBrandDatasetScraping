
# Install backgroundremover:
# pip install backgroundremover

# Starting point:
# BackgroundRemoved is a copy of the raw source images

# Create new copy of  each image with the background removed
# Treated files are called *.jpg.nobackground
find BackgroundRemoved/ -type f -name "*.jpg" | xargs -I '{}'  backgroundremover -i {} -o {}.nobackground

# Remove original .jpg
find BackgroundRemoved/ -type f -name "*.jpg" -exec rm {} \;

# Rename .jpg.nobackground files to .jpg file
find BackgroundRemoved/ -type f -name "*.jpg.nobackground" | xargs -I {} rename 's/.nobackground//' {}


