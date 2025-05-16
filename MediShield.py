import numpy as np
import pywt
from PIL import Image, ImageTk, ImageOps, ImageDraw, ImageFont
import scipy.linalg
import tkinter as tk
from tkinter import filedialog, messagebox
from customtkinter import CTkImage
import customtkinter
import os
import threading
import time
import platform


if platform.system() == "Windows":
    try:
        from ctypes import windll
    except ImportError:
        windll = None
else:
    windll = None

# Set tema dan mode tampilan
customtkinter.set_appearance_mode("System") 
customtkinter.set_default_color_theme("green")

class WatermarkingApp(customtkinter.CTk):


    def __init__(self):
        super().__init__()
        base_dir = os.path.dirname(os.path.realpath(__file__))
        icon_path = os.path.join(base_dir, "assets/icon.ico")

        # Ensure the assets directory and icon file exist
        if not os.path.exists(icon_path):
            print(f"Warning: Icon file not found at {icon_path}. Window may not have an icon.")
            icon_path = None

        if icon_path:
            try:
                self.iconbitmap(default=icon_path)
            except Exception as e:
                print(f"Warning: Could not set window icon from {icon_path}: {e}")

        if platform.system() == "Windows" and windll is not None:
            try:
                myappid = 'TugasKI.medishield.1.0'
                windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
            except Exception as e:
                print(f"Error setting AppUserModelID or taskbar icon: {e}")
        self.overrideredirect(True)

        # Konfigurasi window utama
        self.title("MediShield-DWT-SVD Medical Image Watermarking")
        self.geometry(f"{1200}x750")
        self.minsize(900, 600)

        # Variables for window dragging
        self.x = 0
        self.y = 0
        self._drag_active = False # State to track if drag is in progress

        # Variables for maximize/restore state
        self.is_maximized = False
        self.normal_geometry = None # Stores geometry before maximizing

        # Variables for minimize/restore state
        self.was_maximized_before_minimize = False # Stores if window was maximized before minimizing
        self.normal_geometry_before_minimize = None # Stores geometry before minimizing (needed for restore logic)


        # Buat title bar custom dengan tombol mac-style
        # Use a darker color for visibility against potential light mode themes
        self.title_bar = customtkinter.CTkFrame(self, height=30, fg_color="#2c2c2c", corner_radius=0) # Use corner_radius=0 for top edge
        self.title_bar.pack(fill="x", side="top")

        # Window control buttons (Mac style)
        button_size = 12
        button_padding = 8

        # Close button (red)
        self.close_button = customtkinter.CTkButton(
            self.title_bar, width=button_size, height=button_size,
            fg_color="#FF5F57", hover_color="#E04941",
            text="", corner_radius=button_size//2,
            command=self.quit)
        self.close_button.pack(side="left", padx=(button_padding, 2), pady=button_padding)

        # Minimize button (yellow)
        self.minimize_button = customtkinter.CTkButton(
            self.title_bar, width=button_size, height=button_size,
            fg_color="#FEBC2E", hover_color="#E0A929",
            text="", corner_radius=button_size//2,
            command=self.minimize_window)
        self.minimize_button.pack(side="left", padx=2, pady=button_padding)

        # Maximize button (green)
        self.maximize_button = customtkinter.CTkButton(
            self.title_bar, width=button_size, height=button_size,
            fg_color="#28CA42", hover_color="#26B83C",
            text="", corner_radius=button_size//2,
            command=self.toggle_maximize)
        self.maximize_button.pack(side="left", padx=2, pady=button_padding)

        # Title text
        self.title_label = customtkinter.CTkLabel(
            self.title_bar, text="MediShield-DWT-SVD Medical Image Watermarking",
            font=customtkinter.CTkFont(size=12, weight="bold"),
            text_color="#CCCCCC")
        self.title_label.pack(side="left", padx=15)

        # Bind events for dragging the window using the title bar
        self.title_bar.bind("<ButtonPress-1>", self.start_move)
        self.title_bar.bind("<ButtonRelease-1>", self.stop_move)
        self.title_bar.bind("<B1-Motion>", self.do_move)
        # Also bind to the title label and the empty space in the title bar
        self.title_label.bind("<ButtonPress-1>", self.start_move)
        self.title_label.bind("<ButtonRelease-1>", self.stop_move)
        self.title_label.bind("<B1-Motion>", self.do_move)
        # Bind double-click on title bar to toggle maximize
        self.title_bar.bind("<Double-Button-1>", lambda event: self.toggle_maximize())
        self.title_label.bind("<Double-Button-1>", lambda event: self.toggle_maximize())


        # Container untuk konten utama
        self.main_container = customtkinter.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=10, pady=10)

        # Variabel untuk menyimpan data
        self.original_image = None
        self.watermarked_image = None
        self.comparison_image = None
        self.path_to_image = None
        self.compare_path_to_image = None
        self.extracted_watermark = None
        self.original_svd_values = {}  # Untuk menyimpan nilai SVD original

        # Buat frame utama dengan grid layout
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(1, weight=3)
        self.main_container.grid_rowconfigure(0, weight=1)

        # Frame sidebar untuk kontrol
        self.sidebar_frame = customtkinter.CTkFrame(self.main_container, width=250, corner_radius=10)
        self.sidebar_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(19, weight=1)  # Adjusted for spacing

        # Frame utama untuk preview gambar
        self.main_frame = customtkinter.CTkFrame(self.main_container, corner_radius=10)
        self.main_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=0) # Progress frame should not take vertical space when hidden

        # Judul aplikasi
        self.app_title = customtkinter.CTkLabel(self.sidebar_frame, text="MediShield Watermarking", font=customtkinter.CTkFont(size=20, weight="bold"))
        self.app_title.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Bagian 1: Upload Original Image
        self.section_label_1 = customtkinter.CTkLabel(self.sidebar_frame, text="Step 1: Upload Original Image", font=customtkinter.CTkFont(size=14, weight="bold"))
        self.section_label_1.grid(row=1, column=0, padx=20, pady=(20, 5), sticky="w")

        self.upload_button = customtkinter.CTkButton(self.sidebar_frame, text="Upload Image", command=self.upload_image)
        self.upload_button.grid(row=2, column=0, padx=20, pady=5)

        self.image_info_label = customtkinter.CTkLabel(self.sidebar_frame, text="No image selected", font=customtkinter.CTkFont(size=12))
        self.image_info_label.grid(row=3, column=0, padx=20, pady=5, sticky="w")

        # Bagian 2: Watermark Settings
        self.section_label_2 = customtkinter.CTkLabel(self.sidebar_frame, text="Step 2: Watermark Settings", font=customtkinter.CTkFont(size=14, weight="bold"))
        self.section_label_2.grid(row=4, column=0, padx=20, pady=(20, 5), sticky="w")

        self.watermark_label = customtkinter.CTkLabel(self.sidebar_frame, text="Watermark Text:")
        self.watermark_label.grid(row=5, column=0, padx=20, pady=(5, 0), sticky="w")

        self.watermark_entry = customtkinter.CTkEntry(self.sidebar_frame, width=200, placeholder_text="Enter watermark text")
        self.watermark_entry.grid(row=6, column=0, padx=20, pady=(0, 10))

        self.alpha_label = customtkinter.CTkLabel(self.sidebar_frame, text="Watermark Strength (Alpha):")
        self.alpha_label.grid(row=7, column=0, padx=20, pady=(5, 0), sticky="w")

        self.alpha_slider = customtkinter.CTkSlider(self.sidebar_frame, from_=0.1, to=5.0, number_of_steps=49)
        self.alpha_slider.grid(row=8, column=0, padx=20, pady=(0, 0))
        self.alpha_slider.set(2.0)  # Default value

        self.alpha_value_label = customtkinter.CTkLabel(self.sidebar_frame, text="2.0")
        self.alpha_value_label.grid(row=9, column=0, padx=20, pady=(0, 10))
        self.alpha_slider.configure(command=self.update_alpha_label)

        # Bagian 3: Process
        self.section_label_3 = customtkinter.CTkLabel(self.sidebar_frame, text="Step 3: Process", font=customtkinter.CTkFont(size=14, weight="bold"))
        self.section_label_3.grid(row=10, column=0, padx=20, pady=(20, 5), sticky="w")

        self.process_button = customtkinter.CTkButton(self.sidebar_frame, text="Apply Watermark", command=self.process_with_progress, fg_color="#28a745", hover_color="#218838")
        self.process_button.grid(row=11, column=0, padx=20, pady=5)

        self.save_button = customtkinter.CTkButton(self.sidebar_frame, text="Save Watermarked Image", command=self.save_watermarked_image, state="disabled")
        self.save_button.grid(row=12, column=0, padx=20, pady=5)

        # Bagian 4: Verification
        self.section_label_4 = customtkinter.CTkLabel(self.sidebar_frame, text="Step 4: Verification", font=customtkinter.CTkFont(size=14, weight="bold"))
        self.section_label_4.grid(row=13, column=0, padx=20, pady=(20, 5), sticky="w")

        self.compare_button = customtkinter.CTkButton(self.sidebar_frame, text="Upload Image to Compare", command=self.upload_compare_image)
        self.compare_button.grid(row=14, column=0, padx=20, pady=(0, 5))

        self.verify_button = customtkinter.CTkButton(self.sidebar_frame, text="Verify Authenticity", command=self.compare_images, state="disabled", fg_color="#007bff", hover_color="#0069d9")
        self.verify_button.grid(row=15, column=0, padx=20, pady=5)

        self.extract_button = customtkinter.CTkButton(self.sidebar_frame, text="Extract Watermark", command=self.extract_watermark, state="disabled", fg_color="#6c757d", hover_color="#5a6268")
        self.extract_button.grid(row=16, column=0, padx=20, pady=5)

        # Mode selector
        self.appearance_mode_label = customtkinter.CTkLabel(self.sidebar_frame, text="Appearance Mode:")
        self.appearance_mode_label.grid(row=17, column=0, padx=20, pady=(20, 0), sticky="w")

        self.appearance_mode_option = customtkinter.CTkOptionMenu(self.sidebar_frame, values=["Light", "Dark", "System"],
                                                             command=self.change_appearance_mode)
        self.appearance_mode_option.grid(row=18, column=0, padx=20, pady=(0, 20))
        self.appearance_mode_option.set("System")

        # Main frame for image display with tabs
        self.tabview = customtkinter.CTkTabview(self.main_frame, corner_radius=10)
        # Place tabview in row 0, it will expand
        self.tabview.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Create tabs
        self.tab_original = self.tabview.add("Original Image")
        self.tab_watermarked = self.tabview.add("Watermarked Image")
        self.tab_comparison = self.tabview.add("Comparison")
        self.tab_extraction = self.tabview.add("Extracted Watermark")

        # Configure tab layouts
        for tab in [self.tab_original, self.tab_watermarked, self.tab_comparison, self.tab_extraction]:
            tab.grid_columnconfigure(0, weight=1)
            tab.grid_rowconfigure(0, weight=1)

        # Image canvas/label for each tab
        # Use CTkLabel to display images, it handles image scaling better within its bounds
        self.original_canvas = customtkinter.CTkLabel(self.tab_original, text="Upload an image first")
        self.original_canvas.grid(row=0, column=0, padx=20, pady=20, sticky="nsew") # Added sticky

        self.watermarked_canvas = customtkinter.CTkLabel(self.tab_watermarked, text="Process an image first")
        self.watermarked_canvas.grid(row=0, column=0, padx=20, pady=20, sticky="nsew") # Added sticky

        self.comparison_canvas = customtkinter.CTkLabel(self.tab_comparison, text="Upload a comparison image first")
        self.comparison_canvas.grid(row=0, column=0, padx=20, pady=20, sticky="nsew") # Added sticky

        self.extraction_canvas = customtkinter.CTkLabel(self.tab_extraction, text="Extract watermark first")
        self.extraction_canvas.grid(row=0, column=0, padx=20, pady=20, sticky="nsew") # Added sticky

        # Place progress frame in row 1
        self.progress_frame = customtkinter.CTkFrame(self.main_frame)
        self.progress_frame.grid(row=1, column=0, padx=10, pady=10, sticky="sew")
        self.progress_frame.grid_columnconfigure(0, weight=1) # Ensure progress bar expands
        self.progress_frame.grid_remove()  # Hide initially

        self.progress_label = customtkinter.CTkLabel(self.progress_frame, text="Processing...")
        self.progress_label.pack(pady=(10, 0))

        self.progress_bar = customtkinter.CTkProgressBar(self.progress_frame)
        self.progress_bar.pack(fill="x", padx=20, pady=10)
        self.progress_bar.set(0)

        # Status bar
        self.status_bar = customtkinter.CTkLabel(self, text="Ready", anchor="w")
        self.status_bar.pack(fill="x", side="bottom", padx=10, pady=(0, 5))


    # --- Window Control Methods ---

    def toggle_maximize(self):
        """Toggle between maximize and restore window"""
        if self.is_maximized:
            self.restore_window()
        else:
            self.maximize_window()


    def maximize_window(self):
        """Maximize window to fill the screen"""
        if not self.is_maximized:
            # Save current geometry before maximizing
            self.normal_geometry = self.geometry()
            self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}+0+0")
            self.is_maximized = True


    def restore_window(self):
        """Restore window to its normal size and position"""
        if self.is_maximized and self.normal_geometry:
            self.geometry(self.normal_geometry)
            self.is_maximized = False
            # Update button appearance or state if needed (optional)
        elif self.is_maximized: # Fallback if normal_geometry wasn't saved (shouldn't happen)
             print("Warning: normal_geometry not found during restore. Restoring to default non-maximized state.")
             self.is_maximized = False


    def start_move(self, event):
        """Begin window drag operation"""
        # biar bisa gerak
        if not self.is_maximized:
            self._drag_active = True
            self.x = event.x
            self.y = event.y
            self.lift()


    def stop_move(self, event):
        """End window drag operation"""
        self._drag_active = False
        self.x = 0
        self.y = 0


    def do_move(self, event):
        """Move window during drag operation"""
        # Only move if drag is active and not maximized
        if self._drag_active and not self.is_maximized:
            deltax = event.x - self.x
            deltay = event.y - self.y
            # Get current window position
            current_x = self.winfo_x()
            current_y = self.winfo_y()
            # Calculate new position
            new_x = current_x + deltax
            new_y = current_y + deltay
            # Apply new position
            self.geometry(f"+{new_x}+{new_y}")


    def minimize_window(self):
        """Minimize the window"""
        self.was_maximized_before_minimize = self.is_maximized
        self.normal_geometry_before_minimize = self.geometry()

        self.wm_withdraw()
        self.wm_overrideredirect(False)
        self.wm_iconify()

        # Bind handler to be called when the window is restored (mapped)
        self.bind("<Map>", self.on_map)


    def on_map(self, event):
        """Handle window restore from minimized state"""
        self.unbind("<Map>")
        self.wm_overrideredirect(True)

        # Restore the window geometry and state based on what it was before minimizing
        if self.was_maximized_before_minimize:
            # If it was maximized before minimizing, restore to maximized state
            self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}+0+0")
            self.is_maximized = True
        elif self.normal_geometry_before_minimize:
            # If it was in a normal state before minimizing, restore that geometry
            self.geometry(self.normal_geometry_before_minimize)
            self.is_maximized = False
        else:
             # Fallback: If no geometry was saved (shouldn't happen if minimize was called correctly)
             print("Warning: Could not determine geometry before minimize. Restored to default non-maximized state.")
             self.is_maximized = False


        # Ensure the window is visible and brought to front
        self.deiconify()
        self.lift()


        # Clear the stored minimize-specific state variables after restoration
        self.normal_geometry_before_minimize = None
        self.was_maximized_before_minimize = False


    # --- Image and Watermarking Methods ---

    def update_alpha_label(self, value):
        self.alpha_value_label.configure(text=f"{value:.1f}")


    def upload_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp *.tiff")]
        )
        if file_path:
            try:
                img = Image.open(file_path).convert("L") # Convert to grayscale
                self.original_image = np.array(img)
                self.path_to_image = file_path
                self.image_info_label.configure(text=os.path.basename(file_path))

                # Display the original image
                self.display_image(self.original_image, self.original_canvas)

                # Reset other states
                self.watermarked_image = None
                self.comparison_image = None
                self.extracted_watermark = None
                self.original_svd_values = {} # Clear stored SVD
                self.save_button.configure(state="disabled")
                self.verify_button.configure(state="disabled")
                self.extract_button.configure(state="disabled")
                self.watermarked_canvas.configure(image=None, text="Process an image first")
                self.comparison_canvas.configure(image=None, text="Upload a comparison image first")
                self.extraction_canvas.configure(image=None, text="Extract watermark first")

                self.status_bar.configure(text=f"Loaded image: {os.path.basename(file_path)}")

            except Exception as e:
                messagebox.showerror("Error", f"Could not open or process image: {e}")
                self.status_bar.configure(text="Error loading image")

