import os
import requests
import json
import time
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
import threading
from typing import List, Optional
import customtkinter as ctk
from PIL import Image, ImageTk
import io
import base64

# Set appearance mode and color theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class ContentKillerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configure window
        self.title("Content Killer - AI Image Generator")
        self.geometry("900x700")
        self.minsize(800, 600)

        # Variables
        self.api_key = tk.StringVar()
        self.source_images: List[str] = []
        self.reference_folder: Optional[str] = None
        self.output_folder: Optional[str] = None
        self.is_processing = False

        # Setup UI
        self.setup_ui()

    def setup_ui(self):
        # Main container with padding - use scrollable frame
        main_frame = ctk.CTkScrollableFrame(self, corner_radius=0, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=15, pady=10)

        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="Content Killer",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(0, 5))

        subtitle_label = ctk.CTkLabel(
            main_frame,
            text="AI Image Generator with Seedream V4",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        subtitle_label.pack(pady=(0, 10))

        # API Key Section
        api_frame = ctk.CTkFrame(main_frame, corner_radius=10)
        api_frame.pack(fill="x", pady=(0, 8))

        api_label = ctk.CTkLabel(
            api_frame,
            text="WaveSpeed API Key:",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        api_label.pack(anchor="w", padx=12, pady=(10, 3))

        self.api_entry = ctk.CTkEntry(
            api_frame,
            textvariable=self.api_key,
            placeholder_text="Enter your WaveSpeed API key here...",
            show="*",
            height=32,
            font=ctk.CTkFont(size=11)
        )
        self.api_entry.pack(fill="x", padx=12, pady=(0, 10))

        # Source Images Section
        source_frame = ctk.CTkFrame(main_frame, corner_radius=10)
        source_frame.pack(fill="x", pady=(0, 8))

        source_label = ctk.CTkLabel(
            source_frame,
            text="Source Images (Face & Body):",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        source_label.pack(anchor="w", padx=12, pady=(10, 3))

        self.source_display = ctk.CTkTextbox(
            source_frame,
            height=50,
            font=ctk.CTkFont(size=10),
            state="disabled"
        )
        self.source_display.pack(fill="x", padx=12, pady=(0, 5))

        source_btn = ctk.CTkButton(
            source_frame,
            text="Select Source Images",
            command=self.select_source_images,
            height=32,
            font=ctk.CTkFont(size=11, weight="bold"),
            corner_radius=8
        )
        source_btn.pack(fill="x", padx=12, pady=(0, 10))

        # Reference Folder Section
        reference_frame = ctk.CTkFrame(main_frame, corner_radius=10)
        reference_frame.pack(fill="x", pady=(0, 8))

        reference_label = ctk.CTkLabel(
            reference_frame,
            text="Reference Images Folder (Outfits & Poses):",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        reference_label.pack(anchor="w", padx=12, pady=(10, 3))

        self.reference_display = ctk.CTkLabel(
            reference_frame,
            text="No folder selected",
            font=ctk.CTkFont(size=10),
            text_color="gray",
            anchor="w"
        )
        self.reference_display.pack(fill="x", padx=12, pady=(0, 5))

        reference_btn = ctk.CTkButton(
            reference_frame,
            text="Select Reference Folder",
            command=self.select_reference_folder,
            height=32,
            font=ctk.CTkFont(size=11, weight="bold"),
            corner_radius=8
        )
        reference_btn.pack(fill="x", padx=12, pady=(0, 10))

        # Output Folder Section
        output_frame = ctk.CTkFrame(main_frame, corner_radius=10)
        output_frame.pack(fill="x", pady=(0, 8))

        output_label = ctk.CTkLabel(
            output_frame,
            text="Output Folder:",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        output_label.pack(anchor="w", padx=12, pady=(10, 3))

        self.output_display = ctk.CTkLabel(
            output_frame,
            text="No folder selected",
            font=ctk.CTkFont(size=10),
            text_color="gray",
            anchor="w"
        )
        self.output_display.pack(fill="x", padx=12, pady=(0, 5))

        output_btn = ctk.CTkButton(
            output_frame,
            text="Select Output Folder",
            command=self.select_output_folder,
            height=32,
            font=ctk.CTkFont(size=11, weight="bold"),
            corner_radius=8
        )
        output_btn.pack(fill="x", padx=12, pady=(0, 10))

        # Generate Button
        self.generate_btn = ctk.CTkButton(
            main_frame,
            text="Generate Images",
            command=self.start_generation,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            corner_radius=10,
            fg_color="#28a745",
            hover_color="#218838"
        )
        self.generate_btn.pack(fill="x", pady=(0, 8))

        # Progress Section
        progress_frame = ctk.CTkFrame(main_frame, corner_radius=10)
        progress_frame.pack(fill="x", pady=(0, 0))

        progress_label = ctk.CTkLabel(
            progress_frame,
            text="Progress:",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        progress_label.pack(anchor="w", padx=12, pady=(10, 3))

        self.progress_bar = ctk.CTkProgressBar(progress_frame, height=15)
        self.progress_bar.pack(fill="x", padx=12, pady=(0, 5))
        self.progress_bar.set(0)

        self.status_display = ctk.CTkTextbox(
            progress_frame,
            height=80,
            font=ctk.CTkFont(size=10),
            state="disabled"
        )
        self.status_display.pack(fill="x", padx=12, pady=(0, 10))

    def select_source_images(self):
        files = filedialog.askopenfilenames(
            title="Select Source Images",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.webp *.bmp"),
                ("All files", "*.*")
            ]
        )
        if files:
            self.source_images = list(files)
            self.source_display.configure(state="normal")
            self.source_display.delete("1.0", "end")
            self.source_display.insert("1.0", f"Selected {len(files)} images:\n")
            for i, file in enumerate(files, 1):
                self.source_display.insert("end", f"{i}. {Path(file).name}\n")
            self.source_display.configure(state="disabled")
            self.log_status(f"Selected {len(files)} source images")

    def select_reference_folder(self):
        folder = filedialog.askdirectory(title="Select Reference Images Folder")
        if folder:
            self.reference_folder = folder
            self.reference_display.configure(text=folder, text_color="white")

            # Count image files
            image_extensions = {'.png', '.jpg', '.jpeg', '.webp', '.bmp'}
            image_count = sum(1 for f in Path(folder).iterdir()
                            if f.suffix.lower() in image_extensions)
            self.log_status(f"Selected reference folder with {image_count} images")

    def select_output_folder(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_folder = folder
            self.output_display.configure(text=folder, text_color="white")
            self.log_status(f"Output folder set to: {folder}")

    def log_status(self, message: str):
        self.status_display.configure(state="normal")
        timestamp = time.strftime("%H:%M:%S")
        self.status_display.insert("end", f"[{timestamp}] {message}\n")
        self.status_display.see("end")
        self.status_display.configure(state="disabled")

    def validate_inputs(self) -> bool:
        if not self.api_key.get():
            messagebox.showerror("Error", "Please enter your WaveSpeed API key")
            return False

        if not self.source_images:
            messagebox.showerror("Error", "Please select source images")
            return False

        if not self.reference_folder:
            messagebox.showerror("Error", "Please select a reference images folder")
            return False

        if not self.output_folder:
            messagebox.showerror("Error", "Please select an output folder")
            return False

        return True

    def start_generation(self):
        if not self.validate_inputs():
            return

        if self.is_processing:
            messagebox.showwarning("Warning", "Processing is already in progress")
            return

        # Start processing in a separate thread
        self.is_processing = True
        self.generate_btn.configure(state="disabled", text="Processing...")

        thread = threading.Thread(target=self.process_images, daemon=True)
        thread.start()

    def process_images(self):
        try:
            # Get reference images
            image_extensions = {'.png', '.jpg', '.jpeg', '.webp', '.bmp'}
            reference_images = [
                str(f) for f in Path(self.reference_folder).iterdir()
                if f.suffix.lower() in image_extensions
            ]

            if not reference_images:
                self.after(0, lambda: messagebox.showerror(
                    "Error", "No images found in reference folder"
                ))
                return

            self.after(0, lambda: self.log_status(
                f"Starting generation for {len(reference_images)} reference images"
            ))

            # Upload source images first
            self.after(0, lambda: self.log_status("Uploading source images..."))
            source_urls = self.upload_images(self.source_images)

            if not source_urls:
                self.after(0, lambda: messagebox.showerror(
                    "Error", "Failed to upload source images"
                ))
                return

            total = len(reference_images)

            for idx, ref_image_path in enumerate(reference_images, 1):
                if not self.is_processing:
                    self.after(0, lambda: self.log_status("Processing cancelled"))
                    break

                self.after(0, lambda i=idx, t=total: self.progress_bar.set(i / t))

                ref_name = Path(ref_image_path).name
                self.after(0, lambda name=ref_name, i=idx, t=total: self.log_status(
                    f"Processing {i}/{t}: {name}"
                ))

                # Upload reference image
                ref_urls = self.upload_images([ref_image_path])
                if not ref_urls:
                    self.after(0, lambda name=ref_name: self.log_status(
                        f"Failed to upload reference image: {name}"
                    ))
                    continue

                # Generate image
                result_url = self.generate_image(source_urls, ref_urls[0])

                if result_url:
                    # Download and save the result
                    output_path = Path(self.output_folder) / f"generated_{ref_name}"
                    if self.download_image(result_url, str(output_path)):
                        self.after(0, lambda name=ref_name: self.log_status(
                            f"Successfully generated: {name}"
                        ))
                    else:
                        self.after(0, lambda name=ref_name: self.log_status(
                            f"Failed to download result for: {name}"
                        ))
                else:
                    self.after(0, lambda name=ref_name: self.log_status(
                        f"Failed to generate image for: {name}"
                    ))

                # Small delay between requests
                time.sleep(1)

            self.after(0, lambda: self.log_status("All processing complete!"))
            self.after(0, lambda: messagebox.showinfo(
                "Success", "Image generation complete!"
            ))

        except Exception as e:
            self.after(0, lambda: self.log_status(f"Error: {str(e)}"))
            self.after(0, lambda: messagebox.showerror("Error", str(e)))

        finally:
            self.is_processing = False
            self.after(0, lambda: self.generate_btn.configure(
                state="normal", text="Generate Images"
            ))
            self.after(0, lambda: self.progress_bar.set(0))

    def upload_images(self, image_paths: List[str]) -> List[str]:
        """Convert images to base64 data URLs that the API can accept."""
        data_urls = []

        for image_path in image_paths:
            try:
                # Read the image file
                with open(image_path, 'rb') as image_file:
                    image_data = image_file.read()

                # Encode to base64
                encoded_string = base64.b64encode(image_data).decode('utf-8')

                # Determine MIME type from file extension
                ext = Path(image_path).suffix.lower()
                mime_types = {
                    '.png': 'image/png',
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.webp': 'image/webp',
                    '.bmp': 'image/bmp'
                }
                mime_type = mime_types.get(ext, 'image/jpeg')

                # Create data URL
                data_url = f"data:{mime_type};base64,{encoded_string}"
                data_urls.append(data_url)

            except Exception as e:
                self.after(0, lambda p=image_path, err=str(e): self.log_status(
                    f"Failed to encode {Path(p).name}: {err}"
                ))
                return []

        return data_urls

    def generate_image(self, source_urls: List[str], reference_url: str) -> Optional[str]:
        """Generate image using WaveSpeed API"""
        try:
            url = "https://api.wavespeed.ai/api/v3/bytedance/seedream-v4/edit"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key.get()}",
            }

            # Combine source images and reference image
            all_images = source_urls + [reference_url]

            payload = {
                "size": "2227*3183",
                "images": all_images,
                "prompt": f"Use the first {len(source_urls)} images as a source for the face and body. Use the last image as the source for the outfit, background, and pose",
                "enable_sync_mode": False,
                "enable_base64_output": False,
                "model_id": "bytedance/seedream-v4/edit"
            }

            response = requests.post(url, headers=headers, data=json.dumps(payload))

            if response.status_code == 200:
                result = response.json()["data"]
                request_id = result["id"]

                # Poll for results
                result_url = f"https://api.wavespeed.ai/api/v3/predictions/{request_id}/result"
                headers = {"Authorization": f"Bearer {self.api_key.get()}"}

                max_attempts = 600  # 60 seconds max wait
                for _ in range(max_attempts):
                    response = requests.get(result_url, headers=headers)
                    if response.status_code == 200:
                        result = response.json()["data"]
                        status = result["status"]

                        if status == "completed":
                            return result["outputs"][0]
                        elif status == "failed":
                            self.after(0, lambda: self.log_status(
                                f"Task failed: {result.get('error')}"
                            ))
                            return None

                    time.sleep(0.1)

                self.after(0, lambda: self.log_status("Request timed out"))
                return None
            else:
                self.after(0, lambda: self.log_status(
                    f"API Error: {response.status_code}, {response.text}"
                ))
                return None

        except Exception as e:
            self.after(0, lambda: self.log_status(f"Generation error: {str(e)}"))
            return None

    def download_image(self, url: str, output_path: str) -> bool:
        """Download image from URL and save to disk"""
        try:
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                return True
            return False
        except Exception as e:
            self.after(0, lambda: self.log_status(f"Download error: {str(e)}"))
            return False


def main():
    app = ContentKillerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
