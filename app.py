"""Simulador académico de ventas cruzadas con Online Retail II."""
from pathlib import Path
import pandas as pd
import streamlit as st
from engine import load_data, recommendations

BASE = Path(__file__).resolve().parent
st.set_page_config(page_title="Tienda de regalos | Recomendaciones", page_icon="🎁", layout="wide")
st.markdown("""<style>
.block-container {padding-top: 1.8rem; max-width: 1200px;}
[data-testid="stMetric"] {background: rgba(127,127,127,.07);padding: 14px;border-radius: 12px;}
.small-note {color: #777;font-size: .88rem}
</style>""", unsafe_allow_html=True)

@st.cache_data

def data():
    return load_data(BASE / "data")

try:
    rules, catalog = data()
except Exception as exc:
    st.error(f"No se pudieron cargar los datos: {exc}")
    st.stop()

by_name = catalog.set_index("producto")["precio_referencia"].to_dict()
all_products = catalog["producto"].tolist()
trigger_products = sorted(set().union(*(r["antecedente"] for r in rules)))
if "cart" not in st.session_state:
    st.session_state.cart = []

st.title("🎁 Tienda de regalos — simulador de ventas cruzadas")
st.caption("Prototipo académico CRISP-DM · Online Retail II · Reglas descubiertas con Apriori · Precios históricos de referencia")

tab_shop, tab_rules, tab_about = st.tabs(["🛒 Tienda y recomendaciones", "📈 Reglas del modelo", "ℹ️ Acerca del prototipo"])

with tab_shop:
    left, right = st.columns([1.18, 1], gap="large")
    with left:
        st.subheader("1. Construye tu carrito")
        with st.form("add_products", clear_on_submit=True):
            scope = st.radio("Explorar productos", ["Productos que pueden activar recomendaciones", "Catálogo completo"], horizontal=False)
            choices = trigger_products if scope.startswith("Productos que") else all_products
            selected = st.multiselect("Elige uno o varios artículos", options=choices, placeholder="Escribe parte del nombre...")
            add = st.form_submit_button("Agregar al carrito", type="primary", use_container_width=True)
        if add:
            st.session_state.cart = list(dict.fromkeys(st.session_state.cart + selected))
            st.rerun()
        if not st.session_state.cart:
            st.info("Agrega al menos un producto para obtener recomendaciones.")
        else:
            st.markdown("**Productos seleccionados**")
            for idx, item in enumerate(st.session_state.cart):
                name_col, price_col, remove_col = st.columns([5, 1.5, 1])
                name_col.write(item)
                price_col.write(f"£{by_name[item]:,.2f}")
                if remove_col.button("Quitar", key=f"remove_{idx}"):
                    st.session_state.cart.remove(item)
                    st.rerun()
            st.metric("Total estimado del carrito", f"£{sum(by_name[p] for p in st.session_state.cart):,.2f}")
            if st.button("Vaciar carrito"):
                st.session_state.cart = []
                st.rerun()
    with right:
        st.subheader("2. Recomendaciones")
        with st.expander("Filtros de asociación", expanded=False):
            min_support = st.slider("Soporte mínimo (%)", 0.0, 5.0, 1.0, 0.1)
            min_confidence = st.slider("Confianza mínima (%)", 0, 100, 50, 5)
            min_lift = st.slider("Lift mínimo (superior a)", 0.0, 5.0, 1.2, 0.1)
        suggested = recommendations(st.session_state.cart, rules, min_confidence/100, min_lift, min_support/100)
        if not st.session_state.cart:
            st.info("Tus recomendaciones aparecerán aquí al agregar productos.")
        elif not suggested:
            st.warning("No se encontraron reglas que coincidan con este carrito y los filtros actuales. Prueba con otros artículos o revisa los umbrales.")
        else:
            st.success(f"{len(suggested)} producto(s) complementario(s) sugerido(s)")
            for idx, item in enumerate(suggested[:12]):
                with st.container(border=True):
                    st.markdown(f"**{item['producto']}**")
                    st.write(f"Precio histórico: **£{by_name[item['producto']]:,.2f}**")
                    a, b, c = st.columns(3)
                    a.metric("Soporte", f"{100*item['support']:.2f}%")
                    b.metric("Confianza", f"{100*item['confidence']:.1f}%")
                    c.metric("Lift", f"{item['lift']:.2f}")
                    st.caption(f"Coincidencia del carrito: {item['antecedente']}")
                    if st.button("+ Agregar sugerencia al carrito", key=f"add_rec_{idx}", use_container_width=True):
                        st.session_state.cart.append(item["producto"])
                        st.session_state.cart = list(dict.fromkeys(st.session_state.cart))
                        st.rerun()
            if len(suggested) > 12:
                st.caption(f"Mostrando 12 de {len(suggested)} sugerencias ordenadas por confianza y lift.")
    st.caption("Una asociación no demuestra causalidad ni garantiza ventas adicionales. No se procesan pagos ni compras reales.")

with tab_rules:
    st.subheader("Resumen del modelo descriptivo")
    a, b, c, d = st.columns(4)
    a.metric("Reglas exportadas", len(rules))
    b.metric("Productos del catálogo", len(catalog))
    c.metric("Antecedentes distintos", len(trigger_products))
    d.metric("Reglas con 2+ antecedentes", sum(len(r["antecedente"]) >= 2 for r in rules))
    st.write("**Reglas ordenadas por confianza y lift**")
    table = pd.DataFrame([{
        "Antecedente": " + ".join(sorted(r["antecedente"])),
        "Consecuente": " + ".join(sorted(r["consecuente"])),
        "Soporte (%)": round(100*r["support"], 2),
        "Confianza (%)": round(100*r["confidence"], 2),
        "Lift": round(r["lift"], 2),
    } for r in rules]).sort_values(["Confianza (%)", "Lift"], ascending=False)
    st.dataframe(table, use_container_width=True, hide_index=True)
    st.download_button("Descargar tabla de reglas", data=table.to_csv(index=False).encode("utf-8-sig"), file_name="reglas_interpretables.csv", mime="text/csv")

with tab_about:
    st.subheader("¿Qué muestra este simulador?")
    st.write("""Este prototipo ilustra la **fase 6 (Despliegue) de CRISP-DM** a partir de reglas de asociación extraídas de compras históricas en Online Retail II.

**Funcionamiento:** al seleccionar productos, el sistema busca reglas cuyo antecedente esté contenido completamente en el carrito. Si el consecuente incluye un producto aún no seleccionado, lo recomienda. Si varias reglas sugieren el mismo producto, muestra la de mayor confianza y, en caso de empate, mayor lift y soporte.

**Alcances y limitaciones:**
- No ejecuta Apriori en cada consulta: utiliza un CSV de 404 reglas precomputadas.
- No existen imágenes reales del catálogo en los archivos aportados.
- Los precios son medianas históricas y **no** precios de venta vigentes.
- Las reglas son asociaciones de compras; no prueban incremento comercial ni equivalen a recomendaciones personalizadas por usuario.
- Algunas referencias del catálogo pueden ser cargos administrativos o artículos no pertinentes: requieren curación comercial adicional.
- El CSV contiene reglas que superaron los umbrales estadísticos, pero no una aprobación comercial individual documentada.
""")
    st.info("Los datos comerciales son históricos. La aplicación se presenta como simulación académica, no como comercio electrónico operativo.")
