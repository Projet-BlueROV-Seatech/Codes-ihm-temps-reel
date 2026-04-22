import numpy as np
import os

# Configuration des dossiers : BASE_DIR est le dossier où se trouve ce script (la racine du projet)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def charger_data(chemin_relatif, is_dict=False):
    # os.path.normpath permet de gérer automatiquement les slashs/antislashs selon l'OS (Windows/Linux)
    chemin = os.path.join(BASE_DIR, os.path.normpath(chemin_relatif))
    if os.path.exists(chemin):
        data = np.load(chemin, allow_pickle=True)
        return data.item() if is_dict else data
    else:
        print(f"⚠️ Fichier introuvable : {chemin}")
    return None

def synthese():
    print("="*70)
    print("🚀 BILAN DE CORRÉLATION ET PRÉCISION GLOBALE DU SYSTÈME")
    print("="*70)

    # 1. INCERTITUDES INTRINSÈQUES (K et D)
    k1_std = charger_data("donnees_calibration/intrinseques/K1_std.npy")
    k2_std = charger_data("donnees_calibration/intrinseques/K2_std.npy")
    d1_std = charger_data("donnees_calibration/intrinseques/D1_std.npy")
    d2_std = charger_data("donnees_calibration/intrinseques/D2_std.npy")
    
    err_intr_px = 0
    if k1_std is not None and k2_std is not None:
        print(f"[1] INTRINSÈQUE  : Incertitude de projection CAM1 : {np.mean(k1_std[:4]):.4f} px")
        print(f"[1] INTRINSÈQUE  : Incertitude de projection CAM2 : {np.mean(k2_std[:4]):.4f} px")
        print(f"[1] INTRINSÈQUE  : Distorsion CAM1 : {np.mean(d1_std[4:9]):.4f} px")
        print(f"[1] INTRINSÈQUE  : Distorsion CAM2 : {np.mean(d2_std[4:9]):.4f} px")
        # Moyenne des incertitudes de projection pour le calcul global
        err_intr_px = (np.mean(k1_std[:4]) + np.mean(k2_std[:4])) / 2

    # 2. INCERTITUDES EXTRINSÈQUES
    ext = charger_data("donnees_calibration/extrinseques/erreurs_extrinseques.npy", is_dict=True)
    dist = charger_data("donnees_calibration/extrinseques/t_c2_c1.npy")
    
    valeur_qualisys = 1312 # mm ou mettre np.linalg.norm(dist)*1000
    delta_dist_mm = 0
    err_extr_px = 0
    
    if dist is not None:
        # Écart entre la distance calculée (t_c2_c1) et la vérité terrain Qualisys
        delta_dist_mm = abs(np.linalg.norm(dist)*1000 - valeur_qualisys)
        
    if ext is not None:
        print(f"[2] EXTRINSÈQUE  : Erreur de reprojection CAM1-Mire   : {ext['reprojection_cam1_px']:.4f} px")
        print(f"[2] EXTRINSÈQUE  : Erreur de reprojection CAM2-CAM1   : {ext['reprojection_cam2_px']:.4f} px")
        # Moyenne des erreurs de reprojection
        err_extr_px = (ext['reprojection_cam1_px'] + ext['reprojection_cam2_px']) / 2

    # 3. ERREUR DE REDRESSEMENT (SOL)
    err_sol = charger_data("donnees_calibration/environnement/erreur_redressement.npy")
    err_sol_px = 0
    if err_sol is not None:
        err_sol_px = err_sol[0]
        print(f"[3] REDRESSEMENT : Erreur géométrique du sol          : {err_sol_px:.3f} px")

    # 4. BRUIT DE DÉTECTION (YOLO + TRIANGULATION)
    err_yolo = charger_data("resultats_tracking/erreurs_triangulation_yolo_temps_reel.npy")
    err_detec_px = 0
    if err_yolo is not None:
        err_detec_px = np.mean(err_yolo)
        print(f"[4] TRACKING     : Bruit de triangulation YOLO        : {err_detec_px:.3f} px")

    
    print("\n" + "-"*50)
    print("📈 SYNTHÈSE DES PRÉCISIONS")
    print("-" * 50)
    
    # --- CALCUL CORRIGÉ DE L'INCERTITUDE ---
    
    # 1. Combinaison quadratique de toutes les erreurs en PIXELS (Root Sum Squared)
    erreur_globale_px = np.sqrt(err_intr_px**2 + err_extr_px**2 + err_sol_px**2 + err_detec_px**2)
    print(f"📊 Erreur agrégée totale sur l'image : {erreur_globale_px:.3f} px")

    # 2. Conversion en MILLIMÈTRES via la géométrie Stéréoscopique
    Z_distance_m = 1.5  # Distance moyenne du robot par rapport aux caméras (en mètres)
    Z_mm = Z_distance_m * 1000 
    B_mm = valeur_qualisys  # Ligne de base Qualisys (1312 mm)
    
    # Récupération automatique de la focale (f) en pixels depuis la matrice K1
    k1_matrice = charger_data("donnees_calibration/intrinseques/K1.npy")
    f_px = k1_matrice[0, 0] if k1_matrice is not None else 800.0 # 800px par défaut en sécurité
    
    # Formule fondamentale de l'erreur en stéréovision : ΔZ = (Z² / (f * B)) * Δpx
    incertitude_profondeur_mm = (Z_mm**2 / (f_px * B_mm)) * erreur_globale_px

    # On affiche la vraie précision de triangulation
    print(f"🛠️ INCERTITUDE DE TRIANGULATION ESTIMÉE À {Z_distance_m}m : {incertitude_profondeur_mm:.2f} mm")

    # On affiche le biais d'étalonnage séparément (celui qui faisait exploser le calcul)
    # if dist is not None:
    #     print(f"⚠️ Biais d'étalonnage de la base (Calculé vs Qualisys) : {delta_dist_mm:.2f} mm")


if __name__ == "__main__":
    synthese()
