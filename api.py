# import numpy as np
# from fastapi import APIRouter, File, UploadFile, Form
# from fastapi.responses import JSONResponse, StreamingResponse, Response
# from fastapi.encoders import jsonable_encoder
# from utils import read_dataframe, get_df_info_str, create_plot_pdf, factorize_categoricals
# from io import BytesIO
# import pandas as pd

# router = APIRouter()

# @router.post("/upload/")
# async def upload_file(file: UploadFile = File(...)):
#     df = await read_dataframe(file)
#     if df is None:
#         return JSONResponse({"error": "Не удалось прочитать файл. Убедитесь, что это CSV."}, status_code=400)

#     # Удаляем все строки с пропущенными значениями во всех столбцах
#     df = df.dropna()

#     info_str = get_df_info_str(df)
#     head_df = df.head(10)

#     # Заменяем NaN на None
#     head_df = head_df.where(pd.notnull(head_df), None)

#     # Конвертируем numpy типы в родные python
#     def convert_types(val):
#         if isinstance(val, np.generic):
#             return val.item()
#         return val

#     head_clean = head_df.applymap(convert_types)

#     # Преобразуем в список словарей и кодируем
#     head_list = head_clean.to_dict(orient="records")
#     head_json = jsonable_encoder(head_list)

#     columns = df.columns.tolist()

#     return {"info": info_str, "head": head_json, "columns": columns}

# @router.post("/plot/")
# async def plot_graph(
#     file: UploadFile = File(...),
#     selected_columns: str = Form(...),
#     chart_type: str = Form(...)
# ):
#     df = await read_dataframe(file)
#     if df is None:
#         return JSONResponse({"error": "Не удалось прочитать файл."}, status_code=400)

#     columns = selected_columns.split(",")
#     invalid_cols = [c for c in columns if c not in df.columns]
#     if invalid_cols:
#         return JSONResponse({"error": f"Колонки не найдены: {', '.join(invalid_cols)}"}, status_code=400)
    
#     plot_data = factorize_categoricals(df, columns)

#     try:
#         pdf_bytes = create_plot_pdf(plot_data, columns, chart_type)
#     except ValueError as e:
#         return JSONResponse({"error": str(e)}, status_code=400)

#     return StreamingResponse(BytesIO(pdf_bytes), media_type="application/pdf",
#                              headers={"Content-Disposition": "attachment; filename=plot.pdf"})

# @router.post("/plot/image/")
# async def plot_image(
#     file: UploadFile = File(...),
#     selected_columns: str = Form(...),
#     chart_type: str = Form(...)
# ):
#     df = await read_dataframe(file)
#     if df is None:
#         return JSONResponse({"error": "Не удалось прочитать файл."}, status_code=400)

#     columns = selected_columns.split(",")
#     invalid_cols = [c for c in columns if c not in df.columns]
#     if invalid_cols:
#         return JSONResponse({"error": f"Колонки не найдены: {', '.join(invalid_cols)}"}, status_code=400)
    
#     plot_data = factorize_categoricals(df, columns)

#     # Построение графика и сохранение в PNG
#     fig, ax = plt.subplots(figsize=(8,6))
#     if chart_type == "bar":
#         plot_data.plot(kind="bar", ax=ax)
#     elif chart_type == "barh":
#         plot_data.plot(kind="barh", ax=ax)
#     elif chart_type == "pie":
#         if len(columns) != 1:
#             return JSONResponse({"error":"Для круговой диаграммы выберите только одну колонку"}, status_code=400)
#         plot_data[columns[0]].value_counts().plot.pie(ax=ax, autopct='%1.1f%%')
#     else:
#         return JSONResponse({"error":"Неверный тип графика"}, status_code=400)

#     plt.tight_layout()
#     buf = BytesIO()
#     plt.savefig(buf, format='png')
#     plt.close(fig)
#     buf.seek(0)

#     return Response(content=buf.getvalue(), media_type="image/png")

# @router.post("/plot/pdf/")
# async def plot_pdf(
#     file: UploadFile = File(...),
#     selected_columns: str = Form(...),
#     chart_type: str = Form(...)
# ):
#     df = await read_dataframe(file)
#     if df is None:
#         return JSONResponse({"error":"Не удалось прочитать файл."}, status_code=400)

#     columns = selected_columns.split(",")
#     plot_data = factorize_categoricals(df, columns)

#     pdf_bytes = create_plot_pdf(plot_data, columns, chart_type)

#     return StreamingResponse(BytesIO(pdf_bytes), media_type="application/pdf", headers={
#         "Content-Disposition": "attachment; filename=plot.pdf"
#     })

import numpy as np
from fastapi import APIRouter, File, UploadFile, Form
from fastapi.responses import JSONResponse, StreamingResponse, Response
from fastapi.encoders import jsonable_encoder
from utils import read_dataframe, get_df_info_str, create_plot_pdf, factorize_categoricals
from io import BytesIO
import matplotlib.pyplot as plt
import pandas as pd

router = APIRouter()

@router.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    df = await read_dataframe(file)
    if df is None:
        return JSONResponse({"error": "Не удалось прочитать файл. Убедитесь, что это CSV."}, status_code=400)

    df = df.dropna()
    info_str = get_df_info_str(df)
    head_df = df.head(10)
    head_df = head_df.where(pd.notnull(head_df), None)

    def convert_types(val):
        if isinstance(val, np.generic):
            return val.item()
        return val

    head_clean = head_df.applymap(convert_types)
    head_json = jsonable_encoder(head_clean.to_dict(orient="records"))
    columns = df.columns.tolist()

    return {"info": info_str, "head": head_json, "columns": columns}

@router.post("/plot/image/")
async def plot_image(
    file: UploadFile = File(...),
    selected_columns: str = Form(...),
    chart_type: str = Form(...)
):
    df = await read_dataframe(file)
    if df is None:
        return JSONResponse({"error": "Не удалось прочитать файл."}, status_code=400)
    columns = selected_columns.split(",")
    invalid_cols = [c for c in columns if c not in df.columns]
    if invalid_cols:
        return JSONResponse({"error": f"Колонки не найдены: {', '.join(invalid_cols)}"}, status_code=400)

    plot_data = factorize_categoricals(df, columns)

    fig, ax = plt.subplots(figsize=(8,6))
    if chart_type == "bar":
        plot_data.plot(kind="bar", ax=ax)
    elif chart_type == "barh":
        plot_data.plot(kind="barh", ax=ax)
    elif chart_type == "pie":
        if len(columns) != 1:
            return JSONResponse({"error":"Для круговой диаграммы выберите только одну колонку"}, status_code=400)
        plot_data[columns[0]].value_counts().plot.pie(ax=ax, autopct='%1.1f%%')
    else:
        return JSONResponse({"error":"Неверный тип графика"}, status_code=400)

    plt.tight_layout()
    buf = BytesIO()
    plt.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    return Response(content=buf.getvalue(), media_type="image/png")

@router.post("/plot/pdf/")
async def plot_pdf(
    file: UploadFile = File(...),
    selected_columns: str = Form(...),
    chart_type: str = Form(...)
):
    df = await read_dataframe(file)
    if df is None:
        return JSONResponse({"error": "Не удалось прочитать файл."}, status_code=400)
    columns = selected_columns.split(",")
    plot_data = factorize_categoricals(df, columns)

    pdf_bytes = create_plot_pdf(plot_data, columns, chart_type)

    return StreamingResponse(BytesIO(pdf_bytes), media_type="application/pdf", headers={
        "Content-Disposition": "attachment; filename=plot.pdf"
    })
