import os
import sys
import webbrowser
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from typing import Callable, Tuple, Optional
import cv2

import pyvirtualcam

import numpy as np
from PIL import Image, ImageOps

import roop.globals
import roop.metadata
from roop.face_analyser import get_one_face
from roop.capturer import get_video_frame, get_video_frame_total
from roop.face_reference import get_face_reference, set_face_reference, clear_face_reference
from roop.processors.frame.core import get_frame_processors_modules
from roop.utilities import is_image, is_video, resolve_relative_path

ROOT = None
ROOT_HEIGHT = 700
ROOT_WIDTH = 600

PREVIEW = None
PREVIEW_MAX_HEIGHT = 700
PREVIEW_MAX_WIDTH = 1200

RECENT_DIRECTORY_SOURCE = None
RECENT_DIRECTORY_TARGET = None
RECENT_DIRECTORY_OUTPUT = None

preview_label = None
preview_slider = None
source_label = None
target_label = None
status_label = None


def init(start: Callable[[], None], destroy: Callable[[], None]) -> ctk.CTk:
    global ROOT, PREVIEW

    ROOT = create_root(start, destroy)
    PREVIEW = create_preview(ROOT)

    return ROOT


def create_root(start: Callable[[], None], destroy: Callable[[], None]) -> ctk.CTk:
    global source_label, target_label, status_label

    ctk.deactivate_automatic_dpi_awareness()
    ctk.set_appearance_mode('system')
    ctk.set_default_color_theme(resolve_relative_path('ui.json'))

    root = ctk.CTk()
    root.minsize(ROOT_WIDTH, ROOT_HEIGHT)
    root.title(f'{roop.metadata.name} {roop.metadata.version}')
    root.configure()
    root.protocol('WM_DELETE_WINDOW', lambda: destroy())

    source_label = ctk.CTkLabel(root, text=None)
    source_label.place(relx=0.1, rely=0.1, relwidth=0.3, relheight=0.25)
    if roop.globals.source_path:	
        select_source_path(roop.globals.source_path)

    target_label = ctk.CTkLabel(root, text=None)	
    target_label.place(relx=0.6, rely=0.1, relwidth=0.3, relheight=0.25)	
    if roop.globals.target_path:	
        select_target_path(roop.globals.target_path)

    source_button = ctk.CTkButton(root, text='Выберите лицо', cursor='hand2', command=lambda: select_source_path())
    source_button.place(relx=0.1, rely=0.4, relwidth=0.3, relheight=0.1)

    target_button = ctk.CTkButton(root, text='Выберите объект замены', cursor='hand2', command=lambda: select_target_path())
    target_button.place(relx=0.5, rely=0.4, relwidth=0.4, relheight=0.1)

    keep_fps_value = ctk.BooleanVar(value=roop.globals.keep_fps)
    keep_fps_checkbox = ctk.CTkSwitch(root, text='Оставить родной FPS', variable=keep_fps_value, cursor='hand2', command=lambda: setattr(roop.globals, 'keep_fps', not roop.globals.keep_fps))
    keep_fps_checkbox.place(relx=0.1, rely=0.6)

    keep_frames_value = ctk.BooleanVar(value=roop.globals.keep_frames)
    keep_frames_switch = ctk.CTkSwitch(root, text='Оставить папку с кадрами', variable=keep_frames_value, cursor='hand2', command=lambda: setattr(roop.globals, 'keep_frames', keep_frames_value.get()))
    keep_frames_switch.place(relx=0.1, rely=0.65)
    
    skip_audio_value = ctk.BooleanVar(value=roop.globals.skip_audio)
    skip_audio_switch = ctk.CTkSwitch(root, text='Пропустить оригианльное аудио', variable=skip_audio_value, cursor='hand2', command=lambda: setattr(roop.globals, 'skip_audio', skip_audio_value.get()))
    skip_audio_switch.place(relx=0.6, rely=0.6)

    many_faces_value = ctk.BooleanVar(value=roop.globals.many_faces)
    many_faces_switch = ctk.CTkSwitch(root, text='Заменить все лица в кадре', variable=many_faces_value, cursor='hand2', command=lambda: setattr(roop.globals, 'many_faces', many_faces_value.get()))
    many_faces_switch.place(relx=0.6, rely=0.65)

    start_button = ctk.CTkButton(root, text='Старт', cursor='hand2', command=lambda: select_output_path(start))
    start_button.place(relx=0.15, rely=0.75, relwidth=0.2, relheight=0.05)

    stop_button = ctk.CTkButton(root, text='Прервать', cursor='hand2', command=lambda: destroy())
    stop_button.place(relx=0.4, rely=0.75, relwidth=0.2, relheight=0.05)

    preview_button = ctk.CTkButton(root, text='Предпросмотр', cursor='hand2', command=lambda: toggle_preview())
    preview_button.place(relx=0.65, rely=0.75, relwidth=0.2, relheight=0.05)

    # Create a button to show the options window for webcam preview
    options_button = ctk.CTkButton(root, text="Веб-камера", cursor="hand2", command=show_options)
    options_button.place(relx=0.40, rely=0.83, relwidth=0.2, relheight=0.05)

    status_label = ctk.CTkLabel(root, text=None, justify='center')
    status_label.place(relx=0.1, rely=0.9, relwidth=0.8)

    donate_label = ctk.CTkLabel(root, text='Поддержать автора', justify='center', cursor='hand2')
    donate_label.place(relx=0.1, rely=0.9, relwidth=0.8)

    tg_label = ctk.CTkLabel(root, text='Мой Telegram канал', justify='center', cursor='hand2')
    tg_label.place(relx=0.1, rely=0.95, relwidth=0.8)

    donate_label.configure(text_color=ctk.ThemeManager.theme.get('RoopDonate').get('text_color'))
    donate_label.bind('<Button>', lambda event: webbrowser.open('https://www.donationalerts.com/r/em1t'))

    tg_label.configure(text_color=ctk.ThemeManager.theme.get('RoopDonate').get('text_color'))
    tg_label.bind('<Button>', lambda event: webbrowser.open('https://t.me/neurogen_news'))


    return root


