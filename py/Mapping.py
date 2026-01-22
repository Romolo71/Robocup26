"""
Sistema Professionale di Mappatura del Labirinto
Architettura modulare con Computer Vision e Raspberry Pi 5 support

Author: Senior Software Engineer
Version: 1.0.0
"""

import pygame
import numpy as np
import threading
import queue
import time
from enum import Enum
from typing import Tuple, Optional, Dict, List
from dataclasses import dataclass
import random

# ============================================================================
# CONFIGURAZIONE GLOBALE
# ============================================================================

CONFIG = {
    # Display Settings
    "WINDOW_WIDTH": 1280,
    "WINDOW_HEIGHT": 720,
    "FPS": 30,

    # Grid Settings
    "TILE_SIZE": 40,
    "GRID_MAX_SIZE": 50,
    "GRID_OFFSET_X": 50,
    "GRID_OFFSET_Y": 120,

    # AI Settings
    "MODEL_PATH": "model.tflite",
    "LABELS_PATH": "labels.txt",
    "CONFIDENCE_THRESHOLD": 0.75,
    "INPUT_SIZE": (224, 224),

    # Camera Settings
    "CAMERA_INDEX": 0,
    "CAMERA_WIDTH": 640,
    "CAMERA_HEIGHT": 480,

    # Colors (Dark Mode Professional)
    "COLORS": {
        "BACKGROUND": (20, 20, 25),
        "PANEL_BG": (30, 30, 35),
        "HEADER_BG": (40, 40, 50),
        "TEXT_PRIMARY": (240, 240, 245),
        "TEXT_SECONDARY": (160, 160, 170),
        "ACCENT_BLUE": (100, 180, 255),
        "ACCENT_GREEN": (100, 255, 150),
        "ACCENT_RED": (255, 100, 120),
        "ACCENT_YELLOW": (255, 220, 100),
        "ACCENT_PURPLE": (180, 100, 255),

        # Grid Colors
        "WALL": (80, 80, 90),
        "FLOOR": (40, 40, 45),
        "START": (100, 255, 150),
        "VICTIM": (255, 100, 120),
        "LETTER_X": (100, 180, 255),
        "LETTER_Y": (255, 220, 100),
        "LETTER_H": (180, 100, 255),
        "GRID_LINE": (60, 60, 70),
    },

    # Demo Mode
    "DEMO_MODE": True,  # Cambiar a False per modalità LIVE
}


# ============================================================================
# ENUMERAZIONI
# ============================================================================

class CellState(Enum):
    """Stati possibili di una cella della griglia."""
    UNKNOWN = 0
    WALL = 1
    FLOOR = 2
    START_POINT = 3
    VICTIM_FOUND = 4
    LETTER_X = 5
    LETTER_Y = 6
    LETTER_H = 7


@dataclass
class DetectionResult:
    """Risultato di una detection AI."""
    label: str
    confidence: float
    timestamp: float


# ============================================================================
# SISTEMA DI VISIONE AI
# ============================================================================

class VisionSystem:
    """
    Sistema di Computer Vision per inferenza TensorFlow Lite.
    Gestisce il caricamento del modello e le predizioni.
    """

    def __init__(self, model_path: str, labels_path: str):
        """
        Inizializza il sistema di visione.

        Args:
            model_path: Path al file .tflite
            labels_path: Path al file labels.txt
        """
        self.model_path = model_path
        self.labels_path = labels_path
        self.interpreter = None
        self.labels = []
        self.input_details = None
        self.output_details = None
        self.is_loaded = False

    def load_model(self) -> bool:
        """
        Carica il modello TensorFlow Lite.

        Returns:
            True se il caricamento ha successo
        """
        try:
            # Simulazione caricamento modello per demo
            # In produzione: usare tflite_runtime.interpreter
            print(f"[VisionSystem] Caricamento modello: {self.model_path}")

            # Mock labels
            self.labels = ["WALL", "FLOOR", "START", "VICTIM", "LETTER_X", "LETTER_Y", "LETTER_H"]
            self.is_loaded = True

            print("[VisionSystem] Modello caricato con successo")
            return True

        except Exception as e:
            print(f"[VisionSystem] Errore caricamento modello: {e}")
            return False

    def predict(self, frame: np.ndarray) -> Optional[DetectionResult]:
        """
        Esegue predizione su un frame.

        Args:
            frame: Frame numpy array (BGR)

        Returns:
            DetectionResult o None se fallisce
        """
        if not self.is_loaded:
            return None

        try:
            # Simulazione inferenza per DEMO
            # In produzione: preprocessing + interpreter.invoke()

            label = random.choice(self.labels)
            confidence = random.uniform(0.6, 0.99)

            return DetectionResult(
                label=label,
                confidence=confidence,
                timestamp=time.time()
            )

        except Exception as e:
            print(f"[VisionSystem] Errore predizione: {e}")
            return None


