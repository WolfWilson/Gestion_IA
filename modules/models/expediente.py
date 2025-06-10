"""
models/expediente.py
--------------------
Estructura de datos para un expediente PDF.
"""

from __future__ import annotations

from typing import Dict

from modules.helpers.cuils import validar_cuil


class Expediente:
    # ─────────────────────────────── init ────────────────────────────────
    def __init__(self, ruta_pdf: str) -> None:
        self.ruta_pdf: str = ruta_pdf

        # Checks básicos
        self.caratula_encontrada: bool = False
        self.formulario_inicio: bool = False

        # Renaper
        self.renaper_detectado: bool = False
        self.renaper_completo: bool = False

        # SINTyS
        self.sintys_detectado: bool = False
        self.sintys_ok: bool = False

        # Intercajas
        self.intercajas_detectado: bool = False
        self.intercajas_ok: bool = False

        # Fotos DNI
        self.fotos_dni_front: bool = False
        self.fotos_dni_back: bool = False

        # ANSES 4 pantallas y Cert. Negativa
        self.anses_detectado: bool = False
        self.anses_completo: bool = False
        self.certneg_detectada: bool = False
        self.certneg_ok: bool = False

        # Errores de lectura
        self.error_lectura: bool = False

        # Observaciones libres
        self.observaciones: list[str] = []

        # ──────────── NUEVO: gestión de CUILes ────────────
        # origen  →  cuil
        self.cuiles: Dict[str, str] = {}
        self.cuil_coherente: bool | None = None   # None = sin evaluar

    # ────────────────────────── helpers ───────────────────────────
    def agregar_observacion(self, mensaje: str) -> None:
        self.observaciones.append(mensaje)

    # ─────────────────── CUIL: registro y chequeo ─────────────────
    def registrar_cuil(self, origen: str, cuil: str | None) -> None:
        """
        Guarda el CUIL de *origen* y, de paso, valida el dígito verificador.
        No sobre-escribe si ya había un valor para ese origen.
        """
        if not cuil:
            return

        if origen in self.cuiles:
            # ya estaba registrado → posible re-chequeo
            if self.cuiles[origen] != cuil:
                self.agregar_observacion(
                    f"⚠ CUIL distinto reencontrado en {origen}: "
                    f"{self.cuiles[origen]} → {cuil}"
                )
        else:
            self.cuiles[origen] = cuil

        if not validar_cuil(cuil):
            self.agregar_observacion(f"⚠ CUIL con dígito verificador inválido: {cuil}")

    def verificar_consistencia_cuiles(self) -> None:
        """
        Marca `self.cuil_coherente` y agrega observaciones si existen
        discrepancias entre los CUILes registrados.
        """
        if not self.cuiles:
            self.cuil_coherente = False
            self.agregar_observacion("No se detectó CUIL en ningún informe.")
            return

        distintos = {c for c in self.cuiles.values() if c}
        self.cuil_coherente = len(distintos) == 1

        if not self.cuil_coherente:
            lista = ", ".join(f"{k}:{v}" for k, v in self.cuiles.items())
            self.agregar_observacion(f"⚠ Discrepancia de CUIL entre informes → {lista}")
