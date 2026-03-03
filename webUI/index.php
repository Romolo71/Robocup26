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
                .config-panel { margin-bottom: 20px; padding: 15px; background: #334155; border-radius: 10px; display: flex; flex-wrap: wrap; gap: 10px; justify-content: center; align-items: center; }
                .config-panel input { padding: 8px; border-radius: 5px; border: 1px solid var(--accent-color); background: #1e293b; color: white; width: 200px; }
                .config-panel button { padding: 8px 15px; }
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
                    <input type="text" id="ipInput" placeholder="IP ESP32 (es. 192.168.1.10)">
                    <button onclick="updateIP()">Salva IP</button>
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
                
                function getMap() {
                    let response = fetch(`http://${ESP_IP}/map`);
                    console.log(response);
                }

                setInterval(getMap, 1000);
            });
        </script>

    </body>
</html>