# batas code

    def upload_compare_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp *.tiff")]
        )
        if file_path:
            try:
                img = Image.open(file_path).convert("L")
                self.comparison_image = np.array(img)
                self.compare_path_to_image = file_path

                # Display the comparison image
                self.display_image(self.comparison_image, self.comparison_canvas)

                # Enable verification buttons if original image is also loaded
                if self.original_image is not None:
                     self.verify_button.configure(state="normal")
                     self.extract_button.configure(state="normal") # Enable extraction button too
                else:
                     messagebox.showwarning("Warning", "Please upload the original image first.")
                     self.compare_image = None # Reset comparison image if original is missing
                     self.comparison_canvas.configure(image=None, text="Upload a comparison image first")

                self.status_bar.configure(text=f"Loaded comparison image: {os.path.basename(file_path)}")

            except Exception as e:
                messagebox.showerror("Error", f"Could not open or process comparison image: {e}")
                self.status_bar.configure(text="Error loading comparison image")
                self.compare_image = None
                self.comparison_canvas.configure(image=None, text="Upload a comparison image first")


    def display_image(self, image_array, ctk_label):
        """Displays a numpy image array on a CTkLabel using CTkImage."""
        if image_array is None:
            ctk_label.configure(image=None, text="No image to display")
            ctk_label.image = None
            return

        try:
            # Convert numpy array to PIL Image in 'L' mode (grayscale)
            img_pil = Image.fromarray(image_array, mode='L')
            
            # Get current size of the display area (adjust as needed)
            max_width = self.main_frame.winfo_width() - 40
            max_height = self.main_frame.winfo_height() - 60
            max_width = max(10, max_width)
            max_height = max(10, max_height)

            # Calculate new size maintaining aspect ratio
            img_width, img_height = img_pil.size
            ratio = min(max_width / img_width, max_height / img_height)
            new_width = int(img_width * ratio)
            new_height = int(img_height * ratio)

            # Resize using high-quality resampling
            img_resized = img_pil.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Create CTkImage
            img_ctk = CTkImage(
                light_image=img_resized,
                dark_image=img_resized,
                size=(new_width, new_height)
            )
            
            # Update CTkLabel
            ctk_label.configure(image=img_ctk, text="")
            ctk_label.image = img_ctk  # Keep reference

        except Exception as e:
            ctk_label.configure(image=None, text=f"Display Error: {str(e)}")
            ctk_label.image = None
            

    def process_with_progress(self):
        if self.original_image is None:
            messagebox.showwarning("Warning", "Please upload an image first.")
            return

        watermark_text = self.watermark_entry.get()
        alpha = self.alpha_slider.get()

        if not watermark_text:
            messagebox.showwarning("Warning", "Please enter watermark text.")
            return

        self.status_bar.configure(text="Processing...")
        self.process_button.configure(state="disabled")
        self.save_button.configure(state="disabled")
        self.verify_button.configure(state="disabled")
        self.extract_button.configure(state="disabled")

        # Show progress bar
        self.progress_frame.grid() # Use grid() instead of pack() if using grid layout
        self.progress_bar.set(0)

        # Run the watermarking process in a separate thread to keep the UI responsive
        process_thread = threading.Thread(target=self.perform_watermarking, args=(watermark_text, alpha))
        process_thread.start()


    def perform_watermarking(self, watermark_text, alpha):
        try:
            original_image_np = self.original_image.copy()

            # Ensure the image is square and its size is a power of 2 for DWT
            rows, cols = original_image_np.shape
            size = min(rows, cols)
            # Find the largest power of 2 less than or equal to size
            import math
            max_power_of_2 = 2**int(math.log2(size))

            # Crop the image to the largest square power of 2 size
            cropped_image = original_image_np[:max_power_of_2, :max_power_of_2]

            # Generate a watermark image (size related to the LL band size)
            # Let's target a watermark size related to the LL band after DWT
            wavelet = 'Zeus'
            level = 2 # Example DWT level
            if max_power_of_2 < (2**level):
                 level = int(math.log2(max_power_of_2 / 2)) # Adjust level if image is too small

            # Size of the LL band at the chosen level
            ll_size = max_power_of_2 // (2**level)

            # Generate watermark image with size matching the LL band dimensions
            watermark = self.generate_text_watermark(watermark_text, ll_size)
            watermark_np = np.array(watermark.convert("L")) # Convert to grayscale numpy array


            # --- Watermarking Process (DWT-SVD Embedding in LL band) ---

            # 1. Perform DWT on the cropped image
            coeffs = pywt.wavedec2(cropped_image, wavelet, level=level)
            LL_band = coeffs[0]

            # 2. & 3. Perform SVD on the selected band (LL)
            U, S, V = np.linalg.svd(LL_band)
            self.original_svd_values['LL_S'] = S.copy()
            s_length = len(S)
            watermark_flat = watermark_np.flatten()
            watermark_sv_like = np.interp(np.linspace(0, len(watermark_flat) - 1, s_length),
                                          np.arange(len(watermark_flat)),
                                          watermark_flat)
            watermark_sv_like = watermark_sv_like / 255.0
            embedding_factor = 0.1
            modified_S = S + alpha * watermark_sv_like * np.max(S) * embedding_factor

            m, n = LL_band.shape
            k = min(m, n)
            S_matrix = np.zeros((m, n))
            # Place the diagonal singular values
            np.fill_diagonal(S_matrix, modified_S)
            modified_LL_band = U @ S_matrix @ V

            # Replace the original LL band with the modified one
            modified_coeffs = list(coeffs)
            modified_coeffs[0] = modified_LL_band
            modified_coeffs = tuple(modified_coeffs) # Convert back to tuple

            # Perform inverse DWT
            watermarked_cropped_image = pywt.waverec2(modified_coeffs, wavelet)

            # Ensure the watermarked data is within valid pixel range [0, 255]
            watermarked_cropped_image = np.clip(watermarked_cropped_image, 0, 255)


            # Create the full watermarked image by inserting the watermarked cropped part
            full_watermarked_image = original_image_np.copy()
            full_watermarked_image[:max_power_of_2, :max_power_of_2] = watermarked_cropped_image

            self.watermarked_image = full_watermarked_image.astype(np.uint8)


            # Update UI on the main thread
            self.after(0, self.update_ui_after_processing)

        except Exception as e:
            import traceback
            traceback.print_exc() # Print traceback for debugging
            self.after(0, lambda: self.show_error_after_processing(f"Watermarking failed: {e}"))


    def update_ui_after_processing(self):
        # Hide progress bar
        self.progress_frame.grid_remove()

        # Display the watermarked image
        self.display_image(self.watermarked_image, self.watermarked_canvas)

        # Enable relevant buttons
        self.process_button.configure(state="normal")
        self.save_button.configure(state="normal")

        self.status_bar.configure(text="Watermarking complete.")
        self.tabview.set("Watermarked Image") # Switch to watermarked tab


    def show_error_after_processing(self, message):
        # Hide progress bar
        self.progress_frame.grid_remove()
        messagebox.showerror("Processing Error", message)
        self.status_bar.configure(text="Processing failed.")
        self.process_button.configure(state="normal") # Re-enable process button


    def generate_text_watermark(self, text, size):
        # Create a simple image from text
        try:
            img = Image.new('L', (size, size), color='white') # White background
            d = ImageDraw.Draw(img)

            # Try to load a default font
            try:
                font_size = int(size * 0.6) # Adjust font size relative to image size
                # Common font paths - adjust if needed for your system
                font_path = "arial.ttf" # Windows
                if platform.system() == "Darwin": # macOS
                    font_path = "/Library/Fonts/Arial.ttf"
                elif platform.system() == "Linux":
                     font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf" # Example Linux font

                font = ImageFont.truetype(font_path, font_size)
            except IOError:
                # Fallback to built-in pilfont if freetype is not available or font not found
                print("Warning: Font not found or FreeType not available. Using default PIL font.")
                font = ImageFont.load_default()
                # Adjust font size if using default font as it scales differently
                font_size = int(size * 0.1) # Default font is very small
                # No easy way to resize default font, may need to draw multiple times or use a different approach


            # Calculate text size and position to center it
            # Need to check if font.getbbox is available (newer Pillow) or font.textsize (older)
            try:
                 text_bbox = d.textbbox((0, 0), text, font=font)
                 text_width = text_bbox[2] - text_bbox[0]
                 text_height = text_bbox[3] - text_bbox[1]
            except AttributeError:
                 # Fallback for older Pillow versions
                 text_width, text_height = d.textsize(text, font=font)


            x = (size - text_width) / 2
            y = (size - text_height) / 2

            # Draw text in black
            d.text((x, y), text, fill='black', font=font)

            return img
        except Exception as e:
            print(f"Error generating text watermark: {e}")
            # Return a simple pattern or solid color in case of error
            return Image.new('L', (size, size), color='black') # Return black image on error


    def save_watermarked_image(self):
        if self.watermarked_image is None:
            messagebox.showwarning("Warning", "No watermarked image to save.")
            return

        # Suggest a filename based on the original file
        if self.path_to_image:
            original_filename = os.path.basename(self.path_to_image)
            name, ext = os.path.splitext(original_filename)
            # Ensure extension is valid, default to .png
            if ext.lower() not in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']:
                 ext = '.png'
            suggested_filename = f"{name}_watermarked{ext}"
        else:
            suggested_filename = "watermarked_image.png"

        file_path = filedialog.asksaveasfilename(
            initialfile=suggested_filename,
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"), ("BMP files", "*.bmp"), ("TIFF files", "*.tiff")]
        )

        if file_path:
            try:
                img_to_save = Image.fromarray(self.watermarked_image)
                img_to_save.save(file_path)
                self.status_bar.configure(text=f"Watermarked image saved to {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not save image: {e}")
                self.status_bar.configure(text="Error saving image")


    def compare_images(self):
        if self.original_image is None or self.comparison_image is None:
            messagebox.showwarning("Warning", "Please upload both original and comparison images.")
            return

        # Basic comparison: check dimensions and calculate PSNR or other metrics
        if self.original_image.shape != self.comparison_image.shape:
             messagebox.showwarning("Warning", "Images have different dimensions. Cannot compare.")
             self.status_bar.configure(text="Comparison failed: different dimensions.")
             return

        try:
            # Calculate Peak Signal-to-Noise Ratio (PSNR)
            original_np = self.original_image.astype(np.float64)
            comparison_np = self.comparison_image.astype(np.float64)

            mse = np.mean((original_np - comparison_np)**2)

            if mse == 0:
                psnr = float('inf')
                similarity_message = "Images are identical (PSNR: Infinity)"
            else:
                max_pixel = 255.0
                epsilon = 1e-10
                psnr = 10 * np.log10((max_pixel**2) / (mse + epsilon))
                similarity_message = f"Images similarity (PSNR): {psnr:.2f} dB"
            difference_image_np = np.abs(original_np - comparison_np)
            max_diff = np.max(difference_image_np)
            if max_diff > 0:
                difference_image_np = (difference_image_np / max_diff) * 255
            difference_image_np = difference_image_np.astype(np.uint8)

            self.display_image(difference_image_np, self.comparison_canvas)

            self.status_bar.configure(text=similarity_message)
            messagebox.showinfo("Comparison Result", similarity_message)
            self.tabview.set("Comparison") # Switch to comparison tab


        except Exception as e:
             import traceback
             traceback.print_exc()
             messagebox.showerror("Error", f"Error during comparison: {e}")
             self.status_bar.configure(text="Comparison failed.")


    def extract_watermark(self):
        # Requires original image, potentially watermarked image (uploaded as comparison),
        # and the original SVD values from the embedding process.
        if self.original_image is None or self.comparison_image is None or not self.original_svd_values:
             messagebox.showwarning("Warning", "Please upload the original image and the potentially watermarked image (as comparison). Ensure watermarking was performed successfully to store original SVD values.")
             return

        if self.original_image.shape != self.comparison_image.shape:
             messagebox.showwarning("Warning", "Images have different dimensions. Cannot extract watermark.")
             self.status_bar.configure(text="Extraction failed: different dimensions.")
             return

        try:
            original_image_np = self.original_image.copy()
            watermarked_image_np = self.comparison_image.copy() # Assume comparison is the watermarked one

            # Ensure images are cropped to the same power-of-2 size used during embedding
            rows, cols = original_image_np.shape
            size = min(rows, cols)
            import math
            max_power_of_2 = 2**int(math.log2(size))
            cropped_original = original_image_np[:max_power_of_2, :max_power_of_2]
            cropped_watermarked = watermarked_image_np[:max_power_of_2, :max_power_of_2]

            # Use the same DWT level and wavelet as during embedding
            wavelet = 'Zeus v2'
            level = 2 # Must match embedding level
            if max_power_of_2 < (2**level):
                 level = int(math.log2(max_power_of_2 / 2))


            # 1. Perform DWT on the original and watermarked images
            coeffs_original = pywt.wavedec2(cropped_original, wavelet, level=level)
            coeffs_watermarked = pywt.wavedec2(cropped_watermarked, wavelet, level=level)

            LL_original = coeffs_original[0]
            LL_watermarked = coeffs_watermarked[0]

            U_orig, S_original_extracted, V_orig = np.linalg.svd(LL_original)
            U_w, S_watermarked_extracted, V_w = np.linalg.svd(LL_watermarked)

            # Retrieve the original singular values stored during embedding
            if 'LL_S' not in self.original_svd_values:
                 messagebox.showerror("Error", "Original SVD values from embedding not found. Cannot extract.")
                 self.status_bar.configure(text="Extraction failed: Original SVD missing.")
                 return

            S_original_stored = self.original_svd_values['LL_S']

            # Ensure the lengths of the singular value arrays match
            if len(S_original_stored) != len(S_watermarked_extracted):
                messagebox.showerror("Error", "Mismatch in singular value lengths. Cannot extract.")
                self.status_bar.configure(text="Extraction failed: SV length mismatch.")
                return

            alpha = self.alpha_slider.get()

            if alpha == 0:
                 messagebox.showwarning("Warning", "Alpha was set to 0. Extraction may be inaccurate.")
                 alpha = 1e-9 # Use a very small number to avoid division by zero

            extracted_watermark_signal = (S_watermarked_extracted - S_original_stored) / alpha

            embedding_factor = 0.1
            scale_reference = np.max(S_original_extracted) * embedding_factor
            if scale_reference > 1e-9:
                 extracted_watermark_signal_rescaled = extracted_watermark_signal / scale_reference
            else:
                 extracted_watermark_signal_rescaled = extracted_watermark_signal

            signal_length = len(extracted_watermark_signal_rescaled)
            img_side = int(math.sqrt(signal_length))

            if img_side * img_side > signal_length:
                 img_side = int(math.sqrt(signal_length))
            extracted_watermark_signal_reshaped = extracted_watermark_signal_rescaled[:img_side*img_side]

            extracted_watermark_image_np = extracted_watermark_signal_reshaped.reshape((img_side, img_side))

            min_val = np.min(extracted_watermark_image_np)
            max_val = np.max(extracted_watermark_image_np)

            if max_val - min_val > 1e-9:
                extracted_watermark_image_np = 255 * (extracted_watermark_image_np - min_val) / (max_val - min_val)
            else:
                 extracted_watermark_image_np = np.full((img_side, img_side), 128.0)


            extracted_watermark_image_np = np.clip(extracted_watermark_image_np, 0, 255).astype(np.uint8)

            self.extracted_watermark = extracted_watermark_image_np

            # Display the extracted watermark
            self.display_image(self.extracted_watermark, self.extraction_canvas)

            self.status_bar.configure(text="Watermark extraction complete.")
            self.tabview.set("Extracted Watermark") # Switch to extraction tab

        except Exception as e:
             import traceback
             traceback.print_exc()
             messagebox.showerror("Error", f"Error during watermark extraction: {e}")
             self.status_bar.configure(text="Extraction failed.")


    def change_appearance_mode(self, new_appearance_mode: str):
        customtkinter.set_appearance_mode(new_appearance_mode)

    def update_alpha_label(self, value):
        """Update alpha value label when slider is moved"""
        formatted_value = f"{float(value):.1f}"
        self.alpha_value_label.configure(text=formatted_value)

    def upload_image(self):
        """Function to upload original image"""
        path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff")])
        if path:
            try:
                self.path_to_image = path
                self.original_image = Image.open(path)
                
                # Update info label
                filename = os.path.basename(path)
                w, h = self.original_image.size
                self.image_info_label.configure(text=f"{filename}\n{w}x{h}px")
                
                # Display image preview
                self.display_image(self.original_image, self.original_canvas, "Original Image")
                
                # Update status
                self.status_bar.configure(text=f"Loaded image: {filename}")
                self.tabview.set("Original Image")
                
                # Reset watermarked image
                self.watermarked_image = None
                self.save_button.configure(state="disabled")
                self.extract_button.configure(state="disabled")
            except Exception as e:
                messagebox.showerror("Error", f"Could not open image: {str(e)}")

    def upload_compare_image(self):
        """Function to upload comparison image"""
        path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff")])
        if path:
            try:
                self.compare_path_to_image = path
                self.comparison_image = Image.open(path)
                
                # Display image preview
                self.display_image(self.comparison_image, self.comparison_canvas, "Comparison Image")
                
                # Update status
                filename = os.path.basename(path)
                self.status_bar.configure(text=f"Loaded comparison image: {filename}")
                self.tabview.set("Comparison")
                
                # Enable verification
                if self.path_to_image:
                    self.verify_button.configure(state="normal")
            except Exception as e:
                messagebox.showerror("Error", f"Could not open comparison image: {str(e)}")

    def display_image(self, image, canvas, label_text="Image"):
        """Display an image on a canvas with proper resizing"""
        if image:
            # Calculate appropriate size for display
            max_width, max_height = 800, 500
            width, height = image.size
            
            if width > max_width or height > max_height:
                # Preserve aspect ratio
                ratio = min(max_width/width, max_height/height)
                width = int(width * ratio)
                height = int(height * ratio)
                display_image = image.resize((width, height), Image.Resampling.LANCZOS)
            else:
                display_image = image.copy()
            
            # Convert to PhotoImage
            if display_image.mode == 'RGBA':
                display_image = display_image.convert('RGB')
            
            photo = ImageTk.PhotoImage(display_image)
            
            # Update canvas
            canvas.configure(image=photo, text="")
            canvas.image = photo 
        else:
            canvas.configure(text=label_text, image=None)
            canvas.image = None

    def process_with_progress(self):
        """Start watermark process with progress bar"""
        if not self.path_to_image:
            messagebox.showerror("Error", "Please upload an image first")
            return
        
        if not self.watermark_entry.get():
            messagebox.showerror("Error", "Please enter watermark text")
            return
            
        # Show progress frame
        self.progress_frame.grid()
        self.progress_bar.set(0)
        self.status_bar.configure(text="Processing image...")
        
        # Start processing in a separate thread
        threading.Thread(target=self.process_thread).start()

    def process_thread(self):
        """Process image in a separate thread to avoid UI freezing"""
        try:
            # Update progress
            def update_progress(value):
                self.progress_bar.set(value)
                self.update_idletasks()
            
            # Get inputs
            watermark_text = self.watermark_entry.get()
            alpha = float(self.alpha_slider.get())
            
            # Open image
            image = Image.open(self.path_to_image)
            image_array = np.array(image)
            
            # Update progress
            update_progress(0.1)
            time.sleep(0.2)  # Give UI time to update
            
            # Run watermarking process
            result_image, svd_values = self.apply_watermark(image_array, watermark_text, alpha, update_progress)
            
            # Store SVD values for possible extraction later
            self.original_svd_values = svd_values
            
            # Create final image
            self.watermarked_image = Image.fromarray(np.uint8(result_image))
            
            # Update UI in main thread
            self.after(0, self.update_after_processing)
            
        except Exception as e:
            self.after(0, lambda: self.show_error(f"Error during processing: {str(e)}"))
    
    def update_after_processing(self):
        """Update UI after processing is complete"""
        # Hide progress
        self.progress_frame.grid_remove()
        
        # Display watermarked image
        self.display_image(self.watermarked_image, self.watermarked_canvas, "Watermarked Image")
        
        # Enable save button
        self.save_button.configure(state="normal")
        self.extract_button.configure(state="normal")
        
        # Update status
        self.status_bar.configure(text="Watermark applied successfully")
        
        # Switch to watermarked tab
        self.tabview.set("Watermarked Image")
    
    def show_error(self, message):
        """Show error message and reset progress"""
        self.progress_frame.grid_remove()
        messagebox.showerror("Error", message)
        self.status_bar.configure(text="Ready")
    
    def apply_watermark(self, image_array, watermark_text, alpha, progress_callback=None):
        """Apply watermark to image using DWT and SVD"""
        # Check if image is grayscale
        if len(image_array.shape) == 2:
            # Grayscale image
            coeffs, cA, cH, cV, cD = self.apply_dwt(image_array)
            if progress_callback: progress_callback(0.3)
            
            # Embed watermark
            watermark = np.array([ord(char) for char in watermark_text]) > 0
            U, s, Vh = scipy.linalg.svd(cA, full_matrices=False)
            if progress_callback: progress_callback(0.5)
            
            # Store original SVD values for extraction
            svd_values = {'s': s, 'U': U, 'Vh': Vh}
            
            # Apply watermark
            watermark_resized = np.resize(watermark, s.shape)
            s_w = s + alpha * watermark_resized
            if progress_callback: progress_callback(0.7)
            
            # Reconstruct image
            coeffs_watermarked = (U @ np.diag(s_w) @ Vh, (cH, cV, cD))
            watermarked_image_array = self.apply_idwt(coeffs_watermarked)
            if progress_callback: progress_callback(0.9)
            
            # Ensure valid pixel range
            watermarked_image_array = np.clip(watermarked_image_array, 0, 255)
            
            return watermarked_image_array, svd_values
            
        else:
            # Color image - process each channel
            red_channel, green_channel, blue_channel = image_array[:,:,0], image_array[:,:,1], image_array[:,:,2]
            if progress_callback: progress_callback(0.2)
            
            # Apply DWT
            coeffs_r, cA_r, cH_r, cV_r, cD_r = self.apply_dwt(red_channel)
            coeffs_g, cA_g, cH_g, cV_g, cD_g = self.apply_dwt(green_channel)
            coeffs_b, cA_b, cH_b, cV_b, cD_b = self.apply_dwt(blue_channel)
            if progress_callback: progress_callback(0.4)
            
            # Convert watermark text to binary array
            watermark = np.array([ord(char) for char in watermark_text]) > 0
            
            # Apply SVD to each channel
            U_r, s_r, Vh_r = scipy.linalg.svd(cA_r, full_matrices=False)
            U_g, s_g, Vh_g = scipy.linalg.svd(cA_g, full_matrices=False)
            U_b, s_b, Vh_b = scipy.linalg.svd(cA_b, full_matrices=False)
            if progress_callback: progress_callback(0.6)
            
            # Store original SVD values for extraction
            svd_values = {
                'red': {'s': s_r, 'U': U_r, 'Vh': Vh_r},
                'green': {'s': s_g, 'U': U_g, 'Vh': Vh_g},
                'blue': {'s': s_b, 'U': U_b, 'Vh': Vh_b}
            }
            
            # Embed watermark
            watermark_r = np.resize(watermark, s_r.shape)
            watermark_g = np.resize(watermark, s_g.shape)
            watermark_b = np.resize(watermark, s_b.shape)
            
            s_w_r = s_r + alpha * watermark_r
            s_w_g = s_g + alpha * watermark_g
            s_w_b = s_b + alpha * watermark_b
            if progress_callback: progress_callback(0.7)
            
            # Reconstruct images
            coeffs_watermarked_r = (U_r @ np.diag(s_w_r) @ Vh_r, (cH_r, cV_r, cD_r))
            coeffs_watermarked_g = (U_g @ np.diag(s_w_g) @ Vh_g, (cH_g, cV_g, cD_g))
            coeffs_watermarked_b = (U_b @ np.diag(s_w_b) @ Vh_b, (cH_b, cV_b, cD_b))
            
            watermarked_image_array_r = self.apply_idwt(coeffs_watermarked_r)
            watermarked_image_array_g = self.apply_idwt(coeffs_watermarked_g)
            watermarked_image_array_b = self.apply_idwt(coeffs_watermarked_b)
            if progress_callback: progress_callback(0.9)
            
            # Combine channels
            watermarked_image_array = np.stack(
                (watermarked_image_array_r, watermarked_image_array_g, watermarked_image_array_b), 
                axis=-1
            )
            
            # Ensure valid pixel range
            watermarked_image_array = np.clip(watermarked_image_array, 0, 255)
            
            return watermarked_image_array, svd_values

    def apply_dwt(self, image_array):
        """Apply Discrete Wavelet Transform"""
        coeffs = pywt.dwt2(image_array, 'haar')
        cA, (cH, cV, cD) = coeffs
        return coeffs, cA, cH, cV, cD

    def apply_idwt(self, coeffs):
        """Apply Inverse Discrete Wavelet Transform"""
        return pywt.idwt2(coeffs, 'haar')

    def save_watermarked_image(self):
        """Save watermarked image to disk"""
        if not self.watermarked_image:
            messagebox.showerror("Error", "No watermarked image to save")
            return
        
        save_path = filedialog.asksaveasfilename(
            defaultextension=".png", 
            filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"), ("All files", "*.*")]
        )
        
        if save_path:
            try:
                self.watermarked_image.save(save_path)
                self.status_bar.configure(text=f"Image saved to {save_path}")
                messagebox.showinfo("Success", "Watermarked image saved successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Error saving image: {str(e)}")

    def compare_images(self):
        """Compare original and watermarked images to detect tampering"""
        if not self.path_to_image or not self.compare_path_to_image:
            messagebox.showerror("Error", "Please upload both images first")
            return
        
        try:
            # Load original image
            original_image = Image.open(self.path_to_image)
            
            # Load comparison image
            compare_image = Image.open(self.compare_path_to_image)
            
            # Resize comparison image to match original if needed
            if original_image.size != compare_image.size:
                compare_image = ImageOps.fit(compare_image, original_image.size, Image.Resampling.LANCZOS)
            
            # Convert to grayscale for comparison
            orig_gray = original_image.convert('L')
            comp_gray = compare_image.convert('L')
            
            # Convert to arrays
            orig_array = np.array(orig_gray)
            comp_array = np.array(comp_gray)
            
            # Calculate difference and similarity
            difference = np.abs(orig_array - comp_array)
            total_diff = np.sum(difference)
            max_possible_diff = orig_array.size * 255
            similarity_percent = 100 - (total_diff / max_possible_diff * 100)
            
            # Create difference visualization (enhanced for visibility)
            diff_image = Image.fromarray(np.uint8(difference * 5))  # Multiply to enhance visibility
            self.display_image(diff_image, self.comparison_canvas, "Difference Image")
            
            # Determine authenticity
            threshold = 98.0  # 98% similarity threshold
            if similarity_percent >= threshold:
                status = "AUTHENTIC"
                message = f"The image appears to be authentic.\nSimilarity: {similarity_percent:.2f}%"
                icon = "info"
            else:
                status = "MODIFIED"
                message = f"The image has been modified.\nSimilarity: {similarity_percent:.2f}%"
                icon = "warning"
            
            # Show result
            getattr(messagebox, f"show{icon}")(status, message)
            self.status_bar.configure(text=f"Image comparison complete - {status}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error comparing images: {str(e)}")

    def extract_watermark(self):
        """Extract watermark from a watermarked image"""
        if not self.watermarked_image or not self.original_svd_values:
            messagebox.showerror("Error", "No watermarked image or original SVD values")
            return
        
        try:
            # Get alpha value
            alpha = float(self.alpha_slider.get())
            
            # Get watermarked image array
            watermarked_array = np.array(self.watermarked_image)
            
            # Check if grayscale or color
            if len(watermarked_array.shape) == 2:
                # Grayscale
                coeffs_w, cA_w, _, _, _ = self.apply_dwt(watermarked_array)
                
                # Get SVD components of watermarked image
                U_w, s_w, Vh_w = scipy.linalg.svd(cA_w, full_matrices=False)
                
                # Extract watermark
                original_s = self.original_svd_values['s']
                watermark_array = (s_w - original_s) / alpha
                
            else:
                # Color - use red channel
                red_channel = watermarked_array[:,:,0]
                coeffs_w, cA_w, _, _, _ = self.apply_dwt(red_channel)
                
                # Get SVD components
                U_w, s_w, Vh_w = scipy.linalg.svd(cA_w, full_matrices=False)
                
                # Extract watermark
                original_s = self.original_svd_values['red']['s']
                watermark_array = (s_w - original_s) / alpha
            
            # Try to convert binary array back to text
            try:
                # Threshold the extracted watermark
                binary_watermark = watermark_array > 0.5
                
                # Convert to ASCII
                char_indices = np.where(binary_watermark[:128])[0]  # Limit to prevent garbage
                
                if len(char_indices) > 0:
                    extracted_text = ''.join([chr(idx) for idx in char_indices])
                    # Clean up text (remove non-printable chars)
                    extracted_text = ''.join(c for c in extracted_text if c.isprintable())
                else:
                    extracted_text = "[No watermark detected]"
                
                # Display extracted text
                self.extracted_watermark = extracted_text
                extraction_label = customtkinter.CTkLabel(
                    self.tab_extraction, 
                    text=f"Extracted Watermark:\n\n{extracted_text}",
                    font=customtkinter.CTkFont(size=16)
                )
                
                # Clear previous content
                for widget in self.tab_extraction.winfo_children():
                    widget.destroy()
                
                extraction_label.pack(expand=True, pady=50)
                
                # Switch to extraction tab
                self.tabview.set("Extracted Watermark")
                
                # Update status
                self.status_bar.configure(text="Watermark extracted")
                
            except Exception as e:
                messagebox.showwarning("Warning", f"Could not convert extracted watermark to text: {str(e)}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error extracting watermark: {str(e)}")

    def change_appearance_mode(self, new_appearance_mode):
        """Change app appearance mode"""
        customtkinter.set_appearance_mode(new_appearance_mode)


if __name__ == "__main__":
    app = WatermarkingApp()
    app.mainloop()
