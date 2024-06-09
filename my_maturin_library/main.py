import os, shutil
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import platform

if "Windows" in platform.platform():
    env_paths = os.environ['OPENCV_DIR'].split(";")

    for path in env_paths:
        if "bin" in path:
            os.add_dll_directory(path)

import my_maturin_library

class ImageViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("Object Detection Viewer")

        self.folder_path = None
        self.outputs = None
        
        self.images = []
        self.current_image_index = 0
        
        self.label = tk.Label(root)
        self.label.pack()

        self.prev_button = tk.Button(root, text="<<", command=self.prev_image)
        self.prev_button.pack(side=tk.LEFT)
        self.prev_button = tk.Button(root, text=">>", command=self.next_image)
        self.prev_button.pack(side=tk.RIGHT)

        button_frame = tk.Frame(root)
        button_frame.pack(side=tk.BOTTOM)

        self.load_button = tk.Button(button_frame, text="Load folder", command=self.load_folder)
        self.load_button.pack(side=tk.LEFT)

        self.detect_button = tk.Button(button_frame, text="Detect objects", command=self.detect_objects)
        self.detect_button.pack(side=tk.LEFT)

        self.detect_button = tk.Button(button_frame, text="Show detections", command=self.show_detections)
        self.detect_button.pack(side=tk.LEFT)

        self.detect_button = tk.Button(button_frame, text="Show images", command=self.show_images)
        self.detect_button.pack(side=tk.LEFT)

        self.detect_button = tk.Button(button_frame, text="Clear all outputs", command=self.clear_outputs)
        self.detect_button.pack(side=tk.LEFT)

    def show_images(self):
        if self.folder_path != None and os.path.exists(self.folder_path):
            self.images = [os.path.join(self.folder_path, f).replace("\\","/") for f in os.listdir(self.folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
            self.images.sort() 
            self.show_image()
        else:
            print("Folder not specified")

    def load_folder(self):
        folder_path = filedialog.askdirectory()
        self.folder_path = folder_path
        self.outputs = (self.folder_path+"/outputs").replace("\\","/")
        if folder_path:
            self.images = [os.path.join(folder_path, f).replace("\\","/") for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
            self.images.sort() 
            if self.images:
                self.current_image_index = 0
                self.show_image()
                for image in self.images:
                    print('Loaded image: ', image)
            else:
                messagebox.showerror("Error", "No images found in the selected folder.")

    def show_image(self):
        image_path = self.images[self.current_image_index]
        image = Image.open(image_path)
        image = image.resize((800, 600), Image.LANCZOS)
        photo = ImageTk.PhotoImage(image)

        self.label.config(image=photo)
        self.label.image = photo

    def show_detections(self):
        if self.outputs != None and os.path.exists(self.outputs):
            self.images = [os.path.join(self.outputs, f).replace("\\","/") for f in os.listdir(self.outputs) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
            self.images.sort() 
            print(self.images)
            self.show_image()
        else:
            print("There are no outputs")

    def prev_image(self):
        if self.images:
            self.current_image_index = (self.current_image_index - 1) % len(self.images)
            self.show_image()

    def next_image(self):
        if self.images:
            self.current_image_index = (self.current_image_index + 1) % len(self.images)
            self.show_image()

    def detect_objects(self):
        if self.images:
            my_maturin_library.object_detection(self.folder_path)
        else:
           print("Folder not specified")

    def clear_outputs(self):
        if self.folder_path:
            print(self.outputs)
            if self.outputs != None and os.path.exists(self.outputs):
                shutil.rmtree(self.outputs)
                self.show_images()
            else:
                print('Folder "outputs" does not exist')
        else:
            print("Folder not specified")

    def change_view(self):
        pass

# def select_directory():
#     root = tk.Tk()
#     root.withdraw()  # Hide the root window
#     image_dir = filedialog.askdirectory(title="Select the image directory")
#     return image_dir

def center_window(root, width, height):
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)

    root.geometry(f'{width}x{height}+{x}+{y}')

def main():
    print(my_maturin_library.__doc__)

    width, height = 1024, 768

    root = tk.Tk()
    center_window(root, width, height)
    viewer = ImageViewer(root)
    root.mainloop()


if __name__ == "__main__":
    main()
