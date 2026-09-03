$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Speech

$projectRoot = $PSScriptRoot
$scriptPath = Join-Path $projectRoot "script.txt"
$voicePath = Join-Path $projectRoot "voice.wav"
$text = Get-Content -LiteralPath $scriptPath -Raw -Encoding UTF8

$speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer
$vietnameseVoice = $speaker.GetInstalledVoices() |
    Where-Object { $_.VoiceInfo.Culture.Name -eq "vi-VN" } |
    Select-Object -First 1

if ($null -ne $vietnameseVoice) {
    $speaker.SelectVoice($vietnameseVoice.VoiceInfo.Name)
    Write-Host "Dung voice tieng Viet:" $vietnameseVoice.VoiceInfo.Name
} else {
    Write-Warning "May chua co voice vi-VN; dang dung voice Windows mac dinh."
}

$speaker.Rate = 1
$speaker.Volume = 100
$speaker.SetOutputToWaveFile($voicePath)
$speaker.Speak($text)
$speaker.Dispose()

Write-Host "Da tao voice:" $voicePath

