<?php
session_start();
$password_definita = "robot2026"; // Cambia questa password!

if (isset($_POST['password'])) {
    if ($_POST['password'] === $password_definita) {
        $_SESSION['authorized'] = true;
    } else {
        $error = "Password errata!";
    }
}

if (isset($_GET['logout'])) {
    session_destroy();
    header("Location: index.php");
}
?>

<!DOCTYPE html>
<html lang="it">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Robot Control Center</title>
        <link rel="stylesheet" href="styles/style.css">
        <style>
            /* Control Panel Style */
            .dashboard { display: none; }
            <?php if(isset($_SESSION['authorized'])): ?>
                .login-box { display: none; }
                .dashboard { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
                .config-panel { margin-bottom: 20px; padding: 15px; background: #334155; border-radius: 10px; display: flex; flex-direction: column; gap: 15px; align-items: stretch; border: 1px solid #475569; }
                .config-panel .input-group { display: flex; flex-direction: column; gap: 5px; }
                .config-panel .ip-row { display: flex; gap: 15px; align-items: flex-end; justify-content: center; padding-bottom: 10px; border-bottom: 1px solid #475569; }
                .config-panel label { font-size: 0.8rem; color: #94a3b8; font-weight: bold; }
                .config-panel input { padding: 8px; border-radius: 5px; border: 1px solid var(--accent-color); background: #1e293b; color: white; width: 120px; }
                .config-panel button { padding: 8px 20px; background: var(--accent-color); color: white; border: none; border-radius: 5px; cursor: pointer; transition: background 0.3s; }
                .config-panel button:hover { background: #3b82f6; }
                
                details.advanced { background: #1e293b; padding: 10px; border-radius: 8px; margin-top: 5px; }
                details.advanced summary { cursor: pointer; color: #3b82f6; font-size: 0.9rem; font-weight: bold; margin-bottom: 10px; list-style: none; display: flex; align-items: center; justify-content: center; }
                details.advanced summary::before { content: "⚙️ "; }
                .calibration-grid { display: grid; grid-template-columns: auto 1fr 1fr; gap: 10px; align-items: center; text-align: left; }
                .direction-label { color: white; font-size: 0.85rem; padding-right: 10px; }
                .btn-update-calib { margin-top: 15px; width: 100%; }
            <?php endif; ?>
        </style>
    </head>
    <body>

        <div class="container">
            <?php if(!isset($_SESSION['authorized'])): ?>
                <div class="login-box">
                    <h2>Accedi al Robot</h2>
                    <form method="POST">
                        <input type="password" name="password" placeholder="Inserisci Password" required>
                        <br>
                        <button type="submit">Entra</button>
                        <?php if(isset($error)) echo "<p style='color:red'>$error</p>"; ?>
                    </form>
                </div>
            <?php else: ?>
                <h1>Robot Command Center</h1>
                <div class="config-panel">
                    <div class="ip-row">
                        <div class="input-group">
                            <label for="ipInput">Indirizzo IP ESP32</label>
                            <input type="text" id="ipInput" placeholder="es. 192.168.1.10" style="width: 200px;">
                        </div>
                        <button onclick="updateIP()">Salva IP</button>
                    </div>

                    <details class="advanced">
                        <summary>Calibrazione Avanzata (Motori/Direzioni)</summary>
                        <div class="calibration-grid">
                            <div></div><label>Motore A</label><label>Motore B</label>
                            
                            <span class="direction-label">Avanti:</span>
                            <input type="number" id="fwdA" value="255">
                            <input type="number" id="fwdB" value="255">
                            
                            <span class="direction-label">Indietro:</span>
                            <input type="number" id="bkwA" value="255">
                            <input type="number" id="bkwB" value="255">
                            
                            <span class="direction-label">Destra:</span>
                            <input type="number" id="cwA" value="200">
                            <input type="number" id="cwB" value="200">
                            
                            <span class="direction-label">Sinistra:</span>
                            <input type="number" id="ccwA" value="200">
                            <input type="number" id="ccwB" value="200">
                        </div>
                        <button class="btn-update-calib" onclick="updateSettings()">Salva Calibrazione</button>
                    </details>
                </div>
                <div class="dashboard">
                    <div>
                        <h3>Movimento</h3>
                        <div class="controls">
                            <button class="btn-up" onclick="sendCommand('AVANTI')">▲</button>
                            <button class="btn-left" onclick="sendCommand('SINISTRA')">◀</button>
                            <button class="btn-stop" onclick="sendCommand('STOP')">STOP</button>
                            <button class="btn-right" onclick="sendCommand('DESTRA')">▶</button>
                            <button class="btn-down" onclick="sendCommand('INDIETRO')">▼</button>
                        </div>
                    </div>
                    <div>
                        <h3>Mappa Labirinto</h3>
                        <div class="map-container" id="mapCanvas">
                            <p style="color: #444;">[ Mappa in caricamento... ]</p>
                        </div>
                    </div>
                </div>
                <div class="status" id="statusField">Stato: In attesa di comandi...</div>
                <br>
                <a href="?logout=1" style="color: var(--danger-color); text-decoration: none;">Disconnetti</a>
            <?php endif; ?>
        </div>

        <script>
            let ESP_IP = localStorage.getItem('esp_ip') || "172.20.10.5";

            // Imposta l'IP iniziale nell'input
            document.addEventListener("DOMContentLoaded", () => {
                const ipInput = document.getElementById('ipInput');
                if (ipInput) {
                    ipInput.value = ESP_IP;
                }
            });

            function updateIP() {
                const newIP = document.getElementById('ipInput').value;
                if (newIP) {
                    ESP_IP = newIP;
                    localStorage.setItem('esp_ip', ESP_IP);
                    document.getElementById('statusField').innerText = "Stato: IP aggiornato a " + ESP_IP;
                }
            }

            function updateSettings() {
                const status = document.getElementById('statusField');
                status.innerText = "Stato: Invio calibrazione...";

                const params = new URLSearchParams({
                    fwdA: document.getElementById('fwdA').value,
                    fwdB: document.getElementById('fwdB').value,
                    bkwA: document.getElementById('bkwA').value,
                    bkwB: document.getElementById('bkwB').value,
                    cwA:  document.getElementById('cwA').value,
                    cwB:  document.getElementById('cwB').value,
                    ccwA: document.getElementById('ccwA').value,
                    ccwB: document.getElementById('ccwB').value
                });

                fetch(`http://${ESP_IP}/update?${params.toString()}`)
                    .then(response => response.json())
                    .then(data => {
                        status.innerText = "Stato: Calibrazione salvata correttamente!";
                    })
                    .catch(err => {
                        status.innerText = "Errore: ESP32 non raggiungibile";
                        console.error(err);
                    });
            }

            function sendCommand(dir) {
                const status = document.getElementById('statusField');
                status.innerText = "Stato: Invio comando " + dir + "...";

                let listaComandi = [
                    { command: "AVANTI",   api: "move-fwd" },
                    { command: "INDIETRO", api: "move-bkw" },
                    { command: "DESTRA",   api: "turn-cw"  },
                    { command: "SINISTRA", api: "turn-ccw" },
                    { command: "STOP",     api: "stop"     }
                ]
                let requestedApiEndpoint = "";
                listaComandi.forEach((el, i) => {
                    if (el.command == dir) {
                        requestedApiEndpoint = el.api;
                    }
                });

                // Invia la richiesta HTTP all'ESP32
                fetch(`http://${ESP_IP}/${requestedApiEndpoint}`)
                    .then(response => {
                        console.log(response);
                    })
                    .catch(err => {
                        status.innerText = "Errore: ESP32 non raggiungibile";
                        console.error(err);
                    });
            }

            // Supporto tastiera
            document.addEventListener('keydown', (e) => {
                if(e.key === "ArrowUp") sendCommand('AVANTI');
                if(e.key === "ArrowDown") sendCommand('INDIETRO');
                if(e.key === "ArrowLeft") sendCommand('SINISTRA');
                if(e.key === "ArrowRight") sendCommand('DESTRA');
                if(e.key === " ") sendCommand('STOP');
            });

            document.addEventListener("DOMContentLoaded", () => {
                
                /* function getMap() {
                    let response = fetch(`http://${ESP_IP}/map`);
                    console.log(response);
                }

                setInterval(getMap, 1000); */
            });
        </script>

    </body>
</html>