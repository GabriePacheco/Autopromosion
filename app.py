import pandas as pd
import streamlit as st
from modules.data_utils import cargar_datos, filter_promotions, generar_plan

# 🔹 Interfaz Streamlit
def main():
    st.set_page_config(page_title="Informe de Inserciones", layout="wide")
    df = cargar_datos("promocionales.csv")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        start_date = st.date_input("📅 Fecha de inicio", value=pd.to_datetime("today") - pd.DateOffset(days=7))
    with col2:
        end_date = st.date_input("📅 Fecha de fin", value=pd.to_datetime("today"))
    with col3:
        available_products = filter_promotions(df, start_date, end_date)
        selected_products = st.multiselect("🎯 Promociones", options=available_products )
    with col4:
        tipo_comercial_options = df["Tipo Comercial"].dropna().unique().tolist()
        with st.expander("Opciones avanzadas", expanded=False):
            selected_tipo_comercial = st.multiselect("🏷️ Tipo Comercial", options=tipo_comercial_options, default=tipo_comercial_options)
    with col5:
        accion = st.button("Buscar")

    if len(selected_tipo_comercial) == 0:
        st.warning("⚠️ Debes seleccionar al menos un Tipo Comercial.")
        return

    if accion:
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)

        df_filtrado = df[
            (df["Fecha"] >= start) &
            (df["Fecha"] <= end) &
            (df["Producto"].isin(selected_products)) &
            (df["Tipo Comercial"].isin(selected_tipo_comercial))
        ]

        if df_filtrado.empty:
            st.warning("⚠️ No hay datos para los filtros seleccionados.")
        else:
            plan = generar_plan(df_filtrado)
            st.subheader("📅 Plan")
            st.dataframe(plan, use_container_width=True)

            # Preparar dataset para gráfico único
            from modules.data_utils import preparar_dataset_grafico
            import plotly.express as px
            df_grafico = preparar_dataset_grafico(plan)
            # Filtrar solo lunes a viernes
            if "Fecha" in df_filtrado.columns:
                df_grafico["Fecha_dt"] = df_filtrado.groupby("Título Programa")["Fecha"].min().reindex(df_grafico["Título Programa"]).values
                df_grafico = df_grafico[df_grafico["Fecha_dt"].dt.dayofweek.isin([0,1,2,3,4])]
            # Preparar dataset para sábado y domingo antes de las columnas
            df_grafico_sd = preparar_dataset_grafico(plan)
            if "Fecha" in df_filtrado.columns:
                df_grafico_sd["Fecha_dt"] = df_filtrado.groupby("Título Programa")["Fecha"].min().reindex(df_grafico_sd["Título Programa"]).values
                df_grafico_sd = df_grafico_sd[df_grafico_sd["Fecha_dt"].dt.dayofweek.isin([5,6])]

            col_graf1, col_graf2 = st.columns(2)
            with col_graf1:
               
                fig = px.bar(
                    df_grafico,
                    x="Título Programa",
                    y="Total",
                    color="Franja Horaria",
                    category_orders={"Título Programa": df_grafico["Título Programa"].tolist()},
                    labels={"Total": "Inserciones", "Título Programa": "Programa"},
                    title="INSERCIONES LUNES A VIERNES"
                )
                fig.update_xaxes(tickangle=90)
                fig.update_layout(showlegend=False, height=600)
                st.plotly_chart(fig, use_container_width=True)
            with col_graf2:
               
                if df_grafico_sd.empty:
                    st.info("No hay datos para sábado y domingo.")
                else:
                    fig_sd = px.bar(
                        df_grafico_sd,
                        x="Título Programa",
                        y="Total",
                        color="Franja Horaria",
                        category_orders={"Título Programa": df_grafico_sd["Título Programa"].tolist()},
                        labels={"Total": "Inserciones", "Título Programa": "Programa"},
                        title="INSERCIONES SÁBADO Y DOMINGO"
                    )
                    fig_sd.update_xaxes(tickangle=90)
                    fig_sd.update_layout(showlegend=True, height=600)
                    st.plotly_chart(fig_sd, use_container_width=True)
            col_pie, coltabla = st.columns(2)
            with col_pie:
                if df_grafico.empty:
                    st.info("No hay datos para el gráfico de pastel.")
                else:
                    pie_data = df_grafico.groupby("Franja Horaria")["Total"].sum().reset_index()
                    fig_pie = px.pie(
                        pie_data,
                        names="Franja Horaria",
                        values="Total",
                        title="Distribución de Inserciones por Franja Horaria"
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
            with coltabla:
                st.subheader(" Tabla Resumen por Franja Horaria")
                if df_grafico.empty:
                    st.info("No hay datos para la tabla resumen.")
                else:
                    tabla_resumen = df_grafico.pivot_table(index="Franja Horaria", values="Total", aggfunc="sum").reset_index()
                    tabla_resumen = tabla_resumen.sort_values("Total", ascending=False)
                    st.dataframe(tabla_resumen, use_container_width=True)

            # Gráfico de distribución de frecuencias diarias
            st.markdown("---")
            st.subheader("Evolución")
            
            # Preparar datos para el gráfico de línea de tiempo
            timeline_data = df_filtrado.groupby("Fecha")["Inserciones"].sum().reset_index()
            timeline_data = timeline_data.sort_values("Fecha")
            
            # Crear gráfico de línea
            fig_timeline = px.line(
                timeline_data,
                x="Fecha",
                y="Inserciones",
                title="Evolución diaria de inserciones",
                labels={"Fecha": "Fecha", "Inserciones": "Número de inserciones"}
            )
            
            # Personalizar el gráfico
            fig_timeline.update_traces(mode='lines+markers')
            fig_timeline.update_layout(
                xaxis_title="Fecha",
                yaxis_title="Número de inserciones",
                hovermode='x unified',
                height=400
            )
            
            # Mostrar valores en cada punto
            fig_timeline.update_traces(
                hovertemplate="<b>Fecha:</b> %{x|%d/%m/%Y}<br>" +
                             "<b>Inserciones:</b> %{y}<extra></extra>"
            )
            
            st.plotly_chart(fig_timeline, use_container_width=True)

if __name__ == "__main__":
    main()
