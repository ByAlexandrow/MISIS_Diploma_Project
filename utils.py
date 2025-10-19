import pandas as pd
from io import StringIO, BytesIO
import matplotlib.pyplot as plt


async def read_dataframe(file) -> pd.DataFrame | None:
    """
    Чтение CSV-файла в DataFrame.
    """
    try:
        contents = await file.read()
        df = pd.read_csv(BytesIO(contents))
        return df
    except Exception:
        return None


def factorize_categoricals(
    df: pd.DataFrame, columns: list[str]
) -> pd.DataFrame:
    """
    Преобразование категориальных столбцов в числовой формат через factorize.
    """
    df_copy = df[columns].copy()
    for col in columns:
        if df_copy[col].dtype == 'object':
            codes, _ = pd.factorize(df_copy[col])
            df_copy[col] = codes
    return df_copy


def get_df_info_str(df: pd.DataFrame) -> str:
    """
    Возвращает строку с описательной информацией через df.info().
    """
    buffer = StringIO()
    df.info(buf=buffer)
    return buffer.getvalue()


def create_plot_png(
    df: pd.DataFrame, columns: list[str], chart_type: str, x_label: str = None
) -> bytes:
    """
    Создает PNG-изображение с диаграммой на основе данных.
    Поддерживается только тип графика 'bar' - вертикальный столбчатый.
    """
    fig, ax = plt.subplots(figsize=(8, 6))

    if chart_type == "bar":
        cat_col = df.columns[0]
        num_col = columns[0]
        df.plot(kind="bar", x=cat_col, y=num_col, ax=ax)

        if x_label:
            ax.set_xlabel(x_label)
        else:
            ax.set_xlabel(cat_col)

        ax.set_ylabel(num_col)
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
        plt.tight_layout()

        for p in ax.patches:
            height = p.get_height()
            ax.annotate(f'{height:.2f}',
                        (p.get_x() + p.get_width() / 2, height),
                        ha='center', va='bottom')
    else:
        raise ValueError(
            "Этот тип графика находится в разработке!\n"
            "Наши разработчики изо всех сил стараются расширить функционал)"
        )

    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def prepare_plot_data(
    df: pd.DataFrame, selected_col: str, group_by_col: str
) -> pd.DataFrame:
    """
    Подготовка данных для построения графика.
    Временно без реализация группировки значений.
    """
    if not group_by_col:
        grouped = df.groupby(selected_col).size().reset_index(name='count')
        return grouped.rename(columns={selected_col: 'category'})
    else:
        return df.head(0)
