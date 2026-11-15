"""Esquemas Pydantic para la extracción estructurada (Gemini devuelve JSON que se valida acá)."""

from typing import Literal, Optional

from pydantic import BaseModel, Field

TIPOS = ("rodaje", "series", "fondo", "carrera", "regenerativo", "otro")


class Entrenamiento(BaseModel):
    """Un entrenamiento de running extraído de un texto o de una captura de reloj/app."""

    entendido: bool = Field(description="false si el contenido no describe un entrenamiento de running")
    km: Optional[float] = Field(default=None, description="distancia recorrida en kilómetros")
    minutos: Optional[float] = Field(default=None, description="duración total en minutos (puede tener decimales)")
    tipo: Literal["rodaje", "series", "fondo", "carrera", "regenerativo", "otro"] = "rodaje"
    notas: Optional[str] = Field(default=None, description="detalle breve extra (sensaciones, clima), si lo hay")

    def es_valido(self) -> bool:
        """Solo se guarda si hay distancia y tiempo razonables."""
        return bool(self.entendido and self.km and self.minutos and 0 < self.km <= 1000 and 0 < self.minutos <= 1440)


ESQUEMA_ENTRENAMIENTO = Entrenamiento.model_json_schema()
