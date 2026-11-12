"""Revisión y selección de los pesos incluidos en la copia portátil."""
from datetime import datetime
from hashlib import file_digest
import json
from pathlib import Path
from shutil import copytree
from tempfile import TemporaryDirectory
from uuid import uuid4


def verificar_modelo(carpeta, modelo):
    carpeta = Path(carpeta)
    registro = json.loads((carpeta / "ejecucion.json").read_text(encoding="utf-8"))
    if registro["modelo"] != modelo:
        raise ValueError(f"La carpeta no corresponde a {modelo}.")
    for nombre, esperado in registro["artefactos_sha256"].items():
        archivo = carpeta / nombre
        if not archivo.is_relative_to(carpeta) or Path(nombre).name != nombre:
            raise ValueError("El registro contiene una ruta inesperada.")
        with archivo.open("rb") as entrada:
            actual = file_digest(entrada, "sha256").hexdigest()
        if actual != esperado:
            raise ValueError(f"{modelo}: {nombre} difiere del registro de los pesos.")
    return registro


def preguntar_modelo(raiz, modelo, respuesta=None, permitir_preparacion=False):
    raiz = Path(raiz)
    corrida = json.loads((raiz / "corrida.json").read_text(encoding="utf-8"))["corrida"]
    carpeta = raiz / "modelos" / corrida / modelo
    if not (carpeta / "ejecucion.json").is_file():
        if not permitir_preparacion:
            raise FileNotFoundError(f"Faltan los pesos de {modelo}. Restaura la copia guardada o activa ENTRENAR_MODELO para preparar un ajuste nuevo.")
        print(f"{modelo}: no hay un modelo guardado en {corrida}. Se preparará a continuación.")
        return False
    registro = verificar_modelo(carpeta, modelo)
    if modelo == "M0":
        print("M0: ya hay pesos del modelo base publicado. Épocas de ajuste local: 0.")
    else:
        print(f"{modelo}: ya hay un modelo entrenado con pesos y {registro['epocas']:g} épocas.")
    print(f"Carpeta: modelos/{corrida}/{modelo}")
    validas = {"sí": True, "si": True, "s": True, "no": False, "n": False}
    if respuesta is not None:
        respuesta = respuesta.strip().lower()
        if respuesta not in validas:
            raise ValueError("La respuesta preseleccionada debe ser sí o no.")
        print(f"¿Quieres cargar este modelo? (sí/no): {respuesta}")
        return validas[respuesta]
    while True:
        respuesta = input("¿Quieres cargar este modelo? (sí/no): ").strip().lower()
        if respuesta in validas:
            return validas[respuesta]
        print("Escribe sí o no.")


def nueva_corrida(raiz, modelo):
    """Prepara los antecesores y selecciona una corrida nueva después de copiarlos."""
    raiz = Path(raiz)
    configuracion = raiz / "corrida.json"
    anterior = json.loads(configuracion.read_text(encoding="utf-8"))["corrida"]
    antecesores = {"M0": (), "M1": ("M0",), "M2": ("M0", "M1")}[modelo]
    nombre = datetime.now().strftime("ajuste_%Y%m%d_%H%M%S_") + uuid4().hex[:8]
    modelos = raiz / "modelos"
    with TemporaryDirectory(dir=modelos) as temporal:
        preparada = Path(temporal) / nombre
        preparada.mkdir()
        for antecesor in antecesores:
            origen = modelos / anterior / antecesor
            verificar_modelo(origen, antecesor)
            copytree(origen, preparada / antecesor)
        preparada.rename(modelos / nombre)
    temporal_config = raiz / f".corrida_{uuid4().hex}.json"
    temporal_config.write_text(json.dumps({"corrida": nombre}, indent=2), encoding="utf-8")
    temporal_config.replace(configuracion)
    print(f"Nueva corrida seleccionada: {nombre}")
    return nombre
