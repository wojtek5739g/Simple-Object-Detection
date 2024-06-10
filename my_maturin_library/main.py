import os, shutil
import tkinter as tk
from tkinter import filedialog, messagebox, Frame
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

        self.frame = Frame(self.root)
        self.frame.pack()
        
        self.folder_path = None
        self.outputs = None
        self.detection_view = False
        
        self.images = []
        self.detected_objects = []
        self.current_image_index = 0

        self.top_frame = tk.Frame(root)
        self.prev_button_frame = Frame(self.top_frame)
        self.image_frame = Frame(self.top_frame)
        self.next_button_frame = Frame(self.top_frame)
        
        self.top_frame.pack(side='top', fill='x')
        self.prev_button_frame.pack(side='left', fill='y', expand=True)
        self.image_frame.pack(side="left", fill='y', expand=True)
        self.next_button_frame.pack(side='left', fill='y', expand=True)

        self.prev_button = tk.Button(self.prev_button_frame, text="<<", command=self.prev_image)
        self.label = tk.Label(self.image_frame)
        self.next_button = tk.Button(self.next_button_frame, text=">>", command=self.next_image)

        self.prev_button.pack(anchor='e', expand=True)
        self.next_button.pack(anchor='w', expand=True)

        self.prev_button.pack_forget()
        self.next_button.pack_forget()

        self.label.pack(expand=True)

        self.bottom_frame = tk.Frame(root)
        self.bottom_frame.pack(side='bottom', fill='x')

        self.detected_objects_label = tk.Label(self.bottom_frame, text="")
        self.detected_objects_label.pack(side='top', pady=10)
        self.detected_objects_label.pack_forget()

        self.button_container = tk.Frame(self.bottom_frame)
        self.button_container.pack(side='bottom', fill='x', pady=5)

        self.load_button = tk.Button(self.button_container, text="Load folder", command=self.load_folder)
        self.detect_button = tk.Button(self.button_container, text="Detect objects", command=self.detect_objects)
        self.show_detect_button = tk.Button(self.button_container, text="Show detections", command=self.show_detections)
        self.show_images_button = tk.Button(self.button_container, text="Show images", command=self.show_images)
        self.clear_outputs_button = tk.Button(self.button_container, text="Clear all outputs", command=self.clear_outputs)

        self.load_button.pack(side='left', expand=True, fill='x')
        self.detect_button.pack(side='left', expand=True, fill='x')
        self.show_detect_button.pack(side='left', expand=True, fill='x')
        self.show_images_button.pack(side='left', expand=True, fill='x')
        self.clear_outputs_button.pack(side='left', expand=True, fill='x')

        self.clear_outputs_button.config(state=tk.DISABLED)

    def show_images(self):
        if self.folder_path != None and os.path.exists(self.folder_path):
            self.detection_view = False
            self.detected_objects_label.pack_forget()
            self.images = [os.path.join(self.folder_path, f).replace("\\","/") for f in os.listdir(self.folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
            self.images.sort() 
            self.show_image()
        else:
            print("Folder not specified")

    def load_folder(self):
        self.detected_objects_label.pack_forget()
        self.clear_outputs_button.config(state=tk.NORMAL)
        if self.outputs != None:
            self.clear_outputs()
        folder_path = filedialog.askdirectory()
        self.prev_button.pack(anchor='e', expand=True)
        self.next_button.pack(anchor='w', expand=True)
        self.folder_path = folder_path
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

        if self.detection_view:
            self.detected_objects_label.pack(side='top', pady=10)
            self.detected_objects_label.config(text=f"{self.detected_objects[self.current_image_index]}")

        self.label.config(image=photo)
        self.label.image = photo

    def show_detections(self):
        if self.outputs != None and os.path.exists(self.outputs):
            self.detection_view = True
            self.images = [os.path.join(self.outputs, f).replace("\\","/") for f in os.listdir(self.outputs) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
            self.images.sort() 
            print(self.images)
            self.show_image()
            self.detected_objects_label.pack(side='top', pady=10)
            self.detected_objects_label.config(text=f"{self.detected_objects[self.current_image_index]}")
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
            self.outputs = (self.folder_path+"/outputs").replace("\\","/")
            self.clear_outputs()
            self.show_detect_button.config(state=tk.DISABLED)
            self.detect_button.config(state=tk.DISABLED)
            processing_window = tk.Toplevel(self.root)
            processing_window.title("Processing")
            tk.Label(processing_window, text="Processing... Please wait.").pack(padx=30, pady=30)
            
            processing_window.update()
            try:
                results = my_maturin_library.object_detection(self.folder_path)
                sorted_results = sorted(results, key=lambda x: x[0])
                self.detected_objects = []
                for idx, (img_path, objects) in enumerate(sorted_results):
                    unique_objects = list(set(objects))
                    print(unique_objects)
                    print(self.current_image_index, idx, img_path, unique_objects)
                    self.detected_objects.append(unique_objects)
                if self.detection_view:
                    self.detected_objects_label.config(text=f"{self.detected_objects[self.current_image_index]}")
                    self.detected_objects_label.pack(side='top', pady=10)
                print(self.detected_objects)
            except Exception as e:
                messagebox.showerror("Error", f"Error during processing: {e}")
            finally:
                self.show_detect_button.config(state=tk.NORMAL)
                self.detect_button.config(state=tk.NORMAL)
                processing_window.destroy()
        else:
           print("Folder not specified")

    def clear_outputs(self):
        self.detected_objects = []

        if self.outputs != None and os.path.exists(self.outputs):
            shutil.rmtree(self.outputs)
            self.show_images()
        else:
            print('Folder "outputs" does not exist')

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

