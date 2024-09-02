#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_MPU6050.h>

const char* ssid = "Galaxy S9+f327";
const char* password = "wuse7127";
const char* serverName = "http://192.168.17.78:5000/data";  // Adresse IP du serveur Flask

// Ajout de l'identifiant du capteur ou joueur
const char* sensorID = "Player_1";  // Remplacez par un identifiant unique pour chaque capteur

Adafruit_MPU6050 mpu;

const float gravity = 9.81;          // Accélération due à la gravité en m/s²
const float shockThreshold = 50.0;  // Seuil de détection de choc en m/s²

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(1000);
    Serial.print("Connecting to WiFi... Attempt ");
    Serial.println(attempts + 1);
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("Connected to WiFi");
  } else {
    Serial.println("Failed to connect to WiFi");
  }

  if (!mpu.begin()) {
    Serial.println("Impossible de trouver un MPU6050. Vérifie les connexions !");
    while (1);
  }

  mpu.setAccelerometerRange(MPU6050_RANGE_16_G);  // Plage de ±16g
  mpu.setGyroRange(MPU6050_RANGE_250_DEG);
  mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);

  Serial.println("MPU6050 prêt !");
}


void loop() {
  sensors_event_t accelEvent;
  sensors_event_t gyroEvent;
  sensors_event_t tempEvent;

  // Obtenir les événements pour l'accéléromètre, le gyroscope et la température
  mpu.getEvent(&accelEvent, &gyroEvent, &tempEvent);

  float accelX = accelEvent.acceleration.x;
  float accelY = accelEvent.acceleration.y;
  float accelZ = accelEvent.acceleration.z;

  // Vérifier la détection de choc
  bool shockDetected = (fabs(accelX) > shockThreshold || 
                        fabs(accelY) > shockThreshold || 
                        fabs(accelZ - gravity) > shockThreshold);

  if (shockDetected) {
    Serial.println("Choc détecté !");

    // Préparation du JSON
    StaticJsonDocument<200> doc;
    doc["sensorID"] = sensorID;  // Ajout de l'identifiant du capteur
    doc["accelX"] = accelX;
    doc["accelY"] = accelY;
    doc["accelZ"] = accelZ;
    doc["shockDetected"] = shockDetected;

    char jsonBuffer[512];
    serializeJson(doc, jsonBuffer);

    // Envoi des données au serveur
    if (WiFi.status() == WL_CONNECTED) {
      HTTPClient http;
      http.begin(serverName);
      http.addHeader("Content-Type", "application/json");

      int httpResponseCode = http.POST(jsonBuffer);

      if (httpResponseCode > 0) {
        String response = http.getString();
        Serial.println(httpResponseCode);
        Serial.println(response);
      } else {
        Serial.print("Error on sending POST: ");
        Serial.println(httpResponseCode);
      }

      http.end();
    } else {
      Serial.println("Error in WiFi connection");
    }
  }

  delay(1000);  // Envoi des données toutes les secondes
}
