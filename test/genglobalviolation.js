//  ChatGPT generated code example with Global Variable Violation (Commit 9)

let recording = false;
let audioRecorder;
let audioBlob;

function toggleRecording() {
    if (!recording) {
        startRecording();
    } else {
        stopRecording();
    }
}

function startRecording() {
    // TODO: Start recording.
    // Change button to "Stop Recording".
    document.getElementById('recordButton').textContent = 'Stop Recording';
    recording = true;
}

function stopRecording() {
    // TODO: Stop recording.
    // Change button to "Start Recording".
    document.getElementById('recordButton').textContent = 'Start Recording';
    recording = false;

    // TODO: Send audio to Whisper API.
    // TODO: Send transcription to GPT-3 API.
}
