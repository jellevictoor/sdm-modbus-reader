"""
FastAPI web interface for SDM meter data
"""
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from .data_store import meter_store

app = FastAPI(title="SDM Meter Monitor")


@app.get("/api/meters")
async def get_meters():
    """Get all meter data"""
    return meter_store.get_all_meters()


@app.get("/api/meters/{meter_id}")
async def get_meter(meter_id: int):
    """Get specific meter data"""
    data = meter_store.get_meter(meter_id)
    if data is None:
        return {"error": "Meter not found"}
    return data


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main HTML page"""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SDM Meter Monitor</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1600px;
            margin: 0 auto;
        }

        h1 {
            color: white;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }

        .last-update {
            color: rgba(255,255,255,0.9);
            text-align: center;
            margin-bottom: 20px;
            font-size: 0.9em;
        }

        .meter-grid {
            display: grid;
            gap: 20px;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
        }

        .meter-card {
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 8px 16px rgba(0,0,0,0.2);
        }

        .meter-card.monophase {
            max-width: 275px;
        }

        .meter-card.threephase {
            max-width: 500px;
        }

        .meter-header {
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
            margin-bottom: 15px;
        }

        .meter-name {
            font-size: 1.3em;
            font-weight: bold;
            color: #333;
        }

        .meter-type {
            color: #667eea;
            font-size: 0.9em;
            font-weight: 600;
        }

        .meter-id {
            color: #999;
            font-size: 0.85em;
        }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        th {
            background: #f8f9fa;
            padding: 8px;
            text-align: left;
            font-size: 0.85em;
            color: #666;
            font-weight: 600;
        }

        th:not(:first-child) {
            text-align: right;
        }

        td {
            padding: 8px;
            border-bottom: 1px solid #eee;
        }

        .phase-header {
            background: #667eea;
            color: white;
            font-weight: bold;
            text-align: center;
        }

        .metric-name {
            color: #555;
            font-size: 0.9em;
        }

        .metric-value {
            font-weight: 600;
            color: #333;
            text-align: right;
            font-variant-numeric: tabular-nums;
            white-space: nowrap;
        }

        .metric-unit {
            color: #999;
            font-size: 0.75em;
            margin-left: 0.3em;
        }

        .error {
            background: #fee;
            color: #c33;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }

        .no-data {
            text-align: center;
            color: #999;
            padding: 40px;
        }

        @media (max-width: 768px) {
            .meter-grid {
                grid-template-columns: 1fr;
            }

            h1 {
                font-size: 1.8em;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>⚡ SDM Meter Monitor</h1>
        <div class="last-update" id="lastUpdate">Loading...</div>
        <div class="meter-grid" id="meterGrid"></div>
    </div>

    <script>
        function formatValue(value, decimals = 2) {
            if (value === null || value === undefined) return 'N/A';
            const num = Number(value).toFixed(decimals);
            const parts = num.split('.');
            parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',');
            return parts.join('.');
        }

        function getUnit(metric) {
            if (metric.includes('Voltage')) return 'V';
            if (metric.includes('Current')) return 'A';
            if (metric.includes('Power') && !metric.includes('Apparent') && !metric.includes('Reactive')) return 'W';
            if (metric.includes('ApparentPower')) return 'VA';
            if (metric.includes('ReactivePower')) return 'VAR';
            if (metric.includes('Frequency')) return 'Hz';
            if (metric.includes('Cosphi')) return '';
            if (metric.includes('PhaseAngle')) return '°';
            if (metric.includes('THD')) return '%';
            if (metric.includes('Import') || metric.includes('Export') || metric.includes('Sum')) return 'kWh';
            if (metric.includes('Reactive')) return 'kVARh';
            return '';
        }

        function getIcon(metric) {
            if (metric.includes('Voltage')) return '⚡';
            if (metric.includes('Current')) return '〰️';
            if (metric.includes('Power') && !metric.includes('Apparent') && !metric.includes('Reactive')) return '🔌';
            if (metric.includes('ApparentPower')) return '💫';
            if (metric.includes('ReactivePower')) return '🔄';
            if (metric.includes('Frequency')) return '📊';
            if (metric.includes('Cosphi')) return '📐';
            if (metric.includes('PhaseAngle')) return '∠';
            if (metric.includes('Import')) return '📥';
            if (metric.includes('Export')) return '📤';
            if (metric.includes('Sum')) return '∑';
            return '';
        }

        function createPhaseTable(data, phase) {
            const metrics = ['Voltage', 'Current', 'Power', 'ApparentPower', 'ReactivePower', 'Cosphi', 'PhaseAngle'];
            let html = '';

            for (const metric of metrics) {
                const key = `${metric}/${phase}`;
                if (data[key] !== undefined) {
                    const unit = getUnit(metric);
                    html += `
                        <tr>
                            <td class="metric-name">${metric}</td>
                            <td class="metric-value">${formatValue(data[key])} <span class="metric-unit">${unit}</span></td>
                        </tr>
                    `;
                }
            }

            return html;
        }

        function createMonophaseTable(data) {
            const metrics = [
                'Voltage', 'Current', 'Power', 'ApparentPower', 'ReactivePower',
                'Cosphi', 'PhaseAngle', 'Frequency', 'Import', 'Export', 'Sum'
            ];

            let html = '<table><thead><tr><th>Metric</th><th>Value</th></tr></thead><tbody>';

            for (const metric of metrics) {
                if (data[metric] !== undefined) {
                    const unit = getUnit(metric);
                    const icon = getIcon(metric);
                    html += `
                        <tr>
                            <td class="metric-name">${icon} ${metric}</td>
                            <td class="metric-value">${formatValue(data[metric])} <span class="metric-unit">${unit}</span></td>
                        </tr>
                    `;
                }
            }

            html += '</tbody></table>';
            return html;
        }

        function create3PhaseTable(data) {
            const metrics = ['Voltage', 'Current', 'Power', 'ApparentPower', 'ReactivePower', 'Cosphi', 'PhaseAngle', 'Frequency'];

            let html = '<table><thead><tr><th>Metric</th><th>L1</th><th>L2</th><th>L3</th><th>Total/Avg</th></tr></thead><tbody>';

            // Phase-specific metrics in compact format with total
            for (const metric of metrics) {
                const l1 = data[`${metric}/L1`];
                const l2 = data[`${metric}/L2`];
                const l3 = data[`${metric}/L3`];
                const total = data[metric];

                if (l1 !== undefined || l2 !== undefined || l3 !== undefined || total !== undefined) {
                    const unit = getUnit(metric);
                    const icon = getIcon(metric);
                    html += `
                        <tr>
                            <td class="metric-name">${icon} ${metric}</td>
                            <td class="metric-value">${formatValue(l1)} <span class="metric-unit">${unit}</span></td>
                            <td class="metric-value">${formatValue(l2)} <span class="metric-unit">${unit}</span></td>
                            <td class="metric-value">${formatValue(l3)} <span class="metric-unit">${unit}</span></td>
                            <td class="metric-value">${total !== undefined ? formatValue(total) + ' <span class="metric-unit">' + unit + '</span>' : ''}</td>
                        </tr>
                    `;
                }
            }

            html += '</tbody>';

            // Energy totals section (no per-phase data)
            const energyMetrics = ['Import', 'Export', 'Sum'];
            const hasEnergy = energyMetrics.some(m => data[m] !== undefined);

            if (hasEnergy) {
                html += '<thead><tr><th colspan="5" class="phase-header">Energy</th></tr></thead><tbody>';
                for (const metric of energyMetrics) {
                    if (data[metric] !== undefined) {
                        const unit = getUnit(metric);
                        const icon = getIcon(metric);
                        html += `
                            <tr>
                                <td class="metric-name">${icon} ${metric}</td>
                                <td colspan="4" class="metric-value">${formatValue(data[metric])} <span class="metric-unit">${unit}</span></td>
                            </tr>
                        `;
                    }
                }
                html += '</tbody>';
            }

            html += '</table>';
            return html;
        }

        function renderMeters(meters) {
            const grid = document.getElementById('meterGrid');

            if (!meters || Object.keys(meters).length === 0) {
                grid.innerHTML = '<div class="no-data">No meter data available yet. Waiting for readings...</div>';
                return;
            }

            grid.innerHTML = '';

            for (const [meterId, meter] of Object.entries(meters)) {
                const card = document.createElement('div');
                const isThreePhase = meter.meter_type === 'SDM630';
                card.className = 'meter-card ' + (isThreePhase ? 'threephase' : 'monophase');

                const tableHtml = isThreePhase
                    ? create3PhaseTable(meter.data)
                    : createMonophaseTable(meter.data);

                card.innerHTML = `
                    <div class="meter-header">
                        <div class="meter-name">${meter.meter_name}</div>
                        <div class="meter-type">${meter.meter_type}</div>
                        <div class="meter-id">ID: ${meter.meter_id}</div>
                    </div>
                    ${tableHtml}
                `;

                grid.appendChild(card);
            }

            // Update timestamp
            const now = new Date().toLocaleString();
            document.getElementById('lastUpdate').textContent = `Last updated: ${now}`;
        }

        async function fetchMeters() {
            try {
                const response = await fetch('/api/meters');
                const data = await response.json();
                renderMeters(data);
            } catch (error) {
                console.error('Error fetching meters:', error);
                document.getElementById('meterGrid').innerHTML =
                    '<div class="error">Failed to load meter data. Please check the connection.</div>';
            }
        }

        // Initial fetch
        fetchMeters();

        // Auto-refresh every 5 seconds
        setInterval(fetchMeters, 5000);
    </script>
</body>
</html>
    """