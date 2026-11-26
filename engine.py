"""Motor de recomendaciones por reglas de asociación (sin reentrenamiento)."""
import json
from pathlib import Path
import pandas as pd

RULE_COLUMNS = {"antecedente", "consecuente", "support", "confidence", "lift"}
CATALOG_COLUMNS = {"producto", "precio_referencia", "codigo_producto"}


def load_data(data_dir="data"):
    folder = Path(data_dir)
    rules = pd.read_csv(folder / "reglas_streamlit.csv", encoding="utf-8-sig")
    catalog = pd.read_csv(folder / "catalogo_productos_precios.csv", encoding="utf-8-sig", dtype={"codigo_producto": "string"})
    if not RULE_COLUMNS.issubset(rules.columns):
        raise ValueError("El archivo de reglas no tiene todas las columnas necesarias")
    if not CATALOG_COLUMNS.issubset(catalog.columns):
        raise ValueError("El catálogo no tiene todas las columnas necesarias")
    if rules[list(RULE_COLUMNS)].isna().any().any() or catalog[list(CATALOG_COLUMNS)].isna().any().any():
        raise ValueError("Existen valores faltantes en campos obligatorios")
    catalog = catalog.copy()
    catalog["producto"] = catalog["producto"].astype(str)
    if catalog["producto"].duplicated().any():
        raise ValueError("El catálogo contiene descripciones duplicadas")
    catalog["precio_referencia"] = pd.to_numeric(catalog["precio_referencia"], errors="raise")
    if (catalog["precio_referencia"] < 0).any():
        raise ValueError("Existen precios negativos")
    parsed = []
    product_set = set(catalog["producto"])
    for index, rule in rules.iterrows():
        a = json.loads(rule["antecedente"])
        b = json.loads(rule["consecuente"])
        if not isinstance(a, list) or not isinstance(b, list) or not a or not b:
            raise ValueError(f"Regla {index}: formato JSON incorrecto")
        antecedent, consequent = frozenset(a), frozenset(b)
        if (antecedent & consequent) or not (antecedent | consequent).issubset(product_set):
            raise ValueError(f"Regla {index}: códigos no coincidentes o conjuntos solapados")
        for metric in ("support", "confidence", "lift"):
            if not pd.notna(rule[metric]):
                raise ValueError(f"Regla {index}: métrica ausente")
        parsed.append({
            "antecedente": antecedent,
            "consecuente": consequent,
            "support": float(rule["support"]),
            "confidence": float(rule["confidence"]),
            "lift": float(rule["lift"]),
        })
    return parsed, catalog.sort_values("producto").reset_index(drop=True)


def recommendations(basket, rules, min_confidence=0.50, min_lift=1.2, min_support=0.01):
    """Coincidencia completa de antecedentes; mejor regla por producto recomendado."""
    basket = set(basket)
    candidates = {}
    for rule in rules:
        if (rule["support"] < min_support or rule["confidence"] < min_confidence
                or rule["lift"] <= min_lift or not rule["antecedente"].issubset(basket)):
            continue
        for product in rule["consecuente"] - basket:
            candidate = {
                "producto": product,
                "antecedente": ", ".join(sorted(rule["antecedente"])),
                "consecuente_completo": ", ".join(sorted(rule["consecuente"])),
                "support": rule["support"],
                "confidence": rule["confidence"],
                "lift": rule["lift"],
            }
            old = candidates.get(product)
            if old is None or (candidate["confidence"], candidate["lift"], candidate["support"]) > (old["confidence"], old["lift"], old["support"]):
                candidates[product] = candidate
    return sorted(candidates.values(), key=lambda x: (-x["confidence"], -x["lift"], -x["support"], x["producto"]))
