import numpy as np
import pywt
from PIL import Image, ImageTk
from PIL import ImageOps
import scipy.linalg
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter
import os
import threading
import time

# Set tema dan mode tampilan
customtkinter.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("green")  # Themes: "blue", "green", "dark-blue"

class WatermarkingApp(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # Konfigurasi window utama
        self.title("MediShield")
        self.geometry(f"{1200}x750")
        self.minsize(900, 600)
        
        # Variabel untuk menyimpan data
        self.original_image = None
        self.watermarked_image = None
        self.comparison_image = None
        self.path_to_image = None
        self.compare_path_to_image = None
        self.extracted_watermark = None
        self.original_svd_values = {}  # Untuk menyimpan nilai SVD original

        # Buat frame utama dengan grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(0, weight=1)
        
        # Frame sidebar untuk kontrol
        self.sidebar_frame = customtkinter.CTkFrame(self, width=250, corner_radius=10)
        self.sidebar_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(14, weight=1)  # Untuk spacing
        
        # Frame utama untuk preview gambar
        self.main_frame = customtkinter.CTkFrame(self, corner_radius=10)
        self.main_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)
        
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
        self.tabview.grid(row=0, column=0, rowspan=2, padx=10, pady=10, sticky="nsew")
        
        # Create tabs
        self.tab_original = self.tabview.add("Original Image")
        self.tab_watermarked = self.tabview.add("Watermarked Image")
        self.tab_comparison = self.tabview.add("Comparison")
        self.tab_extraction = self.tabview.add("Extracted Watermark")
        
        # Configure tab layouts
        for tab in [self.tab_original, self.tab_watermarked, self.tab_comparison, self.tab_extraction]:
            tab.grid_columnconfigure(0, weight=1)
            tab.grid_rowconfigure(0, weight=1)
        
        # Image canvas for each tab
        self.original_canvas = customtkinter.CTkLabel(self.tab_original, text="Upload an image first")
        self.original_canvas.grid(row=0, column=0, padx=20, pady=20)
        
        self.watermarked_canvas = customtkinter.CTkLabel(self.tab_watermarked, text="Process an image first")
        self.watermarked_canvas.grid(row=0, column=0, padx=20, pady=20)
        
        self.comparison_canvas = customtkinter.CTkLabel(self.tab_comparison, text="Upload a comparison image first")
        self.comparison_canvas.grid(row=0, column=0, padx=20, pady=20)
        
        self.extraction_canvas = customtkinter.CTkLabel(self.tab_extraction, text="Extract watermark first")
        self.extraction_canvas.grid(row=0, column=0, padx=20, pady=20)
        
        # Progress bar (hidden initially)
        self.progress_frame = customtkinter.CTkFrame(self.main_frame)
        self.progress_frame.grid(row=1, column=0, padx=10, pady=10, sticky="sew")
        self.progress_frame.grid_remove()  # Hide initially
        
        self.progress_label = customtkinter.CTkLabel(self.progress_frame, text="Processing...")
        self.progress_label.pack(pady=(10, 0))
        
        self.progress_bar = customtkinter.CTkProgressBar(self.progress_frame)
        self.progress_bar.pack(fill="x", padx=20, pady=10)
        self.progress_bar.set(0)
        
        # Status bar
        self.status_bar = customtkinter.CTkLabel(self, text="Ready", anchor="w")
        self.status_bar.grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 5), sticky="sw")

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
            canvas.image = photo  # Keep a reference to prevent garbage collection
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