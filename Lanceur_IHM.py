import tkinter as tk
from tkinter import messagebox
import subprocess
import sys
import os

# =========================================================================
# CONFIGURATION DE L'IHM
# =========================================================================
DOSSIER_SCRIPTS = "scripts"

def lancer_script(nom_script):
    """Exécute le script spécifié dans le dossier 'scripts/'."""
    chemin_script = os.path.join(DOSSIER_SCRIPTS, nom_script)
    
    if not os.path.exists(chemin_script):
        messagebox.showerror(
            "Fichier introuvable", 
            f"Le fichier '{nom_script}' est introuvable dans le dossier '{DOSSIER_SCRIPTS}/'.\n"
            "Vérifiez l'architecture de vos dossiers."
        )
        return

    try:
        # On utilise Popen pour ne pas bloquer l'IHM pendant l'exécution du script
        # cwd=DOSSIER_SCRIPTS est crucial pour que les chemins relatifs (../donnees) fonctionnent !
        subprocess.Popen([sys.executable, nom_script], cwd=DOSSIER_SCRIPTS)
    except Exception as e:
        messagebox.showerror("Erreur d'exécution", f"Impossible de lancer {nom_script}.\nErreur: {e}")

# =========================================================================
# CREATION DE L'INTERFACE GRAPHIQUE
# =========================================================================
# Fenêtre principale
root = tk.Tk()
root.title("SYSMER - Interface de Calibration & Tracking")
root.geometry("450x550")
root.configure(bg="#f4f4f9")
root.resizable(False, False)

# En-tête
header_frame = tk.Frame(root, bg="#2c3e50", pady=15)
header_frame.pack(fill=tk.X)

tk.Label(header_frame, text="SYSMER TRACKER", font=("Helvetica", 18, "bold"), fg="white", bg="#2c3e50").pack()
tk.Label(header_frame, text="Pipeline de Calibration et de Suivi", font=("Helvetica", 10), fg="#bdc3c7", bg="#2c3e50").pack()

# Conteneur pour les boutons
content_frame = tk.Frame(root, bg="#f4f4f9", pady=20)
content_frame.pack(fill=tk.BOTH, expand=True)

# Liste des étapes du pipeline
etapes = [
    ("1. Calibration Intrinsèque", "Intrinsec.py", "Calcule les distorsions de la caméra (K, D)"),
    ("2. Calibration Extrinsèque", "Extrinsec.py", "Calcule la pose relative entre les 2 caméras (R, T)"),
    ("3. Génération des Matrices", "Passage.py", "Génère les matrices de projection P1 et P2"),
    ("4. Redressement du Sol", "Redressement.py", "Aligne le repère 3D sur le plan de la mire"),
    ("5. Lancement du Tracking", "Tracking.py", "Suivi YOLO en temps réel et export TSV")
]

# Génération dynamique des boutons
for titre, script, description in etapes:
    frame_etape = tk.Frame(content_frame, bg="#f4f4f9", pady=8)
    frame_etape.pack(fill=tk.X, padx=30)
    
    # Bouton principal
    btn = tk.Button(
        frame_etape, 
        text=titre, 
        font=("Helvetica", 11, "bold"), 
        bg="#3498db", 
        fg="white", 
        activebackground="#2980b9", 
        activeforeground="white",
        relief=tk.FLAT,
        height=2,
        cursor="hand2",
        command=lambda s=script: lancer_script(s)
    )
    btn.pack(fill=tk.X)
    
    # Label de description
    lbl = tk.Label(frame_etape, text=description, font=("Helvetica", 9, "italic"), fg="#7f8c8d", bg="#f4f4f9")
    lbl.pack(anchor="w")

# Pied de page
footer_frame = tk.Frame(root, bg="#ecf0f1", pady=10)
footer_frame.pack(fill=tk.X, side=tk.BOTTOM)
tk.Label(footer_frame, text="Assurez-vous de fermer les fenêtres d'un script avant de lancer le suivant.", 
         font=("Helvetica", 8), fg="#e74c3c", bg="#ecf0f1").pack()

# Lancement de la boucle principale
root.mainloop()