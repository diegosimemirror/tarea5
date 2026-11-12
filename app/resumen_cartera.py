# ============================================================
# MÓDULO COMPARTIDO: resumir un grupo de inversiones en los indicadores de cartera
# Lo usan el Proceso 7 (scripts/07_indicadores.py) y la app (app/app.py). Así, la app calcula los mismos indicadores para
# cualquier selección: un ministerio, un gobierno regional, un pliego, una unidad ejecutora o un portafolio armado a mano.
# Insumo:    filas de indicadores_proyecto.parquet (una por inversión)
# Resultado: una fila (pd.Series) con las cifras de las tarjetas de "¿Cómo está la cartera?"
# ============================================================

# pandas: tablas (se instala una vez)
import pandas as pd

def proporcion(a, b):
    """a / b, o faltante si b es 0 o falta (evita divisiones entre cero)."""
    return a / b if pd.notna(b) and b != 0 else float("nan")

# Cinco grupos de financiamiento (P5), en orden de prioridad: (nombre, clave para las columnas)
GRUPOS_FIN = [("Con presupuesto 2026", "con_pim"), ("Programado para 2026, sin presupuesto", "prog_2026_sin_pim"),
              ("Programado para 2027 en adelante", "prog_2027"), ("Sin financiamiento – le falta ejecutar", "sin_fin_falta"),
              ("Sin financiamiento – prácticamente terminado", "sin_fin_terminado")]

def resumen(g):
    """Resume un grupo de inversiones en una fila de indicadores.
    Antes: una fila por inversión (con las columnas de indicadores_proyecto) | Después: una sola fila con totales,
    porcentajes y conteos. Si el grupo está vacío, los porcentajes quedan como faltantes."""
    pim = g["pim_2026"].sum(); dev = g["dev_2026"].sum()
    comp = g["desv_total"].notna()
    con_pim = g["pim_2026"] > 0
    fila = {
        "n": len(g), "costo": g["costo"].sum(),
        # P1
        "n_con_brecha": int(g["tiene_brecha"].sum()), "pct_con_brecha": g["tiene_brecha"].mean(),
        "n_varias_brechas": int((g["n_brechas_total"] >= 2).sum()),
        # P2
        "pim_2026": pim, "dev_2026": dev, "certificado_2026": g["certificado_2026"].sum(),
        "pendiente_2026": g["pendiente_2026"].sum(), "pct_pendiente_2026": proporcion(g["pendiente_2026"].sum(), pim),
        "n_con_pim": int(con_pim.sum()), "n_mas_mitad_pendiente": int((g["pct_pendiente_2026"] > 0.5).sum()),
        "n_sin_gasto_2026": int((con_pim & (g["dev_2026"] == 0)).sum()),
        "saldo_total": g["saldo_total"].sum(), "pct_saldo_total": proporcion(g["saldo_total"].sum(), g["costo"].sum()),
        # P3
        "viable_comparable": g.loc[comp, "viable"].sum(), "costo_comparable": g.loc[comp, "costo"].sum(),
        "desv_total": g["desv_total"].sum(), "pct_desv_total": proporcion(g["desv_total"].sum(), g.loc[comp, "viable"].sum()),
        "n_subio": int((g["pct_desv_total"] > 0.001).sum()), "n_bajo": int((g["pct_desv_total"] < -0.001).sum()),
        "n_subio_mas_20": int((g["pct_desv_total"] > 0.2).sum()), "n_mas_que_duplico": int((g["pct_desv_total"] > 1).sum()),
        "n_con_laudo": int((g["laudo"] > 0).sum()), "laudo_total": g["laudo"].sum(),
        # P4
        "n_reporta_problemas": int((g["clase_problema"] == "Reporta problemas").sum()),
        "n_dice_sin_problemas": int((g["clase_problema"] == "Dice que no hay problemas").sum()),
        "n_sin_seguimiento": int(g["clase_problema"].isin(["Sin reporte de seguimiento", "Sin texto de problemas"]).sum()),
        **{"n_" + c: int(g[c].sum()) for c in g.columns if c.startswith("tema_")},
        # P7
        "n_atrasados": int(g["atrasado"].sum()),
        "mediana_meses_atraso": g.loc[g["atrasado"], "meses_atraso"].median(),
        "n_atraso_mas_12": int((g["meses_atraso"] > 12).sum()), "n_atraso_mas_36": int((g["meses_atraso"] > 36).sum()),
        "programado_ene_oct": g["programado_ene_oct"].sum(), "devengado_ene_oct": g.loc[g["programado_ene_oct"] > 0, "devengado_ene_oct"].sum(),
        "n_bajo_70_programacion": int((g["pct_cumple_programacion"] < 0.7).sum()),
        # Avance frente a gasto (solo proyectos con avance declarado en 2026, comparados en la misma fecha)
        "n_avance_declarado": int((g["avance_fuente"] == "declarado por la entidad").sum()),
        "n_comparables_avance": int(g["valor_avanzado"].notna().sum()),
        "n_alerta_gasto_avance": int(g["alerta_gasto_avance"].sum()),
        "valor_avanzado": g["valor_avanzado"].sum(), "gastado_a_la_declaracion": g["gastado_a_la_declaracion"].sum(),
        "costo_comparable_avance": g.loc[g["valor_avanzado"].notna(), "costo"].sum(),
    }
    fila["pct_cumple_programacion"] = proporcion(fila["devengado_ene_oct"], fila["programado_ene_oct"])
    fila["pct_avance_declarado"] = proporcion(fila["valor_avanzado"], fila["costo_comparable_avance"])
    fila["pct_gastado_comparable"] = proporcion(fila["gastado_a_la_declaracion"], fila["costo_comparable_avance"])
    fila["indice_avance_gasto"] = proporcion(fila["valor_avanzado"], fila["gastado_a_la_declaracion"])
    # P5: los cinco grupos con su número, costo y saldo; y los tres niveles en porcentaje de proyectos y de costo
    for grupo, clave in GRUPOS_FIN:
        m = g["financiamiento"] == grupo
        fila[f"n_{clave}"], fila[f"costo_{clave}"], fila[f"saldo_{clave}"] = int(m.sum()), g.loc[m, "costo"].sum(), g.loc[m, "saldo_total"].sum()
    for nivel, clave in [("Con presupuesto 2026", "presupuesto"), ("Programado, sin presupuesto", "programado"),
                         ("Sin financiamiento ni programación", "sin_nada")]:
        m = g["nivel_financiamiento"] == nivel
        fila[f"pct_n_{clave}"] = m.mean()
        fila[f"pct_costo_{clave}"] = proporcion(g.loc[m, "costo"].sum(), g["costo"].sum())
    return pd.Series(fila)
