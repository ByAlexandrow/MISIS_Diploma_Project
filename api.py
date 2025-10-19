import numpy as np
from fastapi import APIRouter, File, UploadFile, Form
from fastapi.responses import JSONResponse, StreamingResponse, Response
from fastapi.encoders import jsonable_encoder
from utils import read_dataframe, get_df_info_str, create_plot_pdf, factorize_categoricals
import io
from io import BytesIO
import matplotlib.pyplot as plt
import pandas as pd
import mplcursors


router = APIRouter()


@router.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    df = await read_dataframe(file)
    if df is None:
        return JSONResponse({"error": "Не удалось прочитать файл. Убедитесь, что это CSV."}, status_code=400)

    df = df.dropna()

    # Перехватываем вывод df.info()
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
    if not group_by_col:
        # если нет группировки, посчитать количество уникальных значений выбранного столбца
        grouped = df.groupby(selected_col).size().reset_index(name='count')
        return grouped.rename(columns={selected_col: 'category'})
    else:
        # если выбран столбец для агрегации
        if pd.api.types.is_numeric_dtype(df[selected_col]):
            grouped = df.groupby(group_by_col)[selected_col].mean().reset_index()
        else:
            # для нечисловых столбцов использовать подсчёт количества
            grouped = df.groupby(group_by_col).size().reset_index(name='count')
        return grouped


@router.post("/plot/image/")
async def plot_image(
    file: UploadFile = File(...),
    selected_column: str = Form(...),
    chart_type: str = Form(...),
    group_by_column: str = Form("")
):
    df = await read_dataframe(file)
    if df is None:
        return JSONResponse({"error": "Не удалось прочитать файл."}, status_code=400)

    if selected_column not in df.columns:
        return JSONResponse({"error": f"Колонка не найдена: {selected_column}"}, status_code=400)
    if group_by_column and group_by_column not in df.columns:
        return JSONResponse({"error": f"Колонка группировки не найдена: {group_by_column}"}, status_code=400)

    plot_data = prepare_plot_data(df, selected_column, group_by_column)

    fig, ax = plt.subplots(figsize=(10, 6))

    if not group_by_column:
        plot_data = plot_data.rename(columns={"category": selected_column})
        barplot = plot_data.plot(kind="bar", x=selected_column, y="count", ax=ax)
    else:
        y_col = selected_column if pd.api.types.is_numeric_dtype(df[selected_column]) else 'count'
        barplot = plot_data.plot(kind="bar", x=group_by_column, y=y_col, ax=ax)
    
    # Кол-во уникальных значений для решения подписывать или показывать тултипы
    unique_count = plot_data.shape[0]

    if unique_count <= 10:
        # Подписываем столбцы значениями над ними
        for p in ax.patches:
            height = p.get_height()
            ax.annotate(f'{height:.2f}',
                        (p.get_x() + p.get_width() / 2, height),
                        ha='center', va='bottom')
    else:
        # Убираем подписи (set_xticklabels пустой)
        ax.set_xticklabels([])
        # Включаем всплывающие подсказки на столбцах
        cursor = mplcursors.cursor(ax.patches, hover=True)
        @cursor.connect("add")
        def on_add(sel):
            height = sel.artist[sel.index].get_height()
            label = sel.artist[sel.index].get_x() + sel.artist[sel.index].get_width()/2
            sel.annotation.set(text=f'{height:.2f}', position=(0, 20), anncoords="offset points")
            sel.annotation.xy = (label, height)

    # if chart_type == "barh":
    #     ax.invert_yaxis()

    # elif chart_type == "pie":
    #     if group_by_column:
    #         return JSONResponse({"error": "Для круговой диаграммы группировка не поддерживается"}, status_code=400)
    #     plot_data.set_index(selected_column)['count'].plot.pie(ax=ax, autopct='%1.1f%%')

    if chart_type != "bar":
        return JSONResponse({"error": "Неверный тип графика"}, status_code=400)

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
    df = await read_dataframe(file)
    if df is None:
        return JSONResponse({"error": "Не удалось прочитать файл."}, status_code=400)

    if selected_column not in df.columns:
        return JSONResponse({"error": f"Колонка не найдена: {selected_column}"}, status_code=400)
    if group_by_column and group_by_column not in df.columns:
        return JSONResponse({"error": f"Колонка группировки не найдена: {group_by_column}"}, status_code=400)

    plot_data = prepare_plot_data(df, selected_column, group_by_column)
    plot_data = factorize_categoricals(plot_data, plot_data.columns.tolist())

    pdf_bytes = create_plot_pdf(plot_data, [selected_column], chart_type)
    return StreamingResponse(BytesIO(pdf_bytes), media_type="application/pdf", headers={
        "Content-Disposition": "attachment; filename=plot.pdf"
    })
