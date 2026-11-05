# Paridad y tiempos locales

Estado: **verificado**. Casos: 24. Se utilizaron exclusivamente ejemplos sintéticos.

Referencia: cuaderno 08 original, celda 5 (índice cero), transcripción con retorno ampliado de probabilidades y tramos. CPU float32 en ambos lados. El cuaderno original devuelve solo etiqueta.

Criterio: diferencia estrictamente menor que 0,001 en probabilidad de 0 a 1, equivalente a 0,1 puntos porcentuales. Se informa también la diferencia en puntos porcentuales sin cambiar de escala silenciosamente.

| Modelo | Ejemplo | Tokens | Tramos | Diferencia máxima (prob.) | Diferencia (pp) | Inferencia caliente (s) | Cumple |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| M0 | E1 | 13 | 1 | 0 | 0 | 0.031323 | Sí |
| M0 | E2 | 11 | 1 | 0 | 0 | 0.027222 | Sí |
| M0 | E3 | 15 | 1 | 0 | 0 | 0.035483 | Sí |
| M0 | E4 | 14 | 1 | 0 | 0 | 0.033206 | Sí |
| M0 | E5 | 22 | 1 | 0 | 0 | 0.033870 | Sí |
| M0 | E6 | 171 | 2 | 0 | 0 | 0.235240 | Sí |
| M1 | E1 | 13 | 1 | 0 | 0 | 0.030515 | Sí |
| M1 | E2 | 11 | 1 | 0 | 0 | 0.031150 | Sí |
| M1 | E3 | 15 | 1 | 0 | 0 | 0.034016 | Sí |
| M1 | E4 | 14 | 1 | 0 | 0 | 0.034430 | Sí |
| M1 | E5 | 22 | 1 | 0 | 0 | 0.039454 | Sí |
| M1 | E6 | 171 | 2 | 0 | 0 | 0.228235 | Sí |
| M2 | E1 | 13 | 1 | 0 | 0 | 0.030850 | Sí |
| M2 | E2 | 11 | 1 | 0 | 0 | 0.030005 | Sí |
| M2 | E3 | 15 | 1 | 0 | 0 | 0.033289 | Sí |
| M2 | E4 | 14 | 1 | 0 | 0 | 0.028766 | Sí |
| M2 | E5 | 22 | 1 | 0 | 0 | 0.036490 | Sí |
| M2 | E6 | 171 | 2 | 0 | 0 | 0.246981 | Sí |
| M3 | E1 | 13 | 1 | 0 | 0 | 0.036208 | Sí |
| M3 | E2 | 11 | 1 | 0 | 0 | 0.028453 | Sí |
| M3 | E3 | 15 | 1 | 0 | 0 | 0.031286 | Sí |
| M3 | E4 | 14 | 1 | 0 | 0 | 0.030174 | Sí |
| M3 | E5 | 22 | 1 | 0 | 0 | 0.040377 | Sí |
| M3 | E6 | 171 | 2 | 0 | 0 | 0.228468 | Sí |

| Modelo | Carga fría (s) | Primera inferencia (s) | Total primera llamada (s) | Mediana caliente (s) |
| --- | ---: | ---: | ---: | ---: |
| M0 | 6.211969 | 1.459329 | 7.671318 | 0.033538 |
| M1 | 0.211713 | 0.839456 | 1.051187 | 0.034223 |
| M2 | 0.188436 | 0.753274 | 0.941728 | 0.032070 |
| M3 | 0.217362 | 0.789189 | 1.006565 | 0.033747 |

Una carga fría de aplicación y una medición caliente por ejemplo; caché de disco del sistema no vaciada. No es benchmark de Hugging Face.

Las versiones, huellas y porcentajes completos se conservan en paridad.json y paridad.csv. Las salidas no contienen los textos introducidos ni rutas personales.