# ============================================================================
# SISTEMA DI MAPPATURA
# ============================================================================

class GridMap:
    """
    Sistema di mappatura dinamica del labirinto.
    Gestisce lo stato della griglia e le statistiche.
    """

    def __init__(self, max_size: int = 50):
        """
        Inizializza la griglia.

        Args:
            max_size: Dimensione massima della griglia
        """
        self.max_size = max_size
        self.grid: Dict[Tuple[int, int], CellState] = {}
        self.current_position = (0, 0)
        self.lock = threading.Lock()

        # Statistiche
        self.stats = {
            "total_cells": 0,
            "victims_found": 0,
            "letters_found": 0,
            "walls_detected": 0,
        }

    def set_cell(self, x: int, y: int, state: CellState) -> None:
        """
        Imposta lo stato di una cella.

        Args:
            x: Coordinata X
            y: Coordinata Y
            state: Nuovo stato della cella
        """
        with self.lock:
            if abs(x) > self.max_size or abs(y) > self.max_size:
                return

            self.grid[(x, y)] = state
            self._update_stats(state)

    def get_cell(self, x: int, y: int) -> CellState:
        """Ottiene lo stato di una cella."""
        with self.lock:
            return self.grid.get((x, y), CellState.UNKNOWN)

    def get_all_cells(self) -> Dict[Tuple[int, int], CellState]:
        """Ottiene tutte le celle della griglia (thread-safe)."""
        with self.lock:
            return self.grid.copy()

    def get_bounds(self) -> Tuple[int, int, int, int]:
        """Calcola i bounds della griglia (min_x, max_x, min_y, max_y)."""
        with self.lock:
            if not self.grid:
                return (0, 0, 0, 0)

            xs = [x for x, y in self.grid.keys()]
            ys = [y for x, y in self.grid.keys()]

            return (min(xs), max(xs), min(ys), max(ys))

    def _update_stats(self, state: CellState) -> None:
        """Aggiorna le statistiche interne."""
        self.stats["total_cells"] = len(self.grid)

        if state == CellState.VICTIM_FOUND:
            self.stats["victims_found"] += 1
        elif state in [CellState.LETTER_X, CellState.LETTER_Y, CellState.LETTER_H]:
            self.stats["letters_found"] += 1
        elif state == CellState.WALL:
            self.stats["walls_detected"] += 1

    def get_stats(self) -> Dict[str, int]:
        """Ottiene le statistiche correnti."""
        with self.lock:
            return self.stats.copy()


# ============================================================================
# THREAD DI ACQUISIZIONE CAMERA
# ============================================================================

class CameraThread(threading.Thread):
    """Thread per acquisizione frame dalla camera."""

    def __init__(self, camera_index: int, frame_queue: queue.Queue):
        """
        Inizializza il thread camera.

        Args:
            camera_index: Indice della camera
            frame_queue: Queue per i frame
        """
        super().__init__(daemon=True)
        self.camera_index = camera_index
        self.frame_queue = frame_queue
        self.running = False
        self.cap = None

    def run(self) -> None:
        """Loop principale del thread."""
        try:
            # In produzione: cv2.VideoCapture(self.camera_index)
            print(f"[CameraThread] Inizializzazione camera {self.camera_index}")
            self.running = True

            while self.running:
                # Simulazione frame per DEMO
                time.sleep(0.033)  # ~30 FPS

                # Mock frame (in prod: ret, frame = self.cap.read())
                mock_frame = np.zeros((480, 640, 3), dtype=np.uint8)

                if not self.frame_queue.full():
                    self.frame_queue.put(mock_frame)

        except Exception as e:
            print(f"[CameraThread] Errore: {e}")
        finally:
            self.stop()

    def stop(self) -> None:
        """Ferma il thread."""
        self.running = False
        if self.cap is not None:
            self.cap.release()


