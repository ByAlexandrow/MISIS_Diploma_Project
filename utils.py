import pandas as pd
from io import StringIO, BytesIO
import matplotlib.pyplot as plt

async def read_dataframe(file) -> pd.DataFrame | None:
    try:
        contents = await file.read()
        df = pd.read_csv(BytesIO(contents))
        return df
    except Exception:
        return None

def factorize_categoricals(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    df_copy = df[columns].copy()
    for col in columns:
        if df_copy[col].dtype == 'object':
            codes, _ = pd.factorize(df_copy[col])
            df_copy[col] = codes
    return df_copy

def get_df_info_str(df: pd.DataFrame) -> str:
    buffer = StringIO()
    df.info(buf=buffer)
    return buffer.getvalue()

def create_plot_pdf(df: pd.DataFrame, columns: list[str], chart_type: str) -> bytes:
    fig, ax = plt.subplots(figsize=(8,6))

    if chart_type == "bar":
        df[columns].plot(kind="bar", ax=ax)
    elif chart_type == "barh":
        df[columns].plot(kind="barh", ax=ax)
    elif chart_type == "pie":
        if len(columns) != 1:
            raise ValueError("Для круговой диаграммы выберите только одну колонку")
        df[columns[0]].value_counts().plot.pie(ax=ax, autopct='%1.1f%%')
    else:
        raise ValueError("Неверный тип графика")

    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format='pdf')
    plt.close(fig)
    buf.seek(0)
    return buf.read()
