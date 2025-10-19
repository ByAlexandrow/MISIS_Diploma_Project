import numpy as np
import mplcursors
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from fastapi import APIRouter, File, UploadFile, Form
from fastapi.responses import JSONResponse, StreamingResponse, Response
from fastapi.encoders import jsonable_encoder
from utils import (
    read_dataframe, create_plot_pdf,
    factorize_categoricals,
    prepare_plot_data, get_df_info_str
)

router = APIRouter()


@router.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    """
    Загрузка CSV-файла.
    Возврат информации о DataFrame с помощью: df.info() и df.head(10).
    """
    df = await read_dataframe(file)
    if df is None:
        return JSONResponse({
            "error": "Ошибка чтения файла. Ожидаемый формат файла - CSV."
        }, status_code=400)

    df = df.dropna()

    info_str = get_df_info_str(df)

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


@router.post("/plot/image/")
async def plot_image(
    file: UploadFile = File(...),
    selected_column: str = Form(...),
    chart_type: str = Form(...),
    group_by_column: str = Form("")
):
    """
    Построение диаграммы и подпись столбцов.
    Временно без реализация группировки.
    """
    df = await read_dataframe(file)
    if df is None:
        return JSONResponse({"error": "Ошибка чтения файла("}, status_code=400)

    if selected_column not in df.columns:
        return JSONResponse({
            "error": f"Не удается найти колонку: {selected_column}"
        }, status_code=400)
    if group_by_column and group_by_column not in df.columns:
        return JSONResponse({
            "error": f"Не удается найти колонку: {group_by_column}"
        }, status_code=400)

    plot_data = prepare_plot_data(df, selected_column, group_by_column)

    if plot_data.empty:
        return JSONResponse({
            "error": "Функционал группировки находится в разработке(\n"
            "Наши разработчики изо всех сил стараются расширить функционал)"
        }, status_code=501)

    fig, ax = plt.subplots(figsize=(10, 6))

    plot_data = plot_data.rename(
        columns={"category": selected_column}
    )
    plot_data.plot(
        kind="bar", x=selected_column, y="count", ax=ax
    )

    unique_count = plot_data.shape[0]

    if unique_count <= 10:
        for p in ax.patches:
            height = p.get_height()
            ax.annotate(
                f'{height:.2f}', (p.get_x() + p.get_width() / 2, height),
                ha='center', va='bottom'
            )
    else:
        ax.set_xticklabels([])
        cursor = mplcursors.cursor(ax.patches, hover=True)

        @cursor.connect("add")
        def on_add(sel):
            height = sel.artist[sel.index].get_height()
            label = (
                sel.artist[sel.index].get_x() +
                sel.artist[sel.index].get_width() / 2
            )
            sel.annotation.set(
                text=f'{height:.2f}', position=(0, 20),
                anncoords="offset points"
            )
            sel.annotation.xy = (label, height)

    if chart_type != "bar":
        return JSONResponse({
            "error": "Пожалуйста, воспользуйтесь вертикальной диаграммой!\n"
            "Наши разработчики стараются изо всех сил расширить функционал)"
        }, status_code=400)

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
    Создание PDF-файла с построенным графиком.
    Временно без реализации группировки.
    """
    df = await read_dataframe(file)
    if df is None:
        return JSONResponse({
            "error": "Ошибка чтения файла."
        }, status_code=400)

    if selected_column not in df.columns:
        return JSONResponse({
            "error": f"Не удалось найти такую колонку: {selected_column}"
        }, status_code=400)
    if group_by_column and group_by_column not in df.columns:
        group_by_column = ""

    plot_data = prepare_plot_data(df, selected_column, group_by_column)
    if plot_data.empty:
        return JSONResponse({
            "error": "Функционал группировки находится в разработке)"
        }, status_code=501)

    plot_data = factorize_categoricals(plot_data, plot_data.columns.tolist())
    pdf_bytes = create_plot_pdf(plot_data, [selected_column], chart_type)
    return StreamingResponse(
        BytesIO(pdf_bytes), media_type="application/pdf", headers={
            "Content-Disposition": "attachment; filename=result.pdf"
        }
    )
