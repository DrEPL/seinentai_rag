import os
import time
import shutil
import yaml
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# === Config des services Docker Compose ===
SERVICES = {
    # "mongo": "containers/mongo/docker-compose.yml",
    # "kafka-tai": "containers/kafka-tai/docker-compose.yml",
    # "minio-tai": "containers/minio-tai/docker-compose.yml",
    "qdrant-tai": "containers/qdrant-tai/docker-compose.yml",
    # "postgres": "containers/postgres/docker-compose.yml",
}

# === Fonctions de gestion Docker ===
def get_services_from_compose(yaml_path):
    with open(yaml_path, 'r', encoding='utf-8') as file:
        try:
            compose_content = yaml.safe_load(file)
            return list(compose_content.get("services", {}).keys())
        except yaml.YAMLError as e:
            print(f"[ERREUR] Lecture YAML : {e}")
            return []

def is_container_running(container_name):
    try:
        result = subprocess.run([
            "docker", "ps", "--filter", f"name={container_name}", "--format", "{{.Names}}"
        ], stdout=subprocess.PIPE, text=True)
        return container_name in result.stdout.strip().split("\n")
    except Exception as e:
        print(f"[ERREUR] Vérification conteneur : {e}")
        return False

def remove_container_if_running(containers, compose_file):
    try:
        subprocess.run(["docker-compose", "-f", compose_file, "down"], check=True)
        print(f"[INFO] Conteneurs arrêtés : {containers}")
    except subprocess.CalledProcessError as e:
        print(f"[ERREUR] Arrêt conteneur : {e}")


def run_docker_container(containers, compose_file, env_file=".env"):
    try:
        # Chemins absolus
        compose_path = os.path.abspath(compose_file)
        env_path = os.path.abspath(env_file)
        compose_dir = os.path.dirname(compose_path)

        # Vérifications
        if not os.path.exists(compose_path):
            raise FileNotFoundError(f"Fichier introuvable : {compose_path}")
        if not os.path.exists(env_path):
            raise FileNotFoundError(f"Fichier .env introuvable : {env_path}")

        # Affiche le contenu du .env pour debug
        #with open(env_path) as f:
        #    print(f"[DEBUG] Contenu de {env_file}:\n" + f.read())

        # Lancement Docker
        print(f"[INFO] Lancement de {containers} depuis {compose_file}...")
        subprocess.run(
            [
                "docker-compose",
                "--env-file", env_path,
                "-f", compose_path,
                #"up","-d", "--force-recreate"
                "up", "--build","-d", "--force-recreate"
            ] + containers,
            check=True,
            cwd=compose_dir
        )
        print(f"[OK] Conteneurs lancés : {containers}")

    except Exception as e:
        print(f"[ERREUR] Lancement conteneur : {e}")

def build_docker_image(compose_path):
    try:
        print(f"[BUILD] Dossier : {compose_path}")
        subprocess.run([
            "docker-compose", "build", "--no-cache"
        ], cwd=compose_path, check=True, capture_output=True, text=True)
        print("[OK] Build terminé.")
    except Exception as e:
        print(f"[ERREUR] Build : {e}")


def create_common_networks(networks=[("seinentai_net", "bridge")]):
    try:
        result = subprocess.run(["docker", "network", "ls", "--format", "{{.Name}}"],
                                stdout=subprocess.PIPE, text=True, check=True)
        existing = result.stdout.strip().split("\n")

        for name, driver in networks:
            if name not in existing:
                subprocess.run(["docker", "network", "create", "--driver", driver, name], check=True)
                print(f"[OK] Réseau créé : {name}")
            else:
                print(f"[INFO] Réseau déjà présent : {name}")
    except Exception as e:
        print(f"[ERREUR] Réseau : {e}")


def wait_seconds(seconds=30, msg="Container prêt..."):
    time.sleep(seconds)
    print(f"[INFO] {msg}")

# === MAIN EXECUTION ===
create_common_networks()

# Build jupiterhub
jupyter_dir = os.path.join(BASE_DIR, "container","jupiterhub")


"""
# === Copie des scripts Spark dans le volume partagé ===
source_dir = os.path.join(BASE_DIR, "job")
dest_dir = os.path.join(BASE_DIR, "database", "spark", "spark-scripts")
os.makedirs(dest_dir, exist_ok=True)

for file_name in os.listdir(source_dir):
    source_file = os.path.join(source_dir, file_name)
    dest_file = os.path.join(dest_dir, file_name)

    if os.path.isfile(source_file):
        shutil.copy2(source_file, dest_file)
        print(f"Copié : {file_name}")
"""

# Lancer les services
for name, rel_path in SERVICES.items():
    full_compose_path = os.path.join(BASE_DIR, rel_path)
    if not os.path.exists(full_compose_path):
        print(f"[ERREUR] Compose introuvable : {full_compose_path}")
        continue

    containers = get_services_from_compose(full_compose_path)

    if not all(is_container_running(c) for c in containers):
        print(f"[INFO] Redémarrage : {containers}")
        remove_container_if_running(containers, full_compose_path)
        run_docker_container(containers, full_compose_path)
    else:
        print(f"[OK] Déjà en cours : {containers}")

wait_seconds()

def stop_all():
    for rel_path in SERVICES.values():
        full_path = os.path.join(BASE_DIR, rel_path)
        if os.path.exists(full_path):
            containers = get_services_from_compose(full_path)
            remove_container_if_running(containers, full_path)
            print(f"[INFO] Arrêt de : {full_path}")

# stop_all()