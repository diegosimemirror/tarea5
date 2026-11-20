# ============================================================
# MÓDULO: ocultar datos personales en los textos del 12-B (lo usan los Procesos 3 y 11)
# Regla del proyecto: sin datos personales. Los nombres de personas («Ing. Juan Pérez») pasan a «[nombre omitido]» y los
# correos electrónicos a «[correo omitido]». La regla es prudente: puede ocultar alguna palabra de más, pero no deja
# nombres a la vista.
# ============================================================

# re: buscar y reemplazar patrones en el texto (viene con Python)
import re

PERSONA = re.compile(r"\b(Ing|ING|Sr|SR|Sra|SRA|Srta|Lic|LIC|Arq|ARQ|Dr|DR|Dra|DRA|Econ|ECON|Abog|ABOG|CPC|Mg|MG)\.\s*"
                     r"[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ]+){0,3}")
CORREO = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")


def ocultar(texto):
    """Antes: 'El Ing. Juan Pérez (jperez@x.pe) informa...' | Después: 'El Ing. [nombre omitido] ([correo omitido]) informa...'."""
    texto = CORREO.sub("[correo omitido]", str(texto or ""))
    return PERSONA.sub(lambda m: m.group(1) + ". [nombre omitido]", texto)