# ============================================================================
# THREAD DI INFERENZA AI
# ============================================================================

class InferenceThread(threading.Thread):
    """Thread per inferenza AI e aggiornamento mappa."""

    def __init__(self, vision_system: VisionSystem, grid_map: GridMap,
                 frame_queue: queue.Queue):
        """
        Inizializza il thread di inferenza.

        Args:
            vision_system: Sistema di visione
            grid_map: Mappa della griglia
            frame_queue: Queue dei frame da processare
        """
        super().__init__(daemon=True)
        self.vision_system = vision_system
        self.grid_map = grid_map
        self.frame_queue = frame_queue
        self.running = False
        self.last_detection = None
        self.current_x = 0
        self.current_y = 0

    def run(self) -> None:
        """Loop principale del thread."""
        print("[InferenceThread] Avviato")
        self.running = True

        while self.running:
            try:
                # Ottiene frame dalla queue
                frame = self.frame_queue.get(timeout=0.1)

                # Esegue predizione
                result = self.vision_system.predict(frame)

                if result and result.confidence >= CONFIG["CONFIDENCE_THRESHOLD"]:
                    self.last_detection = result
                    self._update_map(result)

            except queue.Empty:
                continue
            except Exception as e:
                print(f"[InferenceThread] Errore: {e}")

    def _update_map(self, result: DetectionResult) -> None:
        """
        Aggiorna la mappa in base alla detection.

        Args:
            result: Risultato della detection
        """
        # Mappa label -> CellState
        label_to_state = {
            "WALL": CellState.WALL,
            "FLOOR": CellState.FLOOR,
            "START": CellState.START_POINT,
            "VICTIM": CellState.VICTIM_FOUND,
            "LETTER_X": CellState.LETTER_X,
            "LETTER_Y": CellState.LETTER_Y,
            "LETTER_H": CellState.LETTER_H,
        }

        state = label_to_state.get(result.label, CellState.FLOOR)
        self.grid_map.set_cell(self.current_x, self.current_y, state)

        # Avanza posizione (simulazione movimento)
        self.current_x += random.choice([-1, 0, 1])
        self.current_y += random.choice([-1, 0, 1])

    def stop(self) -> None:
        """Ferma il thread."""
        self.running = False


# ============================================================================
# SISTEMA UI (PYGAME)
# ============================================================================