def create_preview(parent: ctk.CTkToplevel) -> ctk.CTkToplevel:
    global preview_label, preview_slider
    preview = ctk.CTkToplevel(parent)
    preview.withdraw()
    preview.title('Preview')
    preview.configure()
    preview.protocol('WM_DELETE_WINDOW', lambda: toggle_preview())
    preview.resizable(width=False, height=False)
    preview_label = ctk.CTkLabel(preview, text=None)
    preview_label.pack(fill='both', expand=True)
    preview_slider = ctk.CTkSlider(preview, from_=0, to=0, command=lambda frame_value: update_preview(frame_value))
    preview.bind('<Up>', lambda event: update_face_reference(1))
    preview.bind('<Down>', lambda event: update_face_reference(-1))
    preview.bind('<Right>', lambda event: update_frame(10))
    preview.bind('<Left>', lambda event: update_frame(-10))
    return preview


def update_status(text: str) -> None:
    status_label.configure(text=text)
    ROOT.update()


def select_source_path(source_path: Optional[str] = None) -> None:
    global RECENT_DIRECTORY_SOURCE
    if PREVIEW:
        PREVIEW.withdraw()
    if source_path is None:
        source_path = ctk.filedialog.askopenfilename(title='select an source image', initialdir=RECENT_DIRECTORY_SOURCE)
    if is_image(source_path):
        roop.globals.source_path = source_path  # type: ignore
        RECENT_DIRECTORY_SOURCE = os.path.dirname(roop.globals.source_path)
        image = render_image_preview(roop.globals.source_path, (200, 200))
        source_label.configure(image=image)
    else:
        roop.globals.source_path = None
        source_label.configure(image=None)
def select_target_path(target_path: Optional[str] = None) -> None:
    global RECENT_DIRECTORY_TARGET
    if PREVIEW:
        PREVIEW.withdraw()
    clear_face_reference()
    if target_path is None:
        target_path = ctk.filedialog.askopenfilename(title='select an target image or video', initialdir=RECENT_DIRECTORY_TARGET)
    if is_image(target_path):
        roop.globals.target_path = target_path  # type: ignore
        RECENT_DIRECTORY_TARGET = os.path.dirname(roop.globals.target_path)
        image = render_image_preview(roop.globals.target_path, (200, 200))
        target_label.configure(image=image)
    elif is_video(target_path):
        roop.globals.target_path = target_path  # type: ignore
        RECENT_DIRECTORY_TARGET = os.path.dirname(roop.globals.target_path)
        video_frame = render_video_preview(target_path, (200, 200))
        target_label.configure(image=video_frame)
    else:
        roop.globals.target_path = None
        target_label.configure(image=None)

def select_output_path(start: Callable[[], None]) -> None:
    global RECENT_DIRECTORY_OUTPUT

    if is_image(roop.globals.target_path):
        output_path = ctk.filedialog.asksaveasfilename(title='save image output file', defaultextension='.png', initialfile='output.png', initialdir=RECENT_DIRECTORY_OUTPUT)
    elif is_video(roop.globals.target_path):
        output_path = ctk.filedialog.asksaveasfilename(title='save video output file', defaultextension='.mp4', initialfile='output.mp4', initialdir=RECENT_DIRECTORY_OUTPUT)
    else:
        output_path = None
    if output_path:
        roop.globals.output_path = output_path
        RECENT_DIRECTORY_OUTPUT = os.path.dirname(roop.globals.output_path)
        start()


