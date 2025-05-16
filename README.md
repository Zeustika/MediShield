# MediShield: DWT-SVD Image Watermarking App

MediShield is a Python desktop application for embedding and verifying digital watermarks in images using **DWT (Discrete Wavelet Transform)** and **SVD (Singular Value Decomposition)** techniques. This tool allows users to apply invisible watermark text to images, verify their authenticity, and extract embedded watermarks from modified images.




---

## 🚀 Features

- Upload and preview original and comparison images
- Embed custom watermark text with adjustable strength (alpha)
- Extract watermark from images
- Verify image authenticity using similarity metrics
- Clean and modern GUI using `CustomTkinter`
- Supports both grayscale and color images

---

## 🧠 Technologies Used

- Python
- Numpy
- PyWavelets (`pywt`)
- SciPy (for SVD)
- Pillow (PIL)
- CustomTkinter
- Tkinter GUI

---

## 📦 Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/Zeustika/MediShield.git
    cd MediShield
    ```

2. Install required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3. Run the app:
    ```bash
    python MediShield.py
    ```

---

## 📸 Usage

1. **Upload** an image (Step 1).
2. Enter the **watermark text** and adjust strength (Step 2).
3. Click **Apply Watermark** (Step 3).
4. Optionally **save** the watermarked image.
5. Upload another image to **verify** authenticity or **extract** watermark (Step 4).

---

## 📂 File Structure

- `MediShield.py` – Main application code
- `assets` – store image,etc
- `README.md` – Documentation
- `requirements.txt` – Dependencies

---

# 📸 ScreenShot
## V1
![image](https://github.com/user-attachments/assets/b35e13e6-2df9-4bb5-8f45-ee12953c0dd2)

![image](https://github.com/user-attachments/assets/a42909a5-087a-41cc-a59a-9a2e12f7aefd)

## V2(current)
![image](https://github.com/user-attachments/assets/28c9a3fd-4449-4b9d-ab5b-0d52b7469558)

![image](https://github.com/user-attachments/assets/ec5661f0-11a3-44a5-8d32-3f1235705418)

![image](https://github.com/user-attachments/assets/f9878ec3-10f4-4f99-8c26-e28606b0cdab)

![image](https://github.com/user-attachments/assets/c83a4ebe-0b31-4ba4-a14a-784eba951c35)


