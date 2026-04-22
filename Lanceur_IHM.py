import tkinter as tk
from tkinter import messagebox, simpledialog
import subprocess
import sys
import os

# =========================================================================
# CONFIGURATION DE L'IHM
# =========================================================================
DOSSIER_SCRIPTS = "scripts"

# On mémorise les ID des caméras choisis par l'utilisateur (0 et 1 par défaut)
memoire_cams = {"cam1": 1, "cam2": 0}

def lancer_script(nom_script, *args):
    """Exécute le script spécifié avec d'éventuels arguments."""
    chemin_script = os.path.join(DOSSIER_SCRIPTS, nom_script)
    
    if not os.path.exists(chemin_script):
        messagebox.showerror(
            "Fichier introuvable", 
            f"Le fichier '{nom_script}' est introuvable dans le dossier '{DOSSIER_SCRIPTS}/'.\n"
        )
        return

    try:
        commande = [sys.executable, nom_script] + list(args)
        subprocess.Popen(commande, cwd=DOSSIER_SCRIPTS)
    except Exception as e:
        messagebox.showerror("Erreur d'exécution", f"Impossible de lancer {nom_script}.\nErreur: {e}")

def demander_cam_et_lancer(nom_script, titre_etape, cle_cam):
    """Demande l'ID de la caméra et le mémorise avant de lancer le script."""
    cam_id = simpledialog.askinteger(
        "Choix de la caméra", 
        f"Entrez l'ID de la caméra pour l'étape :\n{titre_etape}\n(ex: 0, 1, 2...)",
        initialvalue=memoire_cams[cle_cam], # Propose la dernière valeur utilisée
        minvalue=0, 
        maxvalue=10
    )
    
    if cam_id is not None:
        memoire_cams[cle_cam] = cam_id # On sauvegarde le choix
        lancer_script(nom_script, str(cam_id))

def lancer_extrinseque(nom_script):
    """Lance le script extrinsèque en lui passant les DEUX ID mémorisés."""
    id1 = str(memoire_cams["cam1"])
    id2 = str(memoire_cams["cam2"])
    print(f"Lancement de {nom_script} avec Cam1={id1} et Cam2={id2}")
    lancer_script(nom_script, id1, id2)
    
def lancer_redressement(nom_script):
    """Lance le script de redressement en lui passant l'ID mémorisé de la Caméra 1."""
    id1 = str(memoire_cams["cam1"])
    print(f"Lancement de {nom_script} avec Cam1={id1}")
    lancer_script(nom_script, id1)

def lancer_tracking(nom_script):
    """Lance le script de tracking en lui passant les DEUX ID mémorisés."""
    id1 = str(memoire_cams["cam1"])
    id2 = str(memoire_cams["cam2"])
    print(f"Lancement de {nom_script} avec Cam1={id1} et Cam2={id2}")
    lancer_script(nom_script, id1, id2)
    
# =========================================================================
# CREATION DE L'INTERFACE GRAPHIQUE
# =========================================================================
root = tk.Tk()
root.title("SYSMER - Interface de Calibration & Tracking")
root.geometry("450x650") 
root.configure(bg="#f4f4f9")
root.resizable(False, False)

header_frame = tk.Frame(root, bg="#2c3e50", pady=15)
header_frame.pack(fill=tk.X)

tk.Label(header_frame, text="SYSMER TRACKER", font=("Helvetica", 18, "bold"), fg="white", bg="#2c3e50").pack()
tk.Label(header_frame, text="Pipeline de Calibration et de Suivi", font=("Helvetica", 10), fg="#bdc3c7", bg="#2c3e50").pack()

content_frame = tk.Frame(root, bg="#f4f4f9", pady=20)
content_frame.pack(fill=tk.BOTH, expand=True)

# Ajout d'un tag d'action pour identifier le comportement du bouton
etapes = [
    ("1a. Calibration Intrinsèque (Cam 1)", "Intrinsec_cam1.py", "Calcule les distorsions de la caméra 1", "intrinsec1"),
    ("1b. Calibration Intrinsèque (Cam 2)", "Intrinsec_cam2.py", "Calcule les distorsions de la caméra 2", "intrinsec2"),
    ("2. Calibration Extrinsèque", "Extrinsec.py", "Calcule la pose relative entre les 2 caméras", "extrinsec"),
    ("3. Génération des Matrices", "Passage.py", "Génère les matrices de projection P1 et P2", "normal"),
    ("4. Redressement du Sol", "Redressement.py", "Aligne le repère 3D sur le plan de la mire", "redressement"),
    ("5. Lancement du Tracking", "Tracking.py", "Suivi YOLO en temps réel et export TSV", "tracking")
]

for titre, script, description, action in etapes:
    frame_etape = tk.Frame(content_frame, bg="#f4f4f9", pady=8)
    frame_etape.pack(fill=tk.X, padx=30)
    
    # Routage vers la bonne fonction selon l'étape
    if action == "intrinsec1":
        cmd = lambda s=script, t=titre: demander_cam_et_lancer(s, t, "cam1")
    elif action == "intrinsec2":
        cmd = lambda s=script, t=titre: demander_cam_et_lancer(s, t, "cam2")
    elif action == "extrinsec":
        cmd = lambda s=script: lancer_extrinseque(s)
    elif action == "redressement":                                     
        cmd = lambda s=script: lancer_redressement(s)
    elif action == "tracking":                                         
        cmd = lambda s=script: lancer_tracking(s)
    else:
        cmd = lambda s=script: lancer_script(s)

    btn = tk.Button(
        frame_etape, text=titre, font=("Helvetica", 11, "bold"), bg="#3498db", 
        fg="white", activebackground="#2980b9", activeforeground="white",
        relief=tk.FLAT, height=2, cursor="hand2", command=cmd
    )
    btn.pack(fill=tk.X)
    
    lbl = tk.Label(frame_etape, text=description, font=("Helvetica", 9, "italic"), fg="#7f8c8d", bg="#f4f4f9")
    lbl.pack(anchor="w")

footer_frame = tk.Frame(root, bg="#ecf0f1", pady=10)
footer_frame.pack(fill=tk.X, side=tk.BOTTOM)
tk.Label(footer_frame, text="Assurez-vous de fermer les fenêtres d'un script avant de lancer le suivant.", 
         font=("Helvetica", 8), fg="#e74c3c", bg="#ecf0f1").pack()

root.mainloop()
