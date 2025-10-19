import io
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import mplcursors
from io import BytesIO
from fastapi import APIRouter, File, UploadFile, Form
from fastapi.responses import JSONResponse, StreamingResponse, Response
from fastapi.encoders import jsonable_encoder
from utils import read_dataframe, create_plot_pdf, factorize_categoricals


router = APIRouter()


@router.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    """
    Загружает CSV-файл, парсит данные в DataFrame и возвращает информацию о данных:
    - Метаданные DataFrame с помощью df.info()
    - Первые 10 строк для предварительного просмотра с помощью df.head(10)
    - Список колонок для выбора и дальнейшего построения графика.
    """
    df = await read_dataframe(file)
    if df is None:
        return JSONResponse({"error": "Не удалось прочитать файл. Проверьте формат файла (ожидается CSV)"}, status_code=400)

    df = df.dropna()

    buffer = io.StringIO()
    df.info(buf=buffer)
    info_str = buffer.getvalue()
    buffer.close()

    head_df = df.head(10)
    head_df = head_df.where(pd.notnull(head_df), None)

    def convert_types(val):
        if isinstance(val, np.generic):
            return val.item()
        return val

    head_clean = head_df.apply(lambda col: col.map(convert_types))
    head_json = jsonable_encoder(head_clean.to_dict(orient="records"))
    columns = df.columns.tolist()

    return {"info": info_str, "head": head_json, "columns": columns}


def prepare_plot_data(df: pd.DataFrame, selected_col: str, group_by_col: str) -> pd.DataFrame:
    """
    Подготовка данных для построения графика.
    Частичная реализация группировки значений временно отключена.
    При вызове с group_by_col возвращается просто подсчет уникальных значений выбранного столбца.
    """
    if not group_by_col:
        # Подсчет количества уникальных значений выбранного столбца
        grouped = df.groupby(selected_col).size().reset_index(name='count')
        return grouped.rename(columns={selected_col: 'category'})
    else:
        # Заглушка: пока группировка не реализована
        # просто возвращаем сообщение об отсутствующем функционале
        # Можно здесь в будущем реализовать агрегацию по группам
        return df.head(0)  # пустой датафрейм, или можно возвращать ошибку/сообщение


@router.post("/plot/image/")
async def plot_image(
    file: UploadFile = File(...),
    selected_column: str = Form(...),
    chart_type: str = Form(...),
    group_by_column: str = Form("")
):
    """
    Построение вертикальной столбчатой диаграммы.
    Подписи к столбцам добавляются, если число уникальных значений <= 10, иначе показываются всплывающие подсказки.
    Реализация группировки значений временно отключена (работаем без группировки).
    Поддерживается только тип графика 'bar'.
    """
    df = await read_dataframe(file)
    if df is None:
        return JSONResponse({"error": "Не удалось прочитать файл("}, status_code=400)

    if selected_column not in df.columns:
        return JSONResponse({"error": f"Колонка не найдена: {selected_column}"}, status_code=400)
    if group_by_column and group_by_column not in df.columns:
        return JSONResponse({"error": f"Колонка группировки не найдена: {group_by_column}"}, status_code=400)

    plot_data = prepare_plot_data(df, selected_column, group_by_column)

    if plot_data.empty:
        return JSONResponse({"error": "Функционал группировки находится в разработке(\nНаши разработчики изо всех сил стараются расширить функционал)"}, status_code=501)

    fig, ax = plt.subplots(figsize=(10, 6))

    plot_data = plot_data.rename(columns={"category": selected_column})
    barplot = plot_data.plot(kind="bar", x=selected_column, y="count", ax=ax)

    unique_count = plot_data.shape[0]

    if unique_count <= 10:
        for p in ax.patches:
            height = p.get_height()
            ax.annotate(f'{height:.2f}',
                        (p.get_x() + p.get_width() / 2, height),
                        ha='center', va='bottom')
    else:
        ax.set_xticklabels([])
        cursor = mplcursors.cursor(ax.patches, hover=True)

        @cursor.connect("add")
        def on_add(sel):
            height = sel.artist[sel.index].get_height()
            label = sel.artist[sel.index].get_x() + sel.artist[sel.index].get_width() / 2
            sel.annotation.set(text=f'{height:.2f}', position=(0, 20), anncoords="offset points")
            sel.annotation.xy = (label, height)

    if chart_type != "bar":
        return JSONResponse({"error": "Пожалуйста, воспользуйтесь вертикальной диаграммой! Наши разработчики стараются изо всех сил расширить функционал)"}, status_code=400)

    plt.tight_layout()
    buf = BytesIO()
    plt.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    return Response(content=buf.getvalue(), media_type="image/png")


@router.post("/plot/pdf/")
async def plot_pdf(
    file: UploadFile = File(...),
    selected_column: str = Form(...),
    chart_type: str = Form(...),
    group_by_column: str = Form("")
):
    """
    Создание PDF с изображением графика.
    Временно без поддержки группировки (применяется заглушка).
    """
    df = await read_dataframe(file)
    if df is None:
        return JSONResponse({"error": "Не удалось прочитать файл."}, status_code=400)

    if selected_column not in df.columns:
        return JSONResponse({"error": f"Колонка не найдена: {selected_column}"}, status_code=400)
    if group_by_column and group_by_column not in df.columns:
        # Заглушка: отключение группировки
        group_by_column = ""

    plot_data = prepare_plot_data(df, selected_column, group_by_column)
    if plot_data.empty:
        return JSONResponse({"error": "Функционал группировки временно отключен (в разработке)"}, status_code=501)

    plot_data = factorize_categoricals(plot_data, plot_data.columns.tolist())
    pdf_bytes = create_plot_pdf(plot_data, [selected_column], chart_type)
    return StreamingResponse(BytesIO(pdf_bytes), media_type="application/pdf", headers={
        "Content-Disposition": "attachment; filename=plot.pdf"
    })