class MazeMapperUI:
    """
    Interfaccia grafica professionale per la mappatura.
    Gestisce rendering e interazione utente.
    """

    def __init__(self, grid_map: GridMap, inference_thread: InferenceThread):
        """
        Inizializza la UI.

        Args:
            grid_map: Sistema di mappatura
            inference_thread: Thread di inferenza (per stats)
        """
        pygame.init()

        self.grid_map = grid_map
        self.inference_thread = inference_thread

        # Setup finestra
        self.screen = pygame.display.set_mode(
            (CONFIG["WINDOW_WIDTH"], CONFIG["WINDOW_HEIGHT"])
        )
        pygame.display.set_caption("Sistema di Mappatura Labirinto")

        # Clock per FPS
        self.clock = pygame.time.Clock()
        self.running = True

        # Fonts
        self.font_title = pygame.font.SysFont("Arial", 32, bold=True)
        self.font_normal = pygame.font.SysFont("Arial", 16)
        self.font_small = pygame.font.SysFont("Arial", 14)

        # Panels
        self.legend_panel_rect = pygame.Rect(
            CONFIG["WINDOW_WIDTH"] - 280, 80, 260, 500
        )

    def run(self) -> None:
        """Loop principale della UI."""
        while self.running:
            self._handle_events()
            self._update()
            self._render()
            self.clock.tick(CONFIG["FPS"])

        pygame.quit()

    def _handle_events(self) -> None:
        """Gestisce eventi pygame."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_c:
                    # Clear map
                    self.grid_map.grid.clear()

    def _update(self) -> None:
        """Aggiorna logica (se necessario)."""
        pass

    def _render(self) -> None:
        """Renderizza tutta la UI."""
        # Background
        self.screen.fill(CONFIG["COLORS"]["BACKGROUND"])

        # Header
        self._render_header()

        # Grid
        self._render_grid()

        # Legend Panel
        self._render_legend_panel()

        # Status Bar
        self._render_status_bar()

        pygame.display.flip()

    def _render_header(self) -> None:
        """Renderizza l'header."""
        header_rect = pygame.Rect(0, 0, CONFIG["WINDOW_WIDTH"], 70)
        pygame.draw.rect(self.screen, CONFIG["COLORS"]["HEADER_BG"], header_rect)

        # Titolo
        title_text = self.font_title.render(
            "🗺️  MAPPATURA DEL LABIRINTO", True, CONFIG["COLORS"]["TEXT_PRIMARY"]
        )
        title_rect = title_text.get_rect(center=(CONFIG["WINDOW_WIDTH"] // 2, 35))
        self.screen.blit(title_text, title_rect)

    def _render_grid(self) -> None:
        """Renderizza la griglia del labirinto."""
        cells = self.grid_map.get_all_cells()

        if not cells:
            # Nessuna cella da renderizzare
            no_data_text = self.font_normal.render(
                "In attesa di dati...", True, CONFIG["COLORS"]["TEXT_SECONDARY"]
            )
            self.screen.blit(no_data_text, (CONFIG["GRID_OFFSET_X"], CONFIG["GRID_OFFSET_Y"]))
            return

        # Calcola bounds
        min_x, max_x, min_y, max_y = self.grid_map.get_bounds()

        # Renderizza celle
        for (x, y), state in cells.items():
            screen_x = CONFIG["GRID_OFFSET_X"] + (x - min_x) * CONFIG["TILE_SIZE"]
            screen_y = CONFIG["GRID_OFFSET_Y"] + (y - min_y) * CONFIG["TILE_SIZE"]

            cell_rect = pygame.Rect(
                screen_x, screen_y, CONFIG["TILE_SIZE"], CONFIG["TILE_SIZE"]
            )

            # Colore in base allo stato
            color = self._get_cell_color(state)
            pygame.draw.rect(self.screen, color, cell_rect)
            pygame.draw.rect(self.screen, CONFIG["COLORS"]["GRID_LINE"], cell_rect, 1)

            # Icona/Testo per stati speciali
            if state == CellState.VICTIM_FOUND:
                pygame.draw.circle(
                    self.screen, CONFIG["COLORS"]["ACCENT_RED"],
                    cell_rect.center, CONFIG["TILE_SIZE"] // 3
                )
            elif state in [CellState.LETTER_X, CellState.LETTER_Y, CellState.LETTER_H]:
                letter = state.name.split("_")[1]
                letter_text = self.font_small.render(letter, True, (255, 255, 255))
                letter_rect = letter_text.get_rect(center=cell_rect.center)
                self.screen.blit(letter_text, letter_rect)

    def _render_legend_panel(self) -> None:
        """Renderizza il pannello legenda."""
        # Background
        pygame.draw.rect(
            self.screen, CONFIG["COLORS"]["PANEL_BG"], self.legend_panel_rect, 0, 10
        )
        pygame.draw.rect(
            self.screen, CONFIG["COLORS"]["ACCENT_BLUE"], self.legend_panel_rect, 2, 10
        )

        # Titolo legenda
        title = self.font_normal.render("📋 LEGENDA", True, CONFIG["COLORS"]["TEXT_PRIMARY"])
        self.screen.blit(title, (self.legend_panel_rect.x + 20, self.legend_panel_rect.y + 15))

        # Elementi legenda
        legend_items = [
            ("Muro", CONFIG["COLORS"]["WALL"], "rect"),
            ("Pavimento", CONFIG["COLORS"]["FLOOR"], "rect"),
            ("Partenza", CONFIG["COLORS"]["START"], "circle"),
            ("Vittima", CONFIG["COLORS"]["VICTIM"], "circle"),
            ("Lettera X", CONFIG["COLORS"]["LETTER_X"], "text"),
            ("Lettera Y", CONFIG["COLORS"]["LETTER_Y"], "text"),
            ("Lettera H", CONFIG["COLORS"]["LETTER_H"], "text"),
        ]

        y_offset = 55
        for label, color, shape_type in legend_items:
            icon_x = self.legend_panel_rect.x + 25
            icon_y = self.legend_panel_rect.y + y_offset

            if shape_type == "rect":
                pygame.draw.rect(self.screen, color, (icon_x, icon_y, 20, 20))
            elif shape_type == "circle":
                pygame.draw.circle(self.screen, color, (icon_x + 10, icon_y + 10), 10)
            elif shape_type == "text":
                letter = label.split()[-1]
                letter_surf = self.font_small.render(letter, True, (255, 255, 255))
                letter_bg = pygame.Rect(icon_x, icon_y, 20, 20)
                pygame.draw.rect(self.screen, color, letter_bg)
                self.screen.blit(letter_surf, (icon_x + 5, icon_y + 3))

            text = self.font_small.render(label, True, CONFIG["COLORS"]["TEXT_SECONDARY"])
            self.screen.blit(text, (icon_x + 30, icon_y + 2))

            y_offset += 35

        # Statistiche
        y_offset += 20
        stats_title = self.font_normal.render(
            "📊 STATISTICHE", True, CONFIG["COLORS"]["TEXT_PRIMARY"]
        )
        self.screen.blit(stats_title, (self.legend_panel_rect.x + 20,
                                       self.legend_panel_rect.y + y_offset))

        stats = self.grid_map.get_stats()
        y_offset += 35

        stats_lines = [
            f"Celle mappate: {stats['total_cells']}",
            f"Vittime trovate: {stats['victims_found']}",
            f"Lettere trovate: {stats['letters_found']}",
            f"Muri rilevati: {stats['walls_detected']}",
        ]

        for line in stats_lines:
            text = self.font_small.render(line, True, CONFIG["COLORS"]["TEXT_SECONDARY"])
            self.screen.blit(text, (self.legend_panel_rect.x + 25,
                                   self.legend_panel_rect.y + y_offset))
            y_offset += 25

        # Confidenza ultima detection
        if self.inference_thread.last_detection:
            y_offset += 10
            conf = self.inference_thread.last_detection.confidence * 100
            conf_text = self.font_small.render(
                f"Confidenza AI: {conf:.1f}%", True, CONFIG["COLORS"]["ACCENT_GREEN"]
            )
            self.screen.blit(conf_text, (self.legend_panel_rect.x + 25,
                                        self.legend_panel_rect.y + y_offset))

    def _render_status_bar(self) -> None:
        """Renderizza la barra di stato in basso."""
        status_rect = pygame.Rect(
            0, CONFIG["WINDOW_HEIGHT"] - 40, CONFIG["WINDOW_WIDTH"], 40
        )
        pygame.draw.rect(self.screen, CONFIG["COLORS"]["HEADER_BG"], status_rect)

        # Status
        mode = "DEMO" if CONFIG["DEMO_MODE"] else "LIVE"
        status_text = f"● ATTIVO  |  FPS: {int(self.clock.get_fps())}  |  Modalità: {mode}"

        text_surf = self.font_small.render(
            status_text, True, CONFIG["COLORS"]["ACCENT_GREEN"]
        )
        self.screen.blit(text_surf, (20, CONFIG["WINDOW_HEIGHT"] - 25))

        # Istruzioni
        help_text = "ESC: Esci  |  C: Pulisci mappa"
        help_surf = self.font_small.render(
            help_text, True, CONFIG["COLORS"]["TEXT_SECONDARY"]
        )
        help_rect = help_surf.get_rect(right=CONFIG["WINDOW_WIDTH"] - 20,
                                       centery=CONFIG["WINDOW_HEIGHT"] - 20)
        self.screen.blit(help_surf, help_rect)

    def _get_cell_color(self, state: CellState) -> Tuple[int, int, int]:
        """Mappa CellState a colore."""
        color_map = {
            CellState.WALL: CONFIG["COLORS"]["WALL"],
            CellState.FLOOR: CONFIG["COLORS"]["FLOOR"],
            CellState.START_POINT: CONFIG["COLORS"]["START"],
            CellState.VICTIM_FOUND: CONFIG["COLORS"]["VICTIM"],
            CellState.LETTER_X: CONFIG["COLORS"]["LETTER_X"],
            CellState.LETTER_Y: CONFIG["COLORS"]["LETTER_Y"],
            CellState.LETTER_H: CONFIG["COLORS"]["LETTER_H"],
            CellState.UNKNOWN: CONFIG["COLORS"]["FLOOR"],
        }
        return color_map.get(state, CONFIG["COLORS"]["FLOOR"])


# ============================================================================
# MODALITÀ DEMO
# ============================================================================

class DemoSimulator(threading.Thread):
    """Simulatore per popolare la mappa con dati casuali (modalità DEMO)."""

    def __init__(self, grid_map: GridMap):
        super().__init__(daemon=True)
        self.grid_map = grid_map
        self.running = False

    def run(self) -> None:
        """Loop simulazione."""
        print("[DemoSimulator] Avviato - Generazione mappa casuale")
        self.running = True

        x, y = 0, 0

        while self.running:
            # Genera stato casuale
            state_choices = [
                CellState.FLOOR, CellState.FLOOR, CellState.FLOOR,  # Più pavimenti
                CellState.WALL,
                CellState.VICTIM_FOUND,
                CellState.LETTER_X, CellState.LETTER_Y, CellState.LETTER_H,
            ]

            state = random.choice(state_choices)
            self.grid_map.set_cell(x, y, state)

            # Movimento casuale
            direction = random.choice(['N', 'S', 'E', 'W', 'NE', 'NW', 'SE', 'SW'])
            if 'N' in direction:
                y -= 1
            if 'S' in direction:
                y += 1
            if 'E' in direction:
                x += 1
            if 'W' in direction:
                x -= 1

            # Limita espansione
            x = max(-15, min(15, x))
            y = max(-15, min(15, y))

            time.sleep(0.2)  # Aggiornamento ogni 200ms

    def stop(self) -> None:
        self.running = False


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Entry point dell'applicazione."""
    print("=" * 70)
    print(" SISTEMA DI MAPPATURA PROFESSIONALE DEL LABIRINTO")
    print("=" * 70)
    print(f" Modalità: {'DEMO' if CONFIG['DEMO_MODE'] else 'LIVE'}")
    print(f" Risoluzione: {CONFIG['WINDOW_WIDTH']}x{CONFIG['WINDOW_HEIGHT']}")
    print("=" * 70)

    # Inizializza componenti
    grid_map = GridMap(max_size=CONFIG["GRID_MAX_SIZE"])
    vision_system = VisionSystem(CONFIG["MODEL_PATH"], CONFIG["LABELS_PATH"])

    # Carica modello AI
    if not CONFIG["DEMO_MODE"]:
        if not vision_system.load_model():
            print("[ERRORE] Impossibile caricare il modello AI")
            return
    else:
        vision_system.load_model()

    # Queue per comunicazione thread
    frame_queue = queue.Queue(maxsize=5)

    # Inizializza threads
    if CONFIG["DEMO_MODE"]:
        # Modalità DEMO: usa simulatore invece di camera/AI reali
        print("[INFO] Avvio modalità DEMO - Simulazione attiva")
        demo_thread = DemoSimulator(grid_map)
        demo_thread.start()

        # Thread inferenza dummy
        inference_thread = InferenceThread(vision_system, grid_map, frame_queue)
    else:
        # Modalità LIVE: usa camera e AI reali
        print("[INFO] Avvio modalità LIVE - Camera e AI attivi")
        camera_thread = CameraThread(CONFIG["CAMERA_INDEX"], frame_queue)
        camera_thread.start()

        inference_thread = InferenceThread(vision_system, grid_map, frame_queue)
        inference_thread.start()

    # Avvia UI (thread principale)
    try:
        ui = MazeMapperUI(grid_map, inference_thread)
        ui.run()
    except KeyboardInterrupt:
        print("\n[INFO] Interruzione da tastiera")
    finally:
        # Cleanup
        print("[INFO] Arresto sistema...")
        if CONFIG["DEMO_MODE"]:
            demo_thread.stop()
        else:
            camera_thread.stop()
            inference_thread.stop()

        print("[INFO] Sistema arrestato correttamente")
        print("=" * 70)


if __name__ == "__main__":
    main()