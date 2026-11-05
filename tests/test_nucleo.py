"""Controles sin pesos ni red: límites, clases, media de tramos y caché."""
import importlib
import math
import os
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import nucleo


class ValidacionTests(unittest.TestCase):
    def test_vacio_y_tipo_incorrecto_rechazados_sin_cargar(self):
        for value in ("", "  \n", None, 25):
            with self.subTest(value=value), patch.object(nucleo,"cargar_modelo") as carga:
                with self.assertRaises(ValueError):
                    nucleo.predecir(value)
                carga.assert_not_called()

    def test_limite_exacto_y_no_recorte(self):
        self.assertEqual(nucleo.validar_texto("a"*2000), "a"*2000)
        self.assertEqual(nucleo.validar_texto("  ejemplo  "), "  ejemplo  ")
        with self.assertRaises(ValueError):
            nucleo.validar_texto("a"*2001)

    def test_clases_permutadas_se_leen_de_config(self):
        cfg=SimpleNamespace(id2label={0:"POS",1:"NEG",2:"NEU"})
        self.assertEqual(nucleo.indices_clases(cfg),{"POS":0,"NEG":1,"NEU":2})

    def test_clases_ambiguas_o_faltantes_rechazadas(self):
        for mapa in ({0:"LABEL_0",1:"LABEL_1",2:"LABEL_2"}, {0:"NEG",1:"NEU"},
                     {0:"NEG",1:"NEG",2:"POS"}, {0:"NEG",1:"NEU",3:"POS"}):
            with self.subTest(mapa=mapa), self.assertRaises(nucleo.ErrorModelo):
                nucleo.indices_clases(SimpleNamespace(id2label=mapa))

    def test_falta_token_error_claro_sin_exponer_config(self):
        with patch.dict(os.environ,{"M1_REPO_ID":"autor/modelo","M1_REVISION":"a"*40},clear=True):
            with self.assertRaisesRegex(nucleo.ErrorModelo,"HF_TOKEN") as error:
                nucleo.cargar_modelo("M1")
            self.assertNotIn("autor/modelo",str(error.exception))


class InferenciaTests(unittest.TestCase):
    def tearDown(self):
        nucleo.liberar_cache()

    def test_media_softmax_con_overflow_y_orden_de_config(self):
        import torch
        # Orden del checkpoint: POS, NEG, NEU. Cada fila ya tiene distribución
        # conocida; log(p) permite comprobar Softmax y su media sin copiar el núcleo.
        probs=torch.tensor([[0.6,0.3,0.1],[0.2,0.2,0.6]],dtype=torch.float32)
        tokenizer=MagicMock(return_value={"input_ids":torch.tensor([[1,2],[3,4]]),
                                         "attention_mask":torch.ones((2,2),dtype=torch.long),
                                         "overflow_to_sample_mapping":torch.tensor([0,0])})
        model=MagicMock(return_value=SimpleNamespace(logits=probs.log()))
        model.config=SimpleNamespace(id2label={0:"POS",1:"NEG",2:"NEU"})
        with patch.object(nucleo,"cargar_modelo",return_value=(tokenizer,model)), \
             patch("pysentimiento.preprocessing.preprocess_tweet",return_value="preparado") as preparar:
            result=nucleo.predecir("Texto sintético", "M3")
        preparar.assert_called_once_with("Texto sintético",lang="es")
        tokenizer.assert_called_once_with("preparado",return_tensors="pt",truncation=True,
                                          max_length=128,stride=32,return_overflowing_tokens=True,padding=True)
        self.assertNotIn("overflow_to_sample_mapping",model.call_args.kwargs)
        self.assertEqual(result["n_tramos"],2)
        self.assertEqual(result["etiqueta"],"positiva")
        for clase, esperado in {"NEG":25.0,"NEU":35.0,"POS":40.0}.items():
            self.assertAlmostEqual(result["porcentajes"][clase],esperado,places=4)
        self.assertEqual(len(result["porcentajes_por_tramo"]),2)
        self.assertAlmostEqual(sum(result["porcentajes"].values()),100.0,places=4)
        self.assertNotIn("texto",result)

    def test_fallo_no_expone_entrada_ni_error_interno(self):
        marker="CONTENIDO_PRIVADO_FICTICIO"
        tokenizer=MagicMock(side_effect=RuntimeError(marker))
        model=MagicMock();model.config=SimpleNamespace(id2label={0:"NEG",1:"NEU",2:"POS"})
        with patch.object(nucleo,"cargar_modelo",return_value=(tokenizer,model)), \
             patch("pysentimiento.preprocessing.preprocess_tweet",return_value=marker):
            with self.assertRaises(nucleo.ErrorModelo) as error:
                nucleo.predecir(marker)
        self.assertNotIn(marker,str(error.exception))

    def test_cache_reutiliza_uno_y_expulsa_anterior(self):
        model=MagicMock();model.to.return_value=model;model.eval.return_value=model
        model.config=SimpleNamespace(id2label={0:"NEG",1:"NEU",2:"POS"})
        def fuente(codigo):
            return {"ruta":codigo,"local":True,"revision":None,"token":False}
        with patch.object(nucleo,"_fuente",side_effect=fuente), \
             patch("transformers.AutoTokenizer.from_pretrained",return_value=object()) as tok_load, \
             patch("transformers.AutoModelForSequenceClassification.from_pretrained",return_value=model) as mod_load:
            primero=nucleo.cargar_modelo("M1")
            repetido=nucleo.cargar_modelo("M1")
            self.assertIs(repetido[0],primero[0])
            self.assertIs(repetido[1],primero[1])
            self.assertEqual(tok_load.call_count,1)
            nucleo.cargar_modelo("M2")
            self.assertEqual(len(nucleo._CACHE),1)
            self.assertEqual(next(iter(nucleo._CACHE))[0],"M2")
            nucleo.cargar_modelo("M1")
            self.assertEqual(mod_load.call_count,3)
            self.assertEqual(len(nucleo._CACHE),1)
            self.assertFalse(mod_load.call_args.kwargs["trust_remote_code"])
            self.assertTrue(mod_load.call_args.kwargs["use_safetensors"])


if __name__ == "__main__":
    unittest.main()
