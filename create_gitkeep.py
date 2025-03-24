import os

# Create directories if they don't exist
directories = ['input', 'output', 'done']
for directory in directories:
    os.makedirs(directory, exist_ok=True)

    # Create .gitkeep files
    with open(os.path.join(directory, '.gitkeep'), 'w') as f:
        pass

print("Created .gitkeep files in input, output, and done directories")