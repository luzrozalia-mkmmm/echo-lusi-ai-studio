import os
import sys
import torch
from pydub import AudioSegment

# Dodaj RVC do ścieżki
sys.path.append("/home/ubuntu/RVC-WebUI")

from infer.modules.vc.modules import VC

def infer_rvc(input_path, model_name, output_path):
    print(f"Konwersja głosu dla: {input_path}")
    rvc_root = "/home/ubuntu/RVC-WebUI"
    # Zmiana katalogu roboczego na rvc_root, aby RVC znalazło configs/
    os.chdir(rvc_root)
    os.environ["weight_root"] = os.path.join(rvc_root, "assets/weights")
    os.environ["index_root"] = os.path.join(rvc_root, "logs")
    
    # Inicjalizacja VC
    from configs.config import Config
    config = Config()
    config.device = "cpu"
    config.is_half = False
    vc = VC(config)
    
    # Załaduj model
    model_path = f"{model_name}.pth" # VC.get_vc szuka w assets/weights
    
    # Monkeypatch VC.get_vc to handle models without 'config' key
    import torch
    original_get_vc = vc.get_vc
    def patched_get_vc(sid, *args):
        person = f"{os.environ['weight_root']}/{sid}"
        cpt = torch.load(person, map_location='cpu')
        if 'weight' not in cpt: cpt['weight'] = cpt['model']
        if 'config' not in cpt:
            # Domyślne wartości dla modelu v1 40k (19 argumentów)
            cpt['config'] = [1025, 32, 192, 192, 768, 2, 6, 3, 0, "1", [3, 7, 11], [[1, 3, 5], [1, 3, 5], [1, 3, 5]], [10, 10, 2, 2], 512, [16, 16, 4, 4], 109, 256, 40000]
            cpt['version'] = 'v2'
        torch.save(cpt, person)
        return original_get_vc(sid, *args)
    vc.get_vc = patched_get_vc
    vc.get_vc(model_path)

    
    # Parametry konwersji
    # sid, input_audio_path, f0_up_key, f0_file, f0_method, file_index, file_index2, index_rate, filter_radius, resample_sr, rms_mix_rate, protect
    # f0_up_key: przesunięcie tonacji (0 dla braku zmian)
    # f0_method: metoda wyciągania f0 (np. 'pm', 'harvest', 'crepe', 'rmvpe')
    
    print("Uruchamianie konwersji...")
    # RVC inference zwraca (message, audio_data)
    # sid=0 (zazwyczaj pierwszy głos w modelu)
    # f0_up_key=0 (zachowaj oryginalną tonację)
    # f0_method='pm' (szybka metoda na CPU)
    # index_rate=0.75 (balans między modelem a indeksem)
    
    # Uwaga: infer.modules.vc.modules.VC.vc_single to funkcja do konwersji
    # Musimy sprawdzić dokładną sygnaturę w kodzie RVC
    
    # Dla uproszczenia w PoC użyjemy wywołania przez subprocess jeśli API jest zbyt z    # Uruchom CLI do konwersji
    cmd = [
        "python3", os.path.join(rvc_root, "tools/infer_cli.py"),
        "--f0up_key", "0",
        "--input_path", input_path,
        "--index_path", "",
        "--f0method", "pm",
        "--opt_path", output_path,
        "--model_name", model_name + ".pth",
        "--index_rate", "0.66",
        "--device", "cpu",
        "--is_half", "False",
        "--filter_radius", "3",
        "--resample_sr", "0",
        "--rms_mix_rate", "1",
        "--protect", "0.33"
    ]
    
    # W środowisku bez GPU i z ograniczonym RAM, duże pliki mogą powodować SIGKILL.
    # Optymalizacja: Przetwarzanie fragmentów (jeśli plik jest duży)
    # Dla PoC spróbujemy najpierw z mniejszym modelem lub upewnimy się, że proces ma szansę.
    
    try:
        print("Uruchamianie konwersji (może to potrwać kilka minut na CPU)...")
        # Zwiększamy limit pamięci dla Pythona jeśli to możliwe lub po prostu liczymy na optymalizację RVC
        subprocess.run(cmd, check=True)
        print(f"Konwersja zakończona: {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"Błąd konwersji: {e}")
        if "SIGKILL" in str(e) or "9" in str(e):
            print("Wykryto brak pamięci. Próba optymalizacji nie powiodła się. Spróbuję użyć lżejszego modelu.")
        return False

if __name__ == "__main__":
    import subprocess
    input_vocal = "/home/ubuntu/voice_clone_project/output/htdemucs/echo_lusi_przeczekam/vocals_vshort.wav"
    output_vocal = "/home/ubuntu/voice_clone_project/output/user_voice_vocal.wav"
    infer_rvc(input_vocal, "user_voice", output_vocal)
