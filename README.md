<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Immunofluorescence Assay Timer</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            padding: 20px;
        }
        .step {
            margin-bottom: 20px;
        }
        button {
            padding: 10px;
            background-color: #4CAF50;
            color: white;
            border: none;
            cursor: pointer;
        }
        button:disabled {
            background-color: #ddd;
            cursor: not-allowed;
        }
        .countdown {
            font-weight: bold;
            color: red;
        }
    </style>
</head>
<body>

    <h1>Immunofluorescence Assay Tracker</h1>
    <p>Current Time: <span id="currentTime"></span></p>

    <div class="step" id="step1">
        <h3>Step 1: Fixing cells with 100% methanol (10 mins)</h3>
        <button onclick="startStep(1, 10)">Start Step 1</button>
        <p id="status1"></p>
        <p class="countdown" id="countdown1"></p>
    </div>

    <div class="step" id="step2">
        <h3>Step 2: Permeabilizing cells with 0.2% Triton X-100 (10 mins)</h3>
        <button onclick="startStep(2, 10)">Start Step 2</button>
        <p id="status2"></p>
        <p class="countdown" id="countdown2"></p>
    </div>

    <div class="step" id="step3">
        <h3>Step 3: Blocking cells with 1% PBS-BSA (30 mins)</h3>
        <button onclick="startStep(3, 30)">Start Step 3</button>
        <p id="status3"></p>
        <p class="countdown" id="countdown3"></p>
    </div>

    <div class="step" id="step4">
        <h3>Step 4: Primary Antibody Incubation (1 hour)</h3>
        <button onclick="startStep(4, 60)">Start Step 4</button>
        <p id="status4"></p>
        <p class="countdown" id="countdown4"></p>
    </div>

    <div class="step" id="step5">
        <h3>Step 5: Secondary Antibody Incubation (1 hour)</h3>
        <button onclick="startStep(5, 60)">Start Step 5</button>
        <p id="status5"></p>
        <p class="countdown" id="countdown5"></p>
    </div>

    <script>
        // Function to update the live clock every second
        function updateCurrentTime() {
            const now = new Date();
            document.getElementById('currentTime').textContent = now.toLocaleTimeString();
        }

        // Call the clock update every second
        setInterval(updateCurrentTime, 1000);

        // Function to start each step with countdown
        function startStep(stepNumber, durationMinutes) {
            let startTime = new Date();
            document.querySelector(`#step${stepNumber} button`).disabled = true;
            document.querySelector(`#status${stepNumber}`).textContent = `Started at: ${startTime.toLocaleTimeString()}`;

            let countdownElement = document.getElementById(`countdown${stepNumber}`);
            let totalSeconds = durationMinutes * 60;

            let countdown = setInterval(() => {
                if (totalSeconds <= 0) {
                    clearInterval(countdown);
                    countdownElement.textContent = `Step completed!`;
                    return;
                }
                let minutes = Math.floor(totalSeconds / 60);
                let seconds = totalSeconds % 60;
                countdownElement.textContent = `Time remaining: ${minutes}m ${seconds}s`;
                totalSeconds--;
            }, 1000);  // Update countdown every second
        }
    </script>

</body>
</html>
