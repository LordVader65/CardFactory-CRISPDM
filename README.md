# Simulador de ventas cruzadas (Online Retail II)

Aplicación Streamlit para presentar recomendaciones basadas en **404 reglas de asociación** calculadas previamente con Apriori en un notebook de CRISP-DM. Incluye 4.067 productos y precios históricos medianos.

## Ejecutar localmente

```bash
python -m venv .venv
# En Windows: .venv\Scripts\activate
# En macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Publicar en Streamlit Community Cloud

1. Crear un repositorio de GitHub y subir **el contenido de esta carpeta** (sin necesidad de subir el dataset original).
2. Entrar a https://share.streamlit.io y crear una aplicación a partir de ese repositorio.
3. Elegir la rama que contiene `app.py` y establecer `app.py` como archivo principal.
4. Publicar y compartir el enlace generado.

## Estructura

- `app.py`: interfaz para carrito, sugerencias y consulta de reglas.
- `engine.py`: lectura, validación de CSV y motor de reglas.
- `data/reglas_streamlit.csv`: antecedentes y consecuentes en JSON, soporte, confianza y lift.
- `data/catalogo_productos_precios.csv`: nombres, códigos representativos y precios históricos de referencia.
- `tests/test_engine.py`: pruebas básicas del motor y de la integridad de los datos.

## Consideraciones metodológicas

- La unidad de producto es la **descripción**, igual que en el modelado realizado en Colab. Un código se conserva solo como referencia en el catálogo.
- Si un producto no activa reglas, el simulador no sugerirá complementos. La interfaz permite filtrar por productos que sí aparecen como antecedentes.
- Si una regla tiene varios antecedentes, **todos** deben estar presentes en el carrito para activarla.
- Las reglas no son necesariamente causales ni garantizan un aumento de ventas.
- Los precios son medianas históricas; se muestran para fines didácticos, no para ventas actuales.
- Se ha mantenido intacto el conjunto de reglas compartido. La revisión manual de pertinencia comercial, disponibilidad de productos y la validación temporal deben abordarse antes de una implementación real.