def render_image_preview(image_path: str, size: Tuple[int, int]) -> ctk.CTkImage:
    image = Image.open(image_path)
    if size:
        image = ImageOps.fit(image, size, Image.LANCZOS)
    return ctk.CTkImage(image, size=image.size)


def render_video_preview(video_path: str, size: Tuple[int, int], frame_number: int = 0) -> ctk.CTkImage:
    capture = cv2.VideoCapture(video_path)
    if frame_number:
        capture.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    has_frame, frame = capture.read()
    if has_frame:
        image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        if size:
            image = ImageOps.fit(image, size, Image.LANCZOS)
        return ctk.CTkImage(image, size=image.size)
    capture.release()
    cv2.destroyAllWindows()


def toggle_preview() -> None:
    if PREVIEW.state() == 'normal':
        PREVIEW.withdraw()
    elif roop.globals.source_path and roop.globals.target_path:
        init_preview()
        update_preview(roop.globals.reference_frame_number)
        PREVIEW.deiconify()


def init_preview() -> None:
    if is_image(roop.globals.target_path):
        preview_slider.pack_forget()
    if is_video(roop.globals.target_path):
        video_frame_total = get_video_frame_total(roop.globals.target_path)
        preview_slider.configure(to=video_frame_total)
        preview_slider.pack(fill='x')
        preview_slider.set(roop.globals.reference_frame_number)
def update_preview(frame_number: int = 0) -> None:
    if roop.globals.source_path and roop.globals.target_path:
        temp_frame = get_video_frame(roop.globals.target_path, frame_number)
        source_face = get_one_face(cv2.imread(roop.globals.source_path))
        if not get_face_reference():
            reference_frame = get_video_frame(roop.globals.target_path, roop.globals.reference_frame_number)
            reference_face = get_one_face(reference_frame, roop.globals.reference_face_position)
            set_face_reference(reference_face)
        else:
            reference_face = get_face_reference()
        for frame_processor in get_frame_processors_modules(roop.globals.frame_processors):
            temp_frame = frame_processor.process_frame(
                source_face,
                reference_face,
                temp_frame
            )
        image = Image.fromarray(cv2.cvtColor(temp_frame, cv2.COLOR_BGR2RGB))
        image = ImageOps.contain(image, (PREVIEW_MAX_WIDTH, PREVIEW_MAX_HEIGHT), Image.LANCZOS)
        image = ctk.CTkImage(image, size=image.size)
        preview_label.configure(image=image)

def update_face_reference(steps: int) -> None:
    clear_face_reference()
    reference_frame_number = preview_slider.get()
    roop.globals.reference_face_position += steps  # type: ignore
    roop.globals.reference_frame_number = reference_frame_number
    update_preview(reference_frame_number)


def update_frame(steps: int) -> None:
    frame_number = preview_slider.get() + steps
    preview_slider.set(frame_number)
    update_preview(preview_slider.get())
        

# Define a function to create a new window with options for webcam preview
def show_options():
    global options_window, resolution_var, device_var
    options_window = tk.Toplevel(ROOT)  # Use ROOT instead of root
    options_window.title("Настройки камеры")  # Set the title of the window
    options_window.geometry("300x200")  # Set the size of the window

    # Create a label for resolution
    resolution_label = tk.Label(options_window, text="Разрешение:")
    resolution_label.pack()

    # Create a list of possible resolutions
    resolutions = ["480x360", "640x480", "800x600", "1024x768", "1280x720", "1920x1080"]

    # Create a variable to store the selected resolution
    resolution_var = tk.StringVar(options_window)
    resolution_var.set(resolutions[0])  # Set the default value

    # Create a dropdown menu for resolution
    resolution_menu = tk.OptionMenu(options_window, resolution_var, *resolutions)
    resolution_menu.pack()

    # Create a label for device index
    device_label = tk.Label(options_window, text="Индекс устройства:")
    device_label.pack()

    # Create a combobox for device index
    device_combobox = ttk.Combobox(options_window)
    device_combobox.pack()
    device_combobox['values'] = [0, 1, 2, 3, 4]  # You can change this to list available devices
    device_combobox.current (0)


    # Create a button to start the webcam preview with the selected options and pass "webcam" as mode
    webcam_button = tk.Button(options_window, text="Режим Live камеры", command=lambda: start_preview_webcam("webcam", resolution_var.get(), device_combobox.get()))
    webcam_button.pack()

    # Create a button to start the virtual camera with the selected options and pass "virtual" as mode
    virtual_cam_button = tk.Button(options_window, text="Режим виртуальной камеры", command=lambda: start_preview_webcam("virtual", resolution_var.get(), device_combobox.get()))
    virtual_cam_button.pack()

