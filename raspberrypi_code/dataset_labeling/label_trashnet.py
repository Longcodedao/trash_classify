import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import os
import shutil
import sys

class ImageLabelerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TrashNet Image Labeler")
        self.root.geometry("800x700")

        # --- Configuration ---
        # The labels as defined in the TrashNet dataset structure
        self.labels = ['glass', 'plastic', 'metal', 'paper', 'cardboard', 'trash']
        # Image display size (will be resized to fit within this box)
        self.display_size = (700, 500)
        # Allowed image extensions
        self.image_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')

        # --- State Variables ---
        self.input_dir = ""
        self.image_list = []
        self.current_index = 0
        self.photo_image = None # Keep a reference to prevent garbage collection

        # --- GUI Setup ---
        self.setup_gui()
        
        # Start the process by asking for a directory
        self.load_images_from_directory()

    def setup_gui(self):
        # 1. Image Display Area
        self.image_frame = tk.Frame(self.root, width=self.display_size[0], height=self.display_size[1], bg='grey')
        self.image_frame.pack(pady=20)
        self.image_frame.pack_propagate(False) # Prevent frame from shrinking

        self.image_label = tk.Label(self.image_frame, text="No image loaded", bg='grey')
        self.image_label.pack(expand=True, fill='both')

        # 2. Labeling Buttons Area
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=20)

        # Create a button for each label
        for label in self.labels:
            btn = tk.Button(button_frame, text=label.capitalize(), width=12, height=2,
                            font=('Arial', 10, 'bold'),
                            command=lambda l=label: self.label_current_image(l))
            btn.pack(side=tk.LEFT, padx=10)

        # 3. Status Bar
        self.status_label = tk.Label(self.root, text="Please select a directory to start.", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)

    def load_images_from_directory(self):
        """Prompts user to select a directory and scans for images."""
        self.input_dir = filedialog.askdirectory(title="Select Folder with Images to Label")
        
        if not self.input_dir:
            messagebox.showinfo("Info", "No directory selected. Exiting.")
            self.root.destroy()
            return

        # Scan for images
        self.image_list = [f for f in os.listdir(self.input_dir) 
                           if f.lower().endswith(self.image_extensions)
                           and os.path.isfile(os.path.join(self.input_dir, f))]
        
        if not self.image_list:
            messagebox.showerror("Error", "No image files found in the selected directory.")
            self.root.destroy()
            return

        # Create category subdirectories if they don't exist
        try:
            for label in self.labels:
                label_dir = os.path.join(self.input_dir, label)
                if not os.path.exists(label_dir):
                    os.makedirs(label_dir)
                    print(f"Created directory: {label_dir}")
        except OSError as e:
             messagebox.showerror("Error", f"Could not create subdirectories for labels.\nError: {e}")
             self.root.destroy()
             return

        print(f"Found {len(self.image_list)} images to label.")
        self.current_index = 0
        self.show_current_image()

    def show_current_image(self):
        """Loads and displays the image at current_index."""
        if self.current_index < len(self.image_list):
            # Get current filename
            filename = self.image_list[self.current_index]
            file_path = os.path.join(self.input_dir, filename)
            
            # Update status
            progress = f"Image {self.current_index + 1} of {len(self.image_list)}"
            self.status_label.config(text=f"{progress} | File: {filename}")

            try:
                # Load and resize image using Pillow
                pil_image = Image.open(file_path)
                pil_image.thumbnail(self.display_size, Image.LANCZOS) # Resize while maintaining aspect ratio
                
                # Convert to Tkinter-compatible photo image
                self.photo_image = ImageTk.PhotoImage(pil_image)
                
                # Update label widget
                self.image_label.config(image=self.photo_image, text="")
            except Exception as e:
                 messagebox.showerror("Error", f"Could not load image {filename}.\nError: {e}")
                 self.next_image() # Skip corrupted image
        else:
            # No more images
            self.image_label.config(image="", text="Done! All images labeled.", font=('Arial', 20))
            self.status_label.config(text="Finished.")
            messagebox.showinfo("Finished", "You have labeled all images in the directory.")
            self.root.destroy()

    def label_current_image(self, label):
        """Moves the current image to the selected label's subdirectory."""
        if self.current_index < len(self.image_list):
            filename = self.image_list[self.current_index]
            src_path = os.path.join(self.input_dir, filename)
            dst_path = os.path.join(self.input_dir, label, filename)

            try:
                # Move file
                shutil.move(src_path, dst_path)
                print(f"Moved {filename} to {label}/")
                
                # Proceed to next image
                self.next_image()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to move file.\nError: {e}")

    def next_image(self):
        self.current_index += 1
        self.show_current_image()

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageLabelerApp(root)
    root.mainloop()
