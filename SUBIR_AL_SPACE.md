# Subir la aplicación a Hugging Face Spaces

Esta guía separa la aplicación, los pesos y las comprobaciones. No es necesario
publicar el corpus. No pegue ningún token en un chat, documento ni archivo del
proyecto.

## 1. Comprobar la cuenta y el alojamiento

Entre en [Hugging Face](https://huggingface.co/) con su cuenta. Compruebe la opción
de crear un Space Gradio antes de subir archivos. La documentación consultada el
1 de noviembre de 2026 indica que crear Gradio o Docker requiere PRO para cuentas
personales, o Team/Enterprise para organizaciones. CPU Basic no tiene tarifa por
hora, pero eso no elimina el requisito de plan. Las cuentas gratuitas elegibles
pueden tener hasta dos Spaces Gradio ZeroGPU; esta entrega no cambia a ZeroGPU.

Fuente: [documentación de Spaces](https://huggingface.co/docs/hub/spaces-overview).
No contrate ni active recursos de pago solo para seguir esta guía. Si la cuenta
no permite CPU, conserve la ejecución local y decida el alojamiento antes de
continuar. El estado y la reactivación tras inactividad se deben comprobar en
la configuración real del Space; aquí no se atribuye un plazo no verificado.

## 2. Revisar los modelos antes de compartirlos

La ficha original de M0 identifica TASS y RoBERTuito, pero no basta para acreditar
todos los permisos de redistribución de las adaptaciones. Revise las condiciones
del modelo base, de SMPS y de los datos locales. Mantener los repositorios
privados no sustituye los permisos necesarios. No se asigna una licencia nueva
a los pesos en esta entrega.

Las carpetas de M2 y M3 son copias de pesos históricos. No presente estos pesos
como entrenamientos nuevos con `preprocess_tweet`. No cambie las métricas ni
reentrene para completar la subida.

El programa `preparar_modelos.py` prepara carpetas por lista permitida y elimina
las rutas personales de la configuración. No sube nada. Ejecútelo así, dando
sus carpetas reales y una carpeta de salida nueva fuera de `space/`:

```text
python preparar_modelos.py --m1 "RUTA_M1" --m2 "RUTA_M2" --m3 "RUTA_M3" --salida "CARPETA_NUEVA"
```

Conserve el manifiesto de la exportación. Compare sus huellas de pesos con
`checkpoint_manifest.json`. Si difieren, detenga la publicación y revise qué
versión está preparando. El script rechaza pesos distintos a los auditados.

## 3. Crear tres repositorios privados de modelos

En su perfil elija **New model**. Cree, uno por uno, estos nombres y marque
**Private**:

- `SU_USUARIO/robertuito-bol-m1`
- `SU_USUARIO/robertuito-bol-m2`
- `SU_USUARIO/robertuito-bol-m3`

`SU_USUARIO` representa el nombre de su propia cuenta; no debe dejarse literal.
En **Files and versions**, use **Add file / Upload files**. En cada repositorio
suba únicamente el contenido de su carpeta exportada correspondiente: config,
pesos safetensors, archivos del tokenizador y README. No suba la carpeta padre,
el manifiesto privado, tablas, publicaciones, notebooks ni archivos de sesión.
Abra el commit de la carga y copie su identificador completo de 40 caracteres.

## 4. Crear el acceso de lectura

En **Settings / Access Tokens**, cree un token de alcance específico que permita
leer esos tres repositorios. No necesita permiso de escritura para que la
aplicación funcione. Introdúzcalo directamente en el sitio de Hugging Face y
conserve el secreto con seguridad; nunca lo ponga en código o capturas.

Fuente: [tokens de acceso](https://huggingface.co/docs/hub/security-tokens).

## 5. Crear el Space y subir la aplicación

Cuando el plan lo permita, elija **New Space**, un nombre propio y SDK **Gradio**.
Para que el tutor lo abra sin pertenecer al repositorio, compruebe qué visibilidad
le sirve: un Space privado requiere acceso; uno público expone el código.
Mantenga privados los tres repositorios de pesos en ambos casos.

Use CPU Basic si su cuenta lo admite. Suba los siguientes archivos en la raíz
del Space (no dentro de otra carpeta llamada `space`):

- `app.py`, `nucleo.py`, `ui_render.py`, `ejemplos.py`.
- `requirements.txt`, `README.md`, `ficha_modelos.json`, `checkpoint_manifest.json`.
- `.gitignore` y, opcionalmente, `PROTOCOLO.md`.

En **Settings / Variables and secrets**, agregue como variables:

| Nombre | Valor |
| --- | --- |
| HF_MODEL_OWNER | Su usuario de Hugging Face |
| M1_REVISION | Commit completo del repositorio M1 |
| M2_REVISION | Commit completo del repositorio M2 |
| M3_REVISION | Commit completo del repositorio M3 |
| DEFAULT_MODEL | M3 |
| TORCH_NUM_THREADS | 2 |

Si los repositorios tienen otros nombres, configure también `M1_REPO_ID`,
`M2_REPO_ID`, `M3_REPO_ID` con sus nombres completos. Agregue **HF_TOKEN como
Secret**, nunca como variable pública. No configure rutas locales del equipo
en el Space.

## 6. Comprobar el funcionamiento publicado

Espere a que termine la construcción. Abra la aplicación en otra pestaña y
registre su URL real y el commit de código usado. Pruebe E1–E5, luego E6:
la entrada larga debe mostrar varios tramos y su promedio. En Comparar deben
aparecer cuatro resultados, o un mensaje preciso si falta acceso a un modelo.
Compruebe entrada vacía, texto de 2.000 caracteres y vista de celular.

La caché mantiene solo un modelo; comparar los cuatro vuelve a cargar pesos
desde disco y puede tardar. Registre los tiempos y la memoria del alojamiento:
los tiempos locales no prueban el rendimiento de Hugging Face. Si se agota
memoria, detenga la prueba y revise recursos; no suprima modelos silenciosamente.

## 7. Capturas y texto de tesis

Use exclusivamente ejemplos E1–E6 y registre capturas reales:

| Captura | Qué mostrar |
| --- | --- |
| C1 | Clasificar un texto corto con modelo, etiqueta y tres porcentajes |
| C2 | E6, cantidad de tramos, valores por tramo y promedio |
| C3 | Comparar con los cuatro resultados del mismo texto |
| C4 | Acerca de, métricas, procedencia y límites |
| C5 | Vista de celular legible, sin recortes horizontales |

Las capturas locales de esta entrega se identifican como locales; no sustituyen
estas comprobaciones en el Space. No publique capturas de Settings, secretos,
cuentas o datos del corpus. Solo después de abrir una URL funcional se puede
describir el prototipo como publicado. Actualice conjuntamente la sección 4.7,
la Tabla 2.2 y el párrafo 2.11, conservando el historial de versiones.
