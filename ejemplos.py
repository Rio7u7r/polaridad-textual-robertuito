"""Ejemplos creados para demostrar la interfaz, sin datos del corpus."""

EJEMPLOS = {
    "E1 · Satisfacción": "Me alegra haber terminado el trabajo; aprendí mucho y quedé satisfecho.",
    "E2 · Descontento": "La actividad salió mal y me decepcionó perder tanto tiempo.",
    "E3 · Información": "La clase empieza a las ocho y el material está en la biblioteca.",
    "E4 · Opinión mixta": "El tema me interesó, aunque la explicación fue confusa y faltó tiempo.",
    "E5 · Lenguaje informal": "Qué bien salió todo 😊, al final sí pudimos terminar juntos!",
    "E6 · Texto largo": (
        "Hoy revisamos los apuntes para preparar una actividad de clase. "
        "Al principio me preocupó no entender las instrucciones y sentí frustración "
        "porque algunos pasos resultaban confusos. Después organizamos las tareas "
        "con calma y cada integrante explicó una parte del ejercicio. La sala "
        "tenía varias mesas y una pizarra donde anotamos el horario. Me gustó "
        "que pudiéramos escuchar opiniones diferentes y resolver las dudas. "
        "Sin embargo, el ruido del pasillo dificultó la concentración y perdimos "
        "un rato buscando un material que no aparecía. Al terminar, revisamos "
        "el resultado y dejamos una lista de asuntos pendientes para la próxima "
        "sesión. Estoy satisfecho con el esfuerzo del grupo, aunque todavía "
        "hay detalles que debemos mejorar. Mañana continuaremos con la revisión "
        "en el mismo horario y llevaremos los cuadernos necesarios. "
        "La experiencia tuvo momentos agradables y dificultades, por eso quiero "
        "valorar tanto lo que logramos como lo que quedó incompleto."
    ),
}


def texto_ejemplo(nombre: str) -> str:
    """Devuelve solo ejemplos locales, nunca predicciones cacheadas."""
    return EJEMPLOS.get(nombre, "")
