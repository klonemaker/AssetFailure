from flask import Flask, request, jsonify, render_template_string
import pandas as pd
import io

app = Flask(__name__)

# This will store our cleaned data in the server's memory
latest_report_data = []

# --- HTML TEMPLATES ---

# 1. The Admin Upload Page
ADMIN_HTML = """
<!DOCTYPE html>
<html>
<head><title>Admin - Upload ICMS Report</title></head>
<body style="font-family: Arial; margin: 40px; background: #f4f7f6;">
    <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); max-width: 500px;">
        <h2>Admin Portal: Upload Daily Report</h2>
        <form action="/upload" method="post" enctype="multipart/form-data">
            <input type="file" name="file" accept=".xlsx, .xls, .csv" required style="margin-bottom: 20px;"/><br>
            <input type="submit" value="Upload and Process" style="padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;"/>
        </form>
    </div>
</body>
</html>
"""

# 2. The User Search Dashboard
USER_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ICMS Asset Failures Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f4f7f6; }
        .container { background-color: #fff; padding: 25px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; table-layout: fixed; }
        th, td { border: 1px solid #e0e0e0; padding: 10px; text-align: left; vertical-align: top; word-wrap: break-word; }
        th { background-color: #007bff; color: white; position: sticky; top: 0; }
        .controls { display: flex; flex-wrap: wrap; gap: 20px; margin-bottom: 20px; background: #f9f9f9; padding: 15px; border-radius: 6px; border: 1px solid #ddd; }
        .control-group { display: flex; flex-direction: column; gap: 5px; flex: 1; min-width: 200px; }
        input[type="text"], select { padding: 10px; font-size: 14px; border: 1px solid #ccc; border-radius: 4px; }
        .remark-col { width: 50%; }
        mark { background-color: #ffeb3b; color: #000; padding: 0 3px; border-radius: 3px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <h2 style="margin-top:0;">ICMS Asset Failures - Search & Filter</h2>
        
        <div class="controls">
            <div class="control-group">
                <label><b>Search Remarks:</b></label>
                <input type="text" id="searchBar" placeholder="Type keywords..." onkeyup="applyFilters()" />
            </div>
            <div class="control-group">
                <label><b>Zone:</b></label>
                <select id="zoneFilter" onchange="applyFilters()"><option value="All">All</option></select>
            </div>
            <div class="control-group">
                <label><b>Classification:</b></label>
                <select id="classFilter" onchange="applyFilters()"><option value="All">All</option></select>
            </div>
        </div>

        <div id="recordCount" style="font-weight: bold; margin-bottom: 10px;">Loading data...</div>
        
        <div style="max-height: 600px; overflow-y: auto; border: 1px solid #ddd;">
            <table id="reportTable">
                <thead>
                    <tr>
                        <th style="width: 7%;">Zone</th>
                        <th style="width: 12%;">Classification</th>
                        <th style="width: 6%;">Div.</th>
                        <th style="width: 15%;">Date Time</th>
                        <th class="remark-col">Remarks</th>
                    </tr>
                </thead>
                <tbody id="tableBody"></tbody>
            </table>
        </div>
    </div>

    <script>
        let globalData = [];

        // Automatically fetch the latest data from the server on load
        fetch('/api/data')
            .then(response => response.json())
            .then(data => {
                globalData = data;
                populateDropdowns();
                applyFilters();
            })
            .catch(error => {
                document.getElementById('tableBody').innerHTML = '<tr><td colspan="5" style="text-align:center;">No data available. Admin needs to upload a report.</td></tr>';
                document.getElementById('recordCount').innerText = "Waiting for data...";
            });

        function populateDropdowns() {
            const zones = new Set();
            const classifications = new Set();

            globalData.forEach(row => {
                if (row['Zone']) zones.add(row['Zone']);
                if (row['Classification']) classifications.add(row['Classification']);
            });

            const zoneFilter = document.getElementById('zoneFilter');
            const classFilter = document.getElementById('classFilter');

            Array.from(zones).sort().forEach(zone => zoneFilter.innerHTML += `<option value="${zone}">${zone}</option>`);
            Array.from(classifications).sort().forEach(cls => classFilter.innerHTML += `<option value="${cls}">${cls}</option>`);
        }

        function applyFilters() {
            const searchInput = document.getElementById('searchBar').value.trim();
            const searchText = searchInput.toLowerCase();
            const zoneFilter = document.getElementById('zoneFilter').value;
            const classFilter = document.getElementById('classFilter').value;

            const filteredData = globalData.filter(row => {
                const remarks = (row['Remarks'] || "").toLowerCase();
                const matchSearch = searchText === "" || remarks.includes(searchText);
                const matchZone = zoneFilter === "All" || row['Zone'] === zoneFilter;
                const matchClass = classFilter === "All" || row['Classification'] === classFilter;
                return matchSearch && matchZone && matchClass;
            });

            renderTable(filteredData, searchInput);
        }

        function renderTable(data, searchInput) {
            const tbody = document.getElementById('tableBody');
            tbody.innerHTML = "";
            document.getElementById('recordCount').textContent = `Displaying ${data.length} records`;

            const fragment = document.createDocumentFragment();
            data.forEach(row => {
                const tr = document.createElement('tr');
                let remarksHtml = row['Remarks'] || "";
                
                if (searchInput) {
                    const escaped = searchInput.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&');
                    const regex = new RegExp(`(${escaped})`, "gi");
                    remarksHtml = remarksHtml.replace(regex, '<mark>$1</mark>');
                }

                tr.innerHTML = `<td>${row['Zone'] || ""}</td><td>${row['Classification'] || ""}</td><td>${row['Div.'] || ""}</td><td>${row['Start Date Time'] || ""}</td><td>${remarksHtml}</td>`;
                fragment.appendChild(tr);
            });
            tbody.appendChild(fragment);
        }
    </script>
</body>
</html>
"""

# --- ROUTES ---

@app.route('/')
def index():
    # Serve the search dashboard to users
    return render_template_string(USER_HTML)

@app.route('/admin')
def admin():
    # Serve the upload page to the admin
    return render_template_string(ADMIN_HTML)

@app.route('/api/data')
def get_data():
    # Send the cleaned data to the user's browser
    return jsonify(latest_report_data)

@app.route('/upload', methods=['POST'])
def upload_file():
    global latest_report_data
    if 'file' not in request.files:
        return "No file part", 400
    
    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400

    try:
        # Read the file and automatically skip preamble to find the actual headers
        df = pd.read_excel(file) if file.filename.endswith(('.xls', '.xlsx')) else pd.read_csv(file)
        
        # Find the row where "Zone" and "Remarks" exist to treat it as the header
        header_idx = df[df.apply(lambda r: row_contains_headers(r), axis=1)].index
        if len(header_idx) > 0:
            df.columns = df.iloc[header_idx[0]]
            df = df.iloc[header_idx[0] + 1:]
        
        # Clean up empty rows based on our core columns
        df = df.dropna(subset=['Zone', 'Classification', 'Remarks'])
        df = df.fillna("")
        
        # Convert the dataframe to a list of dictionaries for the frontend
        latest_report_data = df[['Zone', 'Classification', 'Div.', 'Start Date Time', 'Remarks']].to_dict(orient='records')
        
        return "File successfully processed and dashboard updated! <a href='/'>Go to Dashboard</a>"
    
    except Exception as e:
        return f"An error occurred: {str(e)}", 500

def row_contains_headers(row):
    row_str = " ".join([str(val).lower() for val in row.values])
    return "zone" in row_str and "remarks" in row_str

if __name__ == '__main__':
    # Run the server on port 5000
    app.run(host='0.0.0.0', port=5000, debug=True)