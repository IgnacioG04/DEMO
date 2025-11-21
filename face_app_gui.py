"""
Sistema de Reconocimiento Facial - Aplicación de Escritorio
Aplicación GUI para registro y login con reconocimiento facial usando cámara
"""
import os
import cv2
import numpy as np
import json
import threading
import time
import urllib.request
from pathlib import Path
from typing import Optional, Tuple, Dict
from tkinter import *
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from deepface import DeepFace

class FaceRecognitionApp:
    """
    Aplicación GUI para reconocimiento facial
    """
    
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Reconocimiento Facial")
        self.root.geometry("900x700")
        self.root.configure(bg='#f0f0f0')
        
        # Configuración
        self.threshold = 0.6  # Umbral de similitud
        self.detection_count_threshold = 5  # Número de detecciones antes de validar
        self.faces_dir = Path("registered_faces")
        self.faces_dir.mkdir(exist_ok=True)
        
        # Variables
        self.camera = None
        self.is_camera_active = False
        self.current_mode = None  # 'register' o 'login'
        self.current_user_name = None  # Nombre del usuario en modo registro
        self.last_frame = None  # Último frame capturado
        self.detection_count = {}  # Contador de detecciones por usuario
        self.last_detection_time = {}  # Tiempo de última detección
        self.detection_window = 2.0  # Ventana de tiempo para contar detecciones (segundos)
        
        # DeepFace config
        self.model_name = 'VGG-Face'
        self.backend = 'opencv'
        
        # Verificar y descargar modelos si es necesario
        self.check_and_download_models()
        
        # Procesar imágenes existentes en la carpeta
        self.process_existing_images()
        
        # UI
        self.setup_ui()
        
    def check_and_download_models(self):
        """Verifica y descarga modelos de DeepFace si es necesario"""
        try:
            # Crear directorio de modelos si no existe
            model_dir = Path.home() / ".deepface" / "weights"
            model_dir.mkdir(parents=True, exist_ok=True)
            
            # Verificar si el modelo VGG-Face existe
            model_file = model_dir / "vgg_face_weights.h5"
            
            if not model_file.exists():
                print("[INFO] Modelo VGG-Face no encontrado.")
                print("[INFO] El modelo se descargará automáticamente la primera vez que se use.")
                print("[INFO] Alternativamente, puedes ejecutar: python download_model.py")
                
                response = messagebox.askyesno(
                    "Modelo no encontrado",
                    "El modelo de reconocimiento facial no está instalado.\n\n"
                    "¿Deseas descargarlo ahora? (Esto puede tardar varios minutos)\n\n"
                    "Si eliges 'No', el modelo se descargará automáticamente\n"
                    "la primera vez que registres un rostro.\n\n"
                    "Alternativamente, puedes ejecutar: python download_model.py"
                )
                
                if response:
                    # Intentar descargar ahora
                    self.download_model_manually()
                    
        except Exception as e:
            print(f"[WARN] Error al verificar modelos: {e}")
    
    def download_model_manually(self):
        """Descarga el modelo manualmente"""
        try:
            import urllib.request
            
            model_url = "https://github.com/serengil/deepface_models/releases/download/v1.0/vgg_face_weights.h5"
            model_dir = Path.home() / ".deepface" / "weights"
            model_dir.mkdir(parents=True, exist_ok=True)
            model_file = model_dir / "vgg_face_weights.h5"
            
            # Crear ventana de progreso
            progress_window = Toplevel(self.root)
            progress_window.title("Descargando modelo...")
            progress_window.geometry("500x150")
            progress_window.transient(self.root)
            progress_window.grab_set()
            
            # Centrar ventana
            progress_window.update_idletasks()
            x = (progress_window.winfo_screenwidth() // 2) - (progress_window.winfo_width() // 2)
            y = (progress_window.winfo_screenheight() // 2) - (progress_window.winfo_height() // 2)
            progress_window.geometry(f"+{x}+{y}")
            
            Label(progress_window, text="Descargando modelo VGG-Face...", 
                  font=('Arial', 12), pady=20).pack()
            
            progress_var = StringVar(value="Iniciando descarga...")
            progress_label = Label(progress_window, textvariable=progress_var, 
                                  font=('Arial', 10), pady=10)
            progress_label.pack()
            
            def download_with_progress():
                try:
                    def update_progress(block_num, block_size, total_size):
                        if total_size > 0:
                            percent = min(block_num * block_size * 100 / total_size, 100)
                            downloaded_mb = block_num * block_size / (1024 * 1024)
                            total_mb = total_size / (1024 * 1024)
                            progress_var.set(f"Descargando: {percent:.1f}% - {downloaded_mb:.1f} MB / {total_mb:.1f} MB")
                            progress_window.update()
                    
                    urllib.request.urlretrieve(model_url, model_file, reporthook=update_progress)
                    progress_var.set("¡Descarga completada!")
                    progress_window.after(1000, progress_window.destroy)
                    messagebox.showinfo("Éxito", "Modelo descargado correctamente!")
                    
                except Exception as e:
                    progress_window.destroy()
                    messagebox.showerror(
                        "Error de descarga",
                        f"No se pudo descargar el modelo automáticamente.\n\n"
                        f"Error: {str(e)}\n\n"
                        f"Por favor, ejecuta manualmente:\n"
                        f"python download_model.py"
                    )
            
            # Iniciar descarga en thread separado
            download_thread = threading.Thread(target=download_with_progress, daemon=True)
            download_thread.start()
            
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"No se pudo iniciar la descarga automática.\n\n"
                f"Por favor, ejecuta manualmente:\n"
                f"python download_model.py\n\n"
                f"Error: {str(e)}"
            )
        
    def setup_ui(self):
        """Configura la interfaz de usuario"""
        # Título
        title_label = Label(
            self.root, 
            text="🔐 Sistema de Reconocimiento Facial",
            font=('Arial', 20, 'bold'),
            bg='#f0f0f0',
            fg='#333'
        )
        title_label.pack(pady=20)
        
        # Frame para botones principales
        button_frame = Frame(self.root, bg='#f0f0f0')
        button_frame.pack(pady=20)
        
        # Botón de Registro
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
        
        # Botón de Login
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
        
        # Frame para video
        video_frame = Frame(self.root, bg='#333', relief=RAISED, borderwidth=2)
        video_frame.pack(pady=20, padx=20, fill=BOTH, expand=True)
        
        # Label para mostrar video
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
        
        # Frame para información
        info_frame = Frame(self.root, bg='#f0f0f0')
        info_frame.pack(pady=10, fill=X)
        
        # Label de estado
        self.status_label = Label(
            info_frame,
            text="Estado: Esperando acción...",
            font=('Arial', 12),
            bg='#f0f0f0',
            fg='#666'
        )
        self.status_label.pack()
        
        # Label de información
        self.info_label = Label(
            info_frame,
            text="",
            font=('Arial', 10),
            bg='#f0f0f0',
            fg='#888'
        )
        self.info_label.pack()
        
        # Botón de detener cámara
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
        
        # Botón de captura (para registro)
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
        
        # Enlazar tecla ESPACIO
        self.root.bind('<Key-space>', lambda e: self.capture_face() if self.current_mode == 'register' else None)
        self.root.focus_set()
        
    def start_register_mode(self):
        """Inicia el modo de registro"""
        if self.is_camera_active:
            messagebox.showwarning("Cámara activa", "Detén la cámara antes de cambiar de modo")
            return
            
        # Pedir nombre de usuario
        user_name = self.get_user_name("Registrar Usuario", "Ingresa tu nombre de usuario:")
        if not user_name:
            return
        
        # Verificar si el usuario ya existe
        if (self.faces_dir / f"{user_name}.npy").exists():
            if not messagebox.askyesno("Usuario existente", 
                                      f"El usuario '{user_name}' ya existe. ¿Deseas reemplazarlo?"):
                return
        
        self.current_mode = 'register'
        self.current_user_name = user_name  # Guardar nombre de usuario
        self.status_label.config(text=f"Modo: REGISTRO - Usuario: {user_name}", fg='#4CAF50')
        self.info_label.config(text="Mira a la cámara y presiona ESPACIO cuando estés listo para registrar tu rostro")
        self.start_camera()
        
    def start_login_mode(self):
        """Inicia el modo de login"""
        if self.is_camera_active:
            messagebox.showwarning("Cámara activa", "Detén la cámara antes de cambiar de modo")
            return
        
        # Procesar imágenes existentes antes de verificar usuarios
        self.process_existing_images()
        
        # Verificar que haya usuarios registrados
        registered_users = self.get_registered_users()
        if not registered_users:
            response = messagebox.askyesno(
                "Sin usuarios registrados",
                "No hay usuarios registrados.\n\n"
                "Puedes:\n"
                "1. Registrar un usuario con la cámara\n"
                "2. Agregar imágenes directamente en la carpeta 'registered_faces/'\n\n"
                "¿Deseas registrar un usuario ahora con la cámara?"
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
        
    def get_user_name(self, title, prompt):
        """Obtiene el nombre de usuario mediante un diálogo"""
        dialog = Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("400x150")
        dialog.configure(bg='#f0f0f0')
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Centrar ventana
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        result = {'name': None}
        
        Label(dialog, text=prompt, font=('Arial', 11), bg='#f0f0f0').pack(pady=10)
        
        entry = Entry(dialog, font=('Arial', 12), width=30)
        entry.pack(pady=10)
        entry.focus()
        
        def on_ok():
            name = entry.get().strip()
            if name:
                result['name'] = name
                dialog.destroy()
            else:
                messagebox.showwarning("Error", "Por favor ingresa un nombre de usuario")
        
        def on_cancel():
            dialog.destroy()
        
        Button(dialog, text="OK", command=on_ok, bg='#4CAF50', fg='white', padx=20).pack(side=LEFT, padx=20, pady=10)
        Button(dialog, text="Cancelar", command=on_cancel, bg='#f44336', fg='white', padx=20).pack(side=RIGHT, padx=20, pady=10)
        
        entry.bind('<Return>', lambda e: on_ok())
        
        dialog.wait_window()
        return result['name']
        
    def start_camera(self):
        """Inicia la captura de video de la cámara"""
        try:
            # Intentar abrir la cámara (Iriun Webcam generalmente está en índice 0)
            self.camera = cv2.VideoCapture(0)
            
            if not self.camera.isOpened():
                messagebox.showerror("Error", "No se pudo abrir la cámara. Verifica que Iriun Webcam esté conectado.")
                return
            
            # Configurar resolución
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            self.is_camera_active = True
            self.register_btn.config(state=DISABLED)
            self.login_btn.config(state=DISABLED)
            self.stop_btn.config(state=NORMAL)
            
            # Mostrar botón de captura solo en modo registro
            if self.current_mode == 'register':
                self.capture_btn.config(state=NORMAL)
            else:
                self.capture_btn.config(state=DISABLED)
            
            # Iniciar thread de video
            self.video_thread = threading.Thread(target=self.update_video, daemon=True)
            self.video_thread.start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al iniciar la cámara: {str(e)}")
            self.is_camera_active = False
            
    def stop_camera(self):
        """Detiene la captura de video"""
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
        self.current_user_name = None
        self.last_frame = None
        
    def update_video(self):
        """Actualiza el video frame"""
        while self.is_camera_active:
            ret, frame = self.camera.read()
            if not ret:
                break
                
            # Procesar frame según el modo
            if self.current_mode == 'register':
                processed_frame = self.process_register_frame(frame)
            elif self.current_mode == 'login':
                processed_frame = self.process_login_frame(frame)
            else:
                processed_frame = frame
            
            # Guardar último frame para captura (antes de procesar)
            self.last_frame = processed_frame.copy()
            
            # Convertir a RGB para tkinter
            frame_rgb = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
            frame_resized = cv2.resize(frame_rgb, (800, 600))
            
            # Convertir a PhotoImage
            img = Image.fromarray(frame_resized)
            imgtk = ImageTk.PhotoImage(image=img)
            
            # Actualizar label
            self.video_label.config(image=imgtk, text="")
            self.video_label.image = imgtk
            
            time.sleep(0.03)  # ~30 FPS
            
    def process_register_frame(self, frame):
        """Procesa el frame en modo registro"""
        # Dibujar instrucciones
        cv2.putText(frame, "Presiona ESPACIO para registrar tu rostro", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, "Mira directamente a la camara", 
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        return frame
        
    def process_login_frame(self, frame):
        """Procesa el frame en modo login"""
        current_time = time.time()
        
        # Detectar rostro y comparar
        detected_user = self.detect_and_recognize_face(frame)
        
        if detected_user:
            # detected_user ahora es: (user_id, similarity, other_similarities)
            user_id, similarity, other_similarities = detected_user
            
            # Actualizar contador
            if user_id not in self.detection_count:
                self.detection_count[user_id] = 0
                self.last_detection_time[user_id] = current_time
            
            # Resetear contador si pasó mucho tiempo desde la última detección
            if current_time - self.last_detection_time[user_id] > self.detection_window:
                self.detection_count[user_id] = 0
            
            # Incrementar contador si es la misma persona
            self.detection_count[user_id] += 1
            self.last_detection_time[user_id] = current_time
            
            # Dibujar información
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
            
            # Mostrar otras similitudes en el video (máximo 3)
            if other_similarities and len(other_similarities) > 0:
                y_offset += 40
                cv2.putText(frame, "Rostros similares:", 
                           (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)
                
                max_others = min(3, len(other_similarities))
                for i in range(max_others):
                    other_user, other_sim = other_similarities[i]
                    # Solo mostrar si la similitud es mayor a 0.05% (5%)
                    if other_sim >= 0.05:
                        y_offset += 25
                        cv2.putText(frame, f"  {other_user}: {other_sim:.2%}", 
                                   (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)
            
            # Validar acceso si alcanzó el umbral
            if count >= self.detection_count_threshold:
                cv2.putText(frame, "ACCESO CONCEDIDO!", 
                           (10, y_offset + 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 3)
                
                # Conceder acceso después de un momento (solo una vez)
                if count == self.detection_count_threshold:
                    self.root.after(500, lambda: self.grant_access(user_id, similarity, other_similarities))
        else:
            # Resetear contadores si no se detecta rostro
            self.detection_count = {}
            self.last_detection_time = {}
            
            cv2.putText(frame, "Rostro no reconocido", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        return frame
        
    def detect_and_recognize_face(self, frame) -> Optional[Tuple[str, float, list]]:
        """Detecta y reconoce el rostro en el frame
        
        Returns:
            Tuple (mejor_match, mejor_similarity, otras_similitudes) o None
            otras_similitudes es una lista de (usuario, similitud) ordenada descendente
        """
        temp_file = None
        try:
            # Guardar frame temporal
            temp_file = "temp_frame.jpg"
            cv2.imwrite(temp_file, frame)
            
            # Extraer embedding del frame
            try:
                embedding_obj = DeepFace.represent(
                    img_path=temp_file,
                    model_name=self.model_name,
                    detector_backend=self.backend,
                    enforce_detection=False
                )
            except Exception as model_error:
                # Si hay error con el modelo, no mostrar error en cada frame
                # Solo imprimir en consola
                error_msg = str(model_error)
                if "downloading" not in error_msg.lower() and "download" not in error_msg.lower():
                    print(f"[WARN] Error en detección: {error_msg}")
                return None
            
            if len(embedding_obj) == 0:
                return None
            
            current_embedding = np.array(embedding_obj[0]['embedding'])
            
            # Comparar con todos los usuarios registrados
            similarities = []  # Lista de (usuario, similitud)
            
            for user_file in self.faces_dir.glob("*.npy"):
                stored_embedding = np.load(user_file)
                
                # Calcular similitud coseno
                similarity = self.calculate_similarity(current_embedding, stored_embedding)
                
                similarities.append((user_file.stem, similarity))
            
            # Ordenar por similitud descendente
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            # Limpiar archivo temporal
            if temp_file and os.path.exists(temp_file):
                os.remove(temp_file)
            
            if not similarities:
                return None
            
            # Obtener mejor match
            best_match, best_similarity = similarities[0]
            
            # Si la mejor similitud supera el umbral, retornar con otras similitudes
            if best_similarity >= self.threshold:
                # Obtener otras similitudes (excluyendo la principal)
                other_similarities = similarities[1:]  # Todas menos la primera
                return (best_match, best_similarity, other_similarities)
            
            return None
            
        except Exception as e:
            print(f"[ERROR] Error en detección: {e}")
            # Limpiar archivo temporal en caso de error
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
            return None
            
    def calculate_similarity(self, embedding1, embedding2):
        """Calcula similitud coseno entre embeddings"""
        embedding1_norm = embedding1 / (np.linalg.norm(embedding1) + 1e-10)
        embedding2_norm = embedding2 / (np.linalg.norm(embedding2) + 1e-10)
        return float(np.dot(embedding1_norm, embedding2_norm))
        
    def capture_face(self):
        """Captura el rostro actual para registro"""
        if not self.is_camera_active or self.current_mode != 'register':
            return
            
        if self.last_frame is None:
            messagebox.showwarning("Error", "No hay frame disponible. Espera un momento.")
            return
            
        self.save_face(self.last_frame)
        
    def save_face(self, frame):
        """Guarda el rostro en modo registro"""
        temp_file = None
        try:
            # Mostrar mensaje de carga
            self.status_label.config(text="Procesando rostro... Por favor espera...", fg='#FF9800')
            self.root.update()
            
            # Guardar frame temporal
            temp_file = "temp_frame.jpg"
            cv2.imwrite(temp_file, frame)
            
            # Extraer embedding (esto descargará el modelo si es necesario)
            try:
                embedding_obj = DeepFace.represent(
                    img_path=temp_file,
                    model_name=self.model_name,
                    detector_backend=self.backend,
                    enforce_detection=False
                )
            except Exception as model_error:
                # Si hay error con el modelo, intentar descargarlo manualmente
                error_msg = str(model_error)
                if "downloading" in error_msg.lower() or "download" in error_msg.lower():
                    messagebox.showerror(
                        "Error de descarga",
                        f"No se pudo descargar el modelo automáticamente.\n\n"
                        f"Error: {error_msg}\n\n"
                        f"Por favor:\n"
                        f"1. Verifica tu conexión a internet\n"
                        f"2. Intenta nuevamente (el modelo se descargará automáticamente)\n"
                        f"3. O descarga manualmente desde:\n"
                        f"   https://github.com/serengil/deepface_models/releases/download/v1.0/vgg_face_weights.h5\n"
                        f"   y guárdalo en: C:\\Users\\PC\\.deepface\\weights\\vgg_face_weights.h5"
                    )
                else:
                    raise
                return
            
            if len(embedding_obj) == 0:
                messagebox.showwarning("Error", "No se detectó ningún rostro en el frame")
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                return
            
            # Obtener nombre de usuario
            user_name = self.current_user_name
            if not user_name:
                messagebox.showerror("Error", "No se pudo obtener el nombre de usuario")
                return
            
            # Guardar embedding
            embedding = np.array(embedding_obj[0]['embedding'])
            embedding_file = self.faces_dir / f"{user_name}.npy"
            np.save(embedding_file, embedding)
            
            # Guardar imagen de referencia
            img_file = self.faces_dir / f"{user_name}.jpg"
            cv2.imwrite(str(img_file), frame)
            
            # Limpiar archivo temporal
            if temp_file and os.path.exists(temp_file):
                os.remove(temp_file)
            
            self.status_label.config(text=f"Usuario '{user_name}' registrado correctamente!", fg='#4CAF50')
            messagebox.showinfo("Éxito", f"Usuario '{user_name}' registrado correctamente!")
            self.stop_camera()
            
        except Exception as e:
            error_msg = str(e)
            print(f"[ERROR] Error al registrar rostro: {error_msg}")
            
            # Mensaje de error más descriptivo
            if "downloading" in error_msg.lower() or "download" in error_msg.lower():
                detailed_msg = (
                    f"Error al descargar el modelo de reconocimiento facial.\n\n"
                    f"Detalles: {error_msg}\n\n"
                    f"Soluciones:\n"
                    f"1. Verifica tu conexión a internet\n"
                    f"2. Intenta nuevamente (el modelo se descargará automáticamente)\n"
                    f"3. O descarga manualmente el archivo desde:\n"
                    f"   https://github.com/serengil/deepface_models/releases/download/v1.0/vgg_face_weights.h5\n\n"
                    f"Y guárdalo en: C:\\Users\\PC\\.deepface\\weights\\vgg_face_weights.h5"
                )
            else:
                detailed_msg = f"Error al registrar rostro:\n{error_msg}"
            
            messagebox.showerror("Error", detailed_msg)
            self.status_label.config(text="Error al registrar rostro. Ver consola para detalles.", fg='#f44336')
            
    def grant_access(self, user_id, similarity, other_similarities=None):
        """Concede acceso al usuario y muestra información detallada"""
        # Construir mensaje principal
        message = f"Bienvenido, {user_id}!\n\n"
        message += f"Similitud: {similarity:.2%}\n\n"
        
        # Agregar otras similitudes si existen
        if other_similarities and len(other_similarities) > 0:
            message += "Rostros similares:\n"
            # Mostrar máximo las 3 mejores similitudes adicionales (o todas si son menos)
            max_others = min(3, len(other_similarities))
            for i in range(max_others):
                other_user, other_sim = other_similarities[i]
                # Solo mostrar si la similitud es mayor a 0.05% (5% formato porcentual)
                if other_sim >= 0.05:
                    message += f"  • {other_user}: {other_sim:.2%}\n"
        
        message += "\nAcceso concedido exitosamente."
        
        messagebox.showinfo("Acceso Concedido", message)
        self.stop_camera()
        
    def process_existing_images(self):
        """Procesa imágenes existentes en registered_faces/ que no tienen embedding"""
        try:
            print("[INFO] Escaneando carpeta registered_faces/ para imágenes sin procesar...")
            
            # Obtener todas las imágenes en la carpeta
            image_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
            processed_count = 0
            
            for ext in image_extensions:
                for image_file in self.faces_dir.glob(f"*{ext}"):
                    user_name = image_file.stem
                    embedding_file = self.faces_dir / f"{user_name}.npy"
                    
                    # Si la imagen no tiene embedding correspondiente, generarlo
                    if not embedding_file.exists():
                        print(f"[INFO] Imagen encontrada sin embedding: {image_file.name}")
                        print(f"[INFO] Generando embedding para: {user_name}...")
                        
                        try:
                            # Generar embedding desde la imagen
                            embedding_obj = DeepFace.represent(
                                img_path=str(image_file),
                                model_name=self.model_name,
                                detector_backend=self.backend,
                                enforce_detection=False
                            )
                            
                            if len(embedding_obj) > 0:
                                # Guardar embedding
                                embedding = np.array(embedding_obj[0]['embedding'])
                                np.save(embedding_file, embedding)
                                processed_count += 1
                                print(f"[OK] Embedding generado para: {user_name}")
                            else:
                                print(f"[WARN] No se detectó rostro en: {image_file.name}")
                                
                        except Exception as e:
                            print(f"[ERROR] Error al procesar {image_file.name}: {e}")
            
            if processed_count > 0:
                print(f"[OK] Procesadas {processed_count} imagen(es) nuevas.")
            else:
                print("[INFO] No se encontraron imágenes nuevas para procesar.")
                
        except Exception as e:
            print(f"[WARN] Error al procesar imágenes existentes: {e}")
    
    def get_registered_users(self):
        """Obtiene lista de usuarios registrados"""
        # Buscar usuarios tanto por embeddings (.npy) como por imágenes (.jpg, .png)
        users = set()
        
        # Agregar usuarios con embeddings
        for npy_file in self.faces_dir.glob("*.npy"):
            users.add(npy_file.stem)
        
        # Agregar usuarios con imágenes (aunque no tengan embedding aún)
        for ext in ['.jpg', '.jpeg', '.png', '.bmp']:
            for img_file in self.faces_dir.glob(f"*{ext}"):
                users.add(img_file.stem)
        
        return sorted(list(users))
        
    def __del__(self):
        """Limpiar recursos al cerrar"""
        self.stop_camera()

def main():
    """Función principal"""
    root = Tk()
    app = FaceRecognitionApp(root)
    
    # Manejar cierre de ventana
    def on_closing():
        app.stop_camera()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()

