let uploadedFile = null;

document.getElementById("file-input").addEventListener("change", (e) => {
    uploadedFile = e.target.files[0];
    clearUI();
});

document.getElementById("analyze-btn").addEventListener("click", async () => {
    if (!uploadedFile) {
        alert("Выберите файл сначала");
        return;
    }

    let formData = new FormData();
    formData.append("file", uploadedFile);

    const res = await fetch("/api/upload/", { method: "POST", body: formData });

    if (!res.ok) {
        alert("Ошибка при загрузке файла");
        return;
    }

    const data = await res.json();

    if (data.error) {
        alert(data.error);
        return;
    }
    document.getElementById("df-info").textContent = data.info;

    let table = document.getElementById("df-head");
    table.innerHTML = "";
    if(data.head.length > 0){
        let headerRow = document.createElement("tr");
        Object.keys(data.head[0]).forEach(col => {
            let th = document.createElement("th");
            th.textContent = col;
            headerRow.appendChild(th);
        });
        table.appendChild(headerRow);
        data.head.forEach(row => {
            let tr = document.createElement("tr");
            Object.values(row).forEach(val => {
                let td = document.createElement("td");
                td.textContent = val;
                tr.appendChild(td);
            });
            table.appendChild(tr);
        });
    }

    let columnsWrapper = document.getElementById("columns-wrapper");
    columnsWrapper.innerHTML = "";
    data.columns.forEach((col, idx) => {
        let label = document.createElement("label");
        if(idx === 0) label.classList.add("selected");
        let input = document.createElement("input");
        input.type = "radio";
        input.name = "columns-select";
        input.value = col;
        if(idx === 0) input.checked = true;
        let span = document.createElement("span");
        span.textContent = col;
        label.appendChild(input);
        label.appendChild(span);
        columnsWrapper.appendChild(label);
    });
});

document.getElementById("plot-btn").addEventListener("click", async () => {
    if(!uploadedFile) { alert("Выберите файл сначала"); return; }
    let selectedRadio = document.querySelector('input[name="columns-select"]:checked');
    if(!selectedRadio) { alert("Выберите колонку для графика"); return; }
    let selected = selectedRadio.value;

    let groupSelected = ""; // заглушка, функционал в разработке

    let chartType = document.getElementById("chart-type").value;

    let formData = new FormData();
    formData.append("file", uploadedFile);
    formData.append("selected_column", selected);
    formData.append("group_by_column", groupSelected);
    formData.append("chart_type", chartType);

    const res = await fetch("/api/plot/image/", {method: "POST", body: formData});
    if(!res.ok) {
        let errorData = await res.json();
        alert(errorData.error || "Ошибка построения графика");
        return;
    }

    const blob = await res.blob();
    const url = URL.createObjectURL(blob);

    let plotImage = document.getElementById("plot-image");
    plotImage.src = url;
    plotImage.style.display = "block";

    document.getElementById("download-png-btn").style.display = "inline-block";
});

document.getElementById("download-png-btn").addEventListener("click", async () => {
    if (!uploadedFile) {
        alert("Выберите файл сначала");
        return;
    }
    let selectedRadio = document.querySelector('input[name="columns-select"]:checked');
    if(!selectedRadio) {
        alert("Выберите колонку для графика");
        return;
    }
    let selected = selectedRadio.value;

    let groupSelected = "";

    let chartType = document.getElementById("chart-type").value;

    let formData = new FormData();
    formData.append("file", uploadedFile);
    formData.append("selected_column", selected);
    formData.append("group_by_column", groupSelected);
    formData.append("chart_type", chartType);

    const res = await fetch("/api/plot/png/", { method: "POST", body: formData });
    if (!res.ok) {
        let errorData = await res.json();
        alert(errorData.error || "Ошибка скачивания .png");
        return;
    }

    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "result.png";
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
});

function clearUI(){
    document.getElementById("df-info").textContent = "";
    document.getElementById("df-head").innerHTML = "";
    document.getElementById("columns-wrapper").innerHTML = "";
    document.getElementById("group-by-select").innerHTML = "";
    document.getElementById("plot-image").style.display = "none";
    document.getElementById("download-png-btn").style.display = "none";
}
