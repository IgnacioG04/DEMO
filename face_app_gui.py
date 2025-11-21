import os
import cv2
import numpy as np
import threading
import time
import urllib.request
import requests
from pathlib import Path
from typing import Optional, Tuple
from tkinter import *
from tkinter import ttk, messagebox
from PIL import Image, ImageTk

class FaceRecognitionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Reconocimiento Facial")
        self.root.geometry("900x700")
        self.root.configure(bg='#f0f0f0')
        
        self.api_base_url = "http://localhost:8000"
        self.threshold = 0.6
        self.detection_count_threshold = 5
        self.detection_window = 2.0
        
        self.camera = None
        self.is_camera_active = False
        self.current_mode = None
        self.current_user_id = None
        self.last_frame = None
        self.detection_count = {}
        self.last_detection_time = {}
        
        self.check_api_connection()
        self.setup_ui()
    
    def check_api_connection(self):
        import time
        max_retries = 5
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                response = requests.get(f"{self.api_base_url}/users", timeout=2)
                if response.status_code == 200:
                    print("[OK] Conexión con API establecida")
                    return
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                else:
                    messagebox.showwarning("Advertencia", f"No se pudo conectar con la API en {self.api_base_url}\n\nEl servidor puede estar iniciando. Intenta nuevamente en unos segundos.\n\nError: {str(e)}")
    
    def setup_ui(self):
        title_label = Label(
            self.root, 
            text="🔐 Sistema de Reconocimiento Facial",
            font=('Arial', 20, 'bold'),
            bg='#f0f0f0',
            fg='#333'
        )
        title_label.pack(pady=20)
        
        button_frame = Frame(self.root, bg='#f0f0f0')
        button_frame.pack(pady=20)
        
        self.register_btn = Button(
            button_frame,
            text="📝 REGISTRAR NUEVO USUARIO",
            font=('Arial', 14, 'bold'),
            bg='#4CAF50',
            fg='white',
            padx=20,
            pady=15,
            cursor='hand2',
            command=self.start_register_mode
        )
        self.register_btn.pack(side=LEFT, padx=10)
        
        self.login_btn = Button(
            button_frame,
            text="🚪 INICIAR SESIÓN",
            font=('Arial', 14, 'bold'),
            bg='#2196F3',
            fg='white',
            padx=20,
            pady=15,
            cursor='hand2',
            command=self.start_login_mode
        )
        self.login_btn.pack(side=LEFT, padx=10)
        
        video_frame = Frame(self.root, bg='#333', relief=RAISED, borderwidth=2)
        video_frame.pack(pady=20, padx=20, fill=BOTH, expand=True)
        
        self.video_label = Label(
            video_frame,
            text="Presiona 'Registrar' o 'Iniciar Sesión' para activar la cámara",
            bg='#222',
            fg='white',
            font=('Arial', 12),
            width=80,
            height=20
        )
        self.video_label.pack(padx=10, pady=10, fill=BOTH, expand=True)
        
        info_frame = Frame(self.root, bg='#f0f0f0')
        info_frame.pack(pady=10, fill=X)
        
        self.status_label = Label(
            info_frame,
            text="Estado: Esperando acción...",
            font=('Arial', 12),
            bg='#f0f0f0',
            fg='#666'
        )
        self.status_label.pack()
        
        self.info_label = Label(
            info_frame,
            text="",
            font=('Arial', 10),
            bg='#f0f0f0',
            fg='#888'
        )
        self.info_label.pack()
        
        self.stop_btn = Button(
            self.root,
            text="⏹ DETENER CÁMARA",
            font=('Arial', 12),
            bg='#f44336',
            fg='white',
            padx=15,
            pady=10,
            cursor='hand2',
            command=self.stop_camera,
            state=DISABLED
        )
        self.stop_btn.pack(pady=10)
        
        self.capture_btn = Button(
            self.root,
            text="📸 CAPTURAR ROSTRO (o presiona ESPACIO)",
            font=('Arial', 12, 'bold'),
            bg='#FF9800',
            fg='white',
            padx=15,
            pady=10,
            cursor='hand2',
            command=self.capture_face,
            state=DISABLED
        )
        self.capture_btn.pack(pady=5)
        
        self.root.bind('<Key-space>', lambda e: self.capture_face() if self.current_mode == 'register' else None)
        self.root.focus_set()
    
    def start_register_mode(self):
        if self.is_camera_active:
            messagebox.showwarning("Cámara activa", "Detén la cámara antes de cambiar de modo")
            return
        
        user_id = self.get_user_id("Registrar Usuario", "Ingresa el ID de usuario (número):")
        if not user_id:
            return
        
        try:
            user_id_int = int(user_id)
        except ValueError:
            messagebox.showerror("Error", "El ID de usuario debe ser un número entero")
            return
        
        registered_users = self.get_registered_users()
        if user_id in registered_users:
            if not messagebox.askyesno("Usuario existente", 
                                      f"El usuario '{user_id}' ya existe. ¿Deseas intentar registrarlo de nuevo?"):
                return
        
        self.current_mode = 'register'
        self.current_user_id = user_id
        self.status_label.config(text=f"Modo: REGISTRO - Usuario: {user_id}", fg='#4CAF50')
        self.info_label.config(text="Mira a la cámara y presiona ESPACIO cuando estés listo para registrar tu rostro")
        self.start_camera()
    
    def start_login_mode(self):
        if self.is_camera_active:
            messagebox.showwarning("Cámara activa", "Detén la cámara antes de cambiar de modo")
            return
        
        registered_users = self.get_registered_users()
        if not registered_users:
            response = messagebox.askyesno(
                "Sin usuarios registrados",
                "No hay usuarios registrados.\n\n"
                "¿Deseas registrar un usuario ahora?"
            )
            if response:
                self.start_register_mode()
            return
        
        self.current_mode = 'login'
        self.detection_count = {}
        self.last_detection_time = {}
        self.status_label.config(text="Modo: LOGIN - Detectando rostro...", fg='#2196F3')
        self.info_label.config(text=f"Usuarios registrados: {len(registered_users)} | Detecta tu rostro {self.detection_count_threshold} veces para acceder")
        self.start_camera()
    
    def get_user_id(self, title, prompt):
        dialog = Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("400x150")
        dialog.configure(bg='#f0f0f0')
        dialog.transient(self.root)
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        result = {'id': None}
        
        Label(dialog, text=prompt, font=('Arial', 11), bg='#f0f0f0').pack(pady=10)
        
        entry = Entry(dialog, font=('Arial', 12), width=30)
        entry.pack(pady=10)
        entry.focus()
        
        def on_ok():
            user_id = entry.get().strip()
            if user_id:
                result['id'] = user_id
                dialog.destroy()
            else:
                messagebox.showwarning("Error", "Por favor ingresa un ID de usuario")
        
        def on_cancel():
            dialog.destroy()
        
        Button(dialog, text="OK", command=on_ok, bg='#4CAF50', fg='white', padx=20).pack(side=LEFT, padx=20, pady=10)
        Button(dialog, text="Cancelar", command=on_cancel, bg='#f44336', fg='white', padx=20).pack(side=RIGHT, padx=20, pady=10)
        
        entry.bind('<Return>', lambda e: on_ok())
        
        dialog.wait_window()
        return result['id']
    
    def start_camera(self):
        try:
            self.camera = cv2.VideoCapture(0)
            
            if not self.camera.isOpened():
                messagebox.showerror("Error", "No se pudo abrir la cámara.")
                return
            
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            self.is_camera_active = True
            self.register_btn.config(state=DISABLED)
            self.login_btn.config(state=DISABLED)
            self.stop_btn.config(state=NORMAL)
            
            if self.current_mode == 'register':
                self.capture_btn.config(state=NORMAL)
            else:
                self.capture_btn.config(state=DISABLED)
            
            self.video_thread = threading.Thread(target=self.update_video, daemon=True)
            self.video_thread.start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al iniciar la cámara: {str(e)}")
            self.is_camera_active = False
    
    def stop_camera(self):
        self.is_camera_active = False
        if self.camera:
            self.camera.release()
            self.camera = None
        
        self.register_btn.config(state=NORMAL)
        self.login_btn.config(state=NORMAL)
        self.stop_btn.config(state=DISABLED)
        self.capture_btn.config(state=DISABLED)
        
        self.video_label.config(image='', text="Cámara detenida")
        self.status_label.config(text="Estado: Esperando acción...", fg='#666')
        self.info_label.config(text="")
        self.current_mode = None
        self.current_user_id = None
        self.last_frame = None
    
    def update_video(self):
        while self.is_camera_active:
            ret, frame = self.camera.read()
            if not ret:
                break
            
            if self.current_mode == 'register':
                processed_frame = self.process_register_frame(frame)
            elif self.current_mode == 'login':
                processed_frame = self.process_login_frame(frame)
            else:
                processed_frame = frame
            
            self.last_frame = processed_frame.copy()
            
            frame_rgb = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
            frame_resized = cv2.resize(frame_rgb, (800, 600))
            
            img = Image.fromarray(frame_resized)
            imgtk = ImageTk.PhotoImage(image=img)
            
            self.video_label.config(image=imgtk, text="")
            self.video_label.image = imgtk
            
            time.sleep(0.03)
    
    def process_register_frame(self, frame):
        cv2.putText(frame, "Presiona ESPACIO para registrar tu rostro", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, "Mira directamente a la camara", 
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        return frame
    
    def process_login_frame(self, frame):
        current_time = time.time()
        
        detected_user = self.detect_and_recognize_face(frame)
        
        if detected_user:
            user_id, similarity, other_similarities = detected_user
            
            if user_id not in self.detection_count:
                self.detection_count[user_id] = 0
                self.last_detection_time[user_id] = current_time
            
            if current_time - self.last_detection_time[user_id] > self.detection_window:
                self.detection_count[user_id] = 0
            
            self.detection_count[user_id] += 1
            self.last_detection_time[user_id] = current_time
            
            count = self.detection_count[user_id]
            color = (0, 255, 0) if count >= self.detection_count_threshold else (0, 255, 255)
            
            y_offset = 30
            cv2.putText(frame, f"Usuario: {user_id}", 
                       (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
            y_offset += 30
            cv2.putText(frame, f"Similitud: {similarity:.2%}", 
                       (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            y_offset += 30
            cv2.putText(frame, f"Detecciones: {count}/{self.detection_count_threshold}", 
                       (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            
            if other_similarities and len(other_similarities) > 0:
                y_offset += 40
                cv2.putText(frame, "Rostros similares:", 
                           (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)
                
                max_others = min(3, len(other_similarities))
                for i in range(max_others):
                    other_user, other_sim = other_similarities[i]
                    if other_sim >= 0.05:
                        y_offset += 25
                        cv2.putText(frame, f"  {other_user}: {other_sim:.2%}", 
                                   (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)
            
            if count >= self.detection_count_threshold:
                cv2.putText(frame, "ACCESO CONCEDIDO!", 
                           (10, y_offset + 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 3)
                
                if count == self.detection_count_threshold:
                    self.root.after(500, lambda: self.grant_access(user_id, similarity, other_similarities))
        else:
            self.detection_count = {}
            self.last_detection_time = {}
            
            cv2.putText(frame, "Rostro no reconocido", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        return frame
    
    def detect_and_recognize_face(self, frame) -> Optional[Tuple[str, float, list]]:
        temp_file = None
        try:
            temp_file = "temp_frame_verify.jpg"
            cv2.imwrite(temp_file, frame)
            
            with open(temp_file, 'rb') as f:
                files = {'file': ('frame.jpg', f, 'image/jpeg')}
                response = requests.post(f"{self.api_base_url}/verify-frame", files=files, timeout=1)
            
            if os.path.exists(temp_file):
                os.remove(temp_file)
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            if not data.get('success') or not data.get('best_match'):
                return None
            
            best_match = data['best_match']
            threshold = data.get('threshold', self.threshold)
            
            if best_match['similarity'] < threshold:
                return None
            
            user_id = best_match['user_id']
            similarity = best_match['similarity']
            
            other_similarities = []
            for sim_data in data.get('other_similarities', []):
                if sim_data['similarity'] >= 0.05:
                    other_similarities.append((sim_data['user_id'], sim_data['similarity']))
            
            return (user_id, similarity, other_similarities)
            
        except requests.exceptions.Timeout:
            return None
        except Exception as e:
            print(f"[ERROR] Error en detección: {e}")
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
            return None
    
    def capture_face(self):
        if not self.is_camera_active or self.current_mode != 'register':
            return
        
        if self.last_frame is None:
            messagebox.showwarning("Error", "No hay frame disponible. Espera un momento.")
            return
        
        self.save_face(self.last_frame)
    
    def save_face(self, frame):
        temp_file = None
        try:
            self.status_label.config(text="Procesando rostro... Por favor espera...", fg='#FF9800')
            self.root.update()
            
            temp_file = "temp_frame_register.jpg"
            cv2.imwrite(temp_file, frame)
            
            user_id = self.current_user_id
            if not user_id:
                messagebox.showerror("Error", "No se pudo obtener el ID de usuario")
                return
            
            with open(temp_file, 'rb') as f:
                files = {'file': ('face.jpg', f, 'image/jpeg')}
                data = {'user_id': user_id}
                response = requests.post(f"{self.api_base_url}/register", files=files, data=data, timeout=10)
            
            if os.path.exists(temp_file):
                os.remove(temp_file)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    self.status_label.config(text=f"Usuario '{user_id}' registrado correctamente!", fg='#4CAF50')
                    messagebox.showinfo("Éxito", f"Usuario '{user_id}' registrado correctamente!")
                    self.stop_camera()
                else:
                    messagebox.showerror("Error", result.get('detail', 'Error desconocido'))
                    self.status_label.config(text="Error al registrar rostro.", fg='#f44336')
            else:
                error_msg = "Error desconocido"
                try:
                    error_data = response.json()
                    error_msg = error_data.get('detail', error_msg)
                except:
                    error_msg = f"Error HTTP {response.status_code}"
                
                messagebox.showerror("Error", f"Error al registrar rostro:\n{error_msg}")
                self.status_label.config(text="Error al registrar rostro.", fg='#f44336')
                
        except requests.exceptions.Timeout:
            messagebox.showerror("Error", "Tiempo de espera agotado. El servidor no respondió a tiempo.")
            self.status_label.config(text="Error: tiempo de espera agotado.", fg='#f44336')
        except Exception as e:
            error_msg = str(e)
            print(f"[ERROR] Error al registrar rostro: {error_msg}")
            messagebox.showerror("Error", f"Error al registrar rostro:\n{error_msg}")
            self.status_label.config(text="Error al registrar rostro.", fg='#f44336')
        finally:
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
    
    def grant_access(self, user_id, similarity, other_similarities=None):
        message = f"Bienvenido, {user_id}!\n\n"
        message += f"Similitud: {similarity:.2%}\n\n"
        
        if other_similarities and len(other_similarities) > 0:
            message += "Rostros similares:\n"
            max_others = min(3, len(other_similarities))
            for i in range(max_others):
                other_user, other_sim = other_similarities[i]
                if other_sim >= 0.05:
                    message += f"  • {other_user}: {other_sim:.2%}\n"
        
        message += "\nAcceso concedido exitosamente."
        
        messagebox.showinfo("Acceso Concedido", message)
        self.stop_camera()
    
    def get_registered_users(self):
        try:
            response = requests.get(f"{self.api_base_url}/users", timeout=2)
            if response.status_code == 200:
                data = response.json()
                return data.get('users', [])
            return []
        except Exception as e:
            print(f"[ERROR] Error al obtener usuarios: {e}")
            return []
    
    def __del__(self):
        self.stop_camera()

def main():
    root = Tk()
    app = FaceRecognitionApp(root)
    
    def on_closing():
        app.stop_camera()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
