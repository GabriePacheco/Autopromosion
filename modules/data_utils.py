import pandas as pd
def filtrar_por_dia(df, dias):
    # df debe tener columna Fecha como datetime
    return df[df["Fecha"].dt.dayofweek.isin(dias)]

def preparar_datasets_graficos(plan_df, fechas_originales):
    # Excluir fila Total y columnas no relevantes
    df_graf = plan_df.drop(index="Total", errors="ignore").copy()
    df_graf = df_graf.reset_index()
    # Recuperar la fecha original para cada programa
    df_graf["Fecha"] = df_graf["Título Programa"].map(fechas_originales)
    df_graf["Franja Horaria"] = df_graf["Hora Inicio"].apply(asignar_franja_horaria)
    df_graf = df_graf[["Título Programa", "Hora Inicio", "Total", "Franja Horaria", "Fecha"]]
    df_graf = df_graf.sort_values("Hora Inicio")
    # Lunes a viernes: dayofweek 0-4, Sábado y domingo: 5-6
    df_graf["Fecha_dt"] = pd.to_datetime(df_graf["Fecha"], format="%d/%m", errors="coerce")
    df_lv = df_graf[df_graf["Fecha_dt"].dt.dayofweek.isin([0,1,2,3,4])]
    df_sd = df_graf[df_graf["Fecha_dt"].dt.dayofweek.isin([5,6])]
    return df_lv, df_sd

FRANJAS_HORARIAS = {
    "Madrugada":        {"inicio": "00:00", "fin": "05:59"},
    "Despertador":      {"inicio": "06:00", "fin": "08:00"},
    "Mañana":           {"inicio": "08:01", "fin": "12:00"},
    "Acceso sobremesa": {"inicio": "12:01", "fin": "13:00"},
    "Sobremesa":        {"inicio": "13:01", "fin": "15:00"},
    "Tarde":            {"inicio": "15:01", "fin": "17:59"},
    "Acceso prime":     {"inicio": "18:00", "fin": "19:59"},
    "Prime time 1":     {"inicio": "20:00", "fin": "22:00"},
    "Prime time 2":     {"inicio": "22:01", "fin": "23:59"}
}

def asignar_franja_horaria(hora):
    if hora is None or hora == "":
        return "Sin franja"
    hora_str = hora.strftime("%H:%M") if hasattr(hora, "strftime") else str(hora)
    for franja, rango in FRANJAS_HORARIAS.items():
        if rango["inicio"] <= hora_str <= rango["fin"]:
            return franja
    return "Sin franja"

def preparar_dataset_grafico(plan_df):
    # Excluir fila Total y columnas no relevantes
    df_graf = plan_df.drop(index="Total", errors="ignore").copy()
    df_graf = df_graf.reset_index()
    df_graf["Franja Horaria"] = df_graf["Hora Inicio"].apply(asignar_franja_horaria)
    # Usar la columna Total para el gráfico
    df_graf = df_graf[["Título Programa", "Hora Inicio", "Total", "Franja Horaria"]]
    df_graf = df_graf.sort_values("Hora Inicio")
    return df_graf


def cargar_datos(ruta_csv):
    df = pd.read_csv(ruta_csv, encoding="utf-8")
    df = df[pd.to_datetime(df["Fecha"], errors="coerce", dayfirst=True).notna()]
    df["Fecha"] = pd.to_datetime(df["Fecha"], format="%d/%m/%Y", errors="coerce")
    df["Hora Inicio"] = pd.to_datetime(df["Hora Inicio"], format="%H:%M:%S", errors="coerce").dt.time
    df["Inserciones"] = 1
    for col in ["Producto", "Tipo Comercial", "Título Programa"]:
        if col in df.columns:
            df[col] = df[col].astype(str)
    for col in ["Inserciones"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(float)
    return df

def filter_promotions(df, start_date, end_date):
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)
    filtered = df[(df["Fecha"] >= start) & (df["Fecha"] <= end)]
    return filtered["Producto"].dropna().unique().tolist()

def generar_plan(df_filtrado):
    df_grouped = df_filtrado.groupby(["Título Programa", "Fecha"]).agg(
        Inserciones=("Inserciones", "sum"),
        Hora=("Hora Inicio", lambda x: x.mode().iloc[0] if not x.mode().empty else None)
    ).reset_index()
    # Formatear fechas como dd/mm
    df_grouped["Fecha"] = df_grouped["Fecha"].dt.strftime("%d/%m")
    # Pivotear y ordenar columnas por fecha ascendente
    pivot = df_grouped.pivot_table(index="Título Programa", columns="Fecha", values="Inserciones", aggfunc="sum", fill_value=0)
    pivot = pivot.reindex(sorted(pivot.columns, key=lambda x: int(x[:2]) + int(x[3:])*100), axis=1)
    horas = df_grouped.groupby("Título Programa")["Hora"].first()
    pivot.insert(0, "Hora Inicio", pivot.index.map(horas))
    # Calcular el total por programa y agregar la columna 'Total' al lado de 'Hora Inicio'
    pivot.insert(1, "Total", pivot.drop(columns=["Hora Inicio"]).sum(axis=1).astype(int))
    pivot.loc["Total"] = pivot.sum(numeric_only=True)
    pivot.loc["Total", "Hora Inicio"] = ""
    pivot.loc["Total", "Total"] = pivot.drop(columns=["Hora Inicio", "Total"]).sum().sum().astype(int)
    def hora_a_minutos(h):
        if pd.isnull(h) or h == "":
            return 999999
        return h.hour * 60 + h.minute + h.second / 60 if hasattr(h, "hour") else 999999
    pivot["_orden"] = pivot["Hora Inicio"].apply(hora_a_minutos)
    pivot = pivot.sort_values("_orden").drop(columns=["_orden"])
    # Mostrar los valores como enteros
    for col in pivot.columns:
        if col != "Hora Inicio":
            pivot[col] = pivot[col].astype(int)
    pivot = pivot.replace(0, "")
    return pivot
