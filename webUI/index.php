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
        <style>
            :root {
                --bg-color: #0f172a;
                --accent-color: #38bdf8;
                --danger-color: #ef4444;
                --card-bg: #1e293b;
            }

            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: var(--bg-color);
                color: white;
                margin: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
            }

            .container {
                background: var(--card-bg);
                padding: 2rem;
                border-radius: 15px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.5);
                width: 90%;
                max-width: 800px;
                text-align: center;
            }

            /* Login Style */
            .login-box input {
                padding: 10px;
                border-radius: 5px;
                border: none;
                margin-bottom: 10px;
            }

            /* Control Panel Style */
            .dashboard { display: none; }
            <?php if(isset($_SESSION['authorized'])): ?>
                .login-box { display: none; }
                .dashboard { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
            <?php endif; ?>

            .controls {
                display: grid;
                grid-template-areas: 
                    ". up ."
                    "left stop right"
                    ". down .";
                gap: 10px;
                justify-content: center;
            }

            button {
                background: #334155;
                color: white;
                border: none;
                padding: 20px;
                border-radius: 10px;
                cursor: pointer;
                transition: 0.3s;
                font-weight: bold;
            }

            button:active { background: var(--accent-color); transform: scale(0.95); }
            .btn-up { grid-area: up; }
            .btn-left { grid-area: left; }
            .btn-right { grid-area: right; }
            .btn-down { grid-area: down; }
            .btn-stop { grid-area: stop; background: var(--danger-color); }

            .map-container {
                background: #000;
                border: 2px solid var(--accent-color);
                border-radius: 10px;
                min-height: 200px;
                display: flex;
                align-items: center;
                justify-content: center;
            }

            .status { margin-top: 20px; font-size: 0.9rem; color: #94a3b8; }
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
            function sendCommand(dir) {
                const status = document.getElementById('statusField');
                status.innerText = "Stato: Invio comando " + dir + "...";
                
                // Qui invieresti il comando al tuo robot tramite fetch o WebSocket
                console.log("Eseguo: " + dir);
                
                // Simulazione feedback
                setTimeout(() => {
                    status.innerText = "Stato: Eseguito " + dir;
                }, 500);
            }

            // Supporto tastiera
            document.addEventListener('keydown', (e) => {
                if(e.key === "ArrowUp") sendCommand('AVANTI');
                if(e.key === "ArrowDown") sendCommand('INDIETRO');
                if(e.key === "ArrowLeft") sendCommand('SINISTRA');
                if(e.key === "ArrowRight") sendCommand('DESTRA');
                if(e.key === " ") sendCommand('STOP');
            });
        </script>

    </body>
</html>