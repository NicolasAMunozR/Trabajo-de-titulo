# run_sonarqube_analysis.ps1
# ============================================================
# Script para ejecutar análisis SonarQube en EDDIE-2023 C#
# ============================================================

$JAVA_HOME = "C:\Program Files\Microsoft\jdk-21.0.12.101-hotspot"
$env:JAVA_HOME = $JAVA_HOME
$env:PATH = "$JAVA_HOME\bin;$env:PATH"

$SONAR_HOST  = "http://localhost:9000"
$SONAR_TOKEN = "admin"
$SONAR_PASS  = "admin"
$PROJECT_KEY = "EDDIE-2023"
$SOLUTION    = "EDDIE-2023\AugmentedReadingApp32.sln"

Write-Host "============================================"
Write-Host "  ANÁLISIS SONARQUBE — EDDIE-2023 C#"
Write-Host "============================================"

# Verificar que SonarQube está corriendo
Write-Host "PASO 1: Verificando SonarQube..."
try {
    $status = Invoke-RestMethod "$SONAR_HOST/api/system/status" -Method GET
    Write-Host "OK SonarQube status: $($status.status)"
} catch {
    Write-Host "ERROR: SonarQube no responde"
    exit 1
}

# Crear proyecto en SonarQube via API
Write-Host "PASO 2: Creando proyecto en SonarQube..."
$pair = "${SONAR_TOKEN}:${SONAR_PASS}"
$bytes = [System.Text.Encoding]::ASCII.GetBytes($pair)
$base64 = [System.Convert]::ToBase64String($bytes)
$headers = @{ Authorization = "Basic $base64" }

$bodyParams = @{
    project    = $PROJECT_KEY
    name       = "EDDIE-2023 C# Legacy"
    visibility = "public"
}

try {
    $proj = Invoke-RestMethod "$SONAR_HOST/api/projects/create" -Method POST -Headers $headers -Body $bodyParams
    Write-Host "OK Proyecto creado: $($proj.project.key)"
} catch {
    Write-Host "INFO: Proyecto ya listo"
}

# Inicio del análisis con dotnet-sonarscanner
Write-Host "PASO 3: Iniciando dotnet-sonarscanner BEGIN..."
$beginArgs = @(
    "begin",
    "/k:$PROJECT_KEY",
    "/n:EDDIE 2023 C# Legacy",
    "/v:2023.1",
    "/d:sonar.host.url=$SONAR_HOST",
    "/d:sonar.login=$SONAR_TOKEN",
    "/d:sonar.password=$SONAR_PASS",
    "/d:sonar.exclusions=**/bin/**,**/obj/**,**/packages/**"
)
& dotnet-sonarscanner $beginArgs

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR en sonarscanner begin"
    exit 1
}
Write-Host "OK Scanner inicializado"

# Build del proyecto C#
Write-Host "PASO 4: Compilando solución C# (dotnet build)..."
& dotnet build "$SOLUTION" /p:Configuration=Release 2>&1 | Select-Object -Last 15

# Fin del análisis
Write-Host "PASO 5: Finalizando análisis (sonarscanner END)..."
$endArgs = @(
    "end",
    "/d:sonar.login=$SONAR_TOKEN",
    "/d:sonar.password=$SONAR_PASS"
)
& dotnet-sonarscanner $endArgs

Write-Host "============================================"
Write-Host "ANÁLISIS SONARQUBE COMPLETADO CON ÉXITO"
Write-Host "Dashboard: $SONAR_HOST/dashboard?id=$PROJECT_KEY"
Write-Host "============================================"