def start_preview_webcam(mode, resolution, device): # Add arguments for mode, resolution and device
    global options_window

    # Close the options window
    options_window.destroy()

    try:
        width, height = map(int, resolution.split("x"))  # Split the resolution into width and height and convert them to integers
        device = int(device)  # Convert the device index to integer
        if mode == "webcam": # If the mode is webcam
            webcam_preview(width, height, device)  # Call the webcam_preview function with the given arguments
        elif mode == "virtual": # If the mode is virtual
            virtual_cam(width, height, device)  # Call the virtual_cam function with the given arguments
        else: # If the mode is invalid
            print("Invalid mode") # Print an error message
    except ValueError:  # If the resolution is not a valid format or the device index is not a valid integer
        print("Invalid input")  # Print an error message

def webcam_preview(width, height, device):
    global preview_label, PREVIEW
    if roop.globals.source_path is None:
        # No image selected
        update_status('Вы не выбрали изображение с лицом для замены')
        return

    cap = cv2.VideoCapture(device, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc('H', '2', '6', '4'))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_HW_ACCELERATION, 1)
    PREVIEW_MAX_HEIGHT = height
    PREVIEW_MAX_WIDTH = width

    preview_label.configure(image=None)

    PREVIEW.deiconify()

    frame_processors = get_frame_processors_modules(roop.globals.frame_processors)
    source_face = get_one_face(cv2.imread(roop.globals.source_path))

    source_image = None
    reference_face = None

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if source_image is None and roop.globals.source_path:
            source_image = get_one_face(cv2.imread(roop.globals.source_path))

        if reference_face is None:
            reference_frame = get_video_frame(roop.globals.target_path, roop.globals.reference_frame_number)
            reference_face = get_one_face(reference_frame, roop.globals.reference_face_position)
            set_face_reference(reference_face)

        temp_frame = frame.copy()

        for frame_processor in get_frame_processors_modules(roop.globals.frame_processors):
            temp_frame = frame_processor.process_frame(
                source_face,
                reference_face,
                temp_frame
            )

        image = cv2.cvtColor(temp_frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(image)
        image = ImageOps.contain(image, (PREVIEW_MAX_WIDTH, PREVIEW_MAX_HEIGHT), Image.LANCZOS)
        image = ctk.CTkImage(image, size=image.size)
        preview_label.configure(image=image)
        ROOT.update()

    cap.release()
    PREVIEW.withdraw()

def virtual_cam(width, height, device):
    global PREVIEW
    if roop.globals.source_path is None:
        # No image selected
        update_status('Вы не выбрали изображение с лицом для замены')
        return

    cap = cv2.VideoCapture(device, cv2.CAP_DSHOW)  # Capture video from the selected device
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc('M', 'J', 'P', 'G'))      
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)  # Set the selected width of the resolution
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)  # Set the selected height of the resolution
    cap.set(cv2.CAP_PROP_FPS, 25)  # Set the frame rate of the webcam

    with pyvirtualcam.Camera(width=width, height=height, fps=30) as cam: # Create a virtual camera with the selected width and height
        frame_processors = get_frame_processors_modules(roop.globals.frame_processors)
        source_face = get_one_face(cv2.imread(roop.globals.source_path))

        source_image = None  # Initialize variable for the selected face image
        reference_face = None

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if source_image is None and roop.globals.source_path:
                source_image = get_one_face(cv2.imread(roop.globals.source_path))

            if reference_face is None:
                reference_frame = get_video_frame(roop.globals.target_path, roop.globals.reference_frame_number)
                reference_face = get_one_face(reference_frame, roop.globals.reference_face_position)
                set_face_reference(reference_face)

            temp_frame = frame.copy()

            for frame_processor in get_frame_processors_modules(roop.globals.frame_processors):
                temp_frame = frame_processor.process_frame(
                    source_face,
                    reference_face,
                    temp_frame
                )

            temp_frame = cv2.cvtColor(temp_frame, cv2.COLOR_BGR2RGB) # Convert the frame to RGB format
            temp_frame = np.flip(temp_frame, axis=1) # Flip the frame horizontally
            cam.send(temp_frame) # Send the frame to the virtual camera
            cam.sleep_until_next_frame() # Wait until it's time for the next frame
            ROOT.update()

    cap.release() # Release the webcam
    PREVIEW.withdraw()