#include <WiFi.h>
#include <PubSubClient.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <MAX30105.h>
#include <heartRate.h>
#include <Adafruit_MLX90614.h>
#include <driver/i2s.h>

// --- Network & MQTT Settings ---
const char* ssid = "SSID"; //WIFI SSID
const char* password = "PASSWORD"; //WIFI Password
const char* mqtt_server = "IPv4"; // Fog Node IP(cmd->ipconfig)
const char* mqtt_topic = "smedikit/vitals";

WiFiClient espClient;
PubSubClient client(espClient);

// --- Pin Definitions (SmediKit V4 Blueprint) ---
#define I2C_SDA 8
#define I2C_SCL 9
#define I2S_WS 15
#define I2S_SCK 16
#define I2S_SD 17

// --- Objects ---
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);
MAX30105 particleSensor;
Adafruit_MLX90614 mlx = Adafruit_MLX90614();

// --- State Machine & Timers ---
enum SystemState { STANDBY, ACTIVE };
SystemState currentState = STANDBY;
unsigned long activeStartTime = 0;
const unsigned long DIAGNOSTIC_DURATION = 60000; // 60 seconds

// --- Acoustic Settings ---
unsigned long lastAcousticTrigger = 0;
const unsigned long ACOUSTIC_COOLDOWN = 2000; // 2 seconds
const float ACOUSTIC_THRESHOLD = 3000.0; // The new sensitivity baseline

// --- SpO2 & BPM Variables ---
const byte RATE_SIZE = 4; 
byte rates[RATE_SIZE]; 
byte rateSpot = 0;
long lastBeat = 0; 
float beatsPerMinute = 0;
int beatAvg = 0;
int spo2 = 0;

void setup() {
  Serial.begin(115200);
  delay(2000); // Give the USB port 2 seconds to wake up
  Serial.println("\n--- SmediKit V4 Boot Sequence Started ---");
  Wire.begin(I2C_SDA, I2C_SCL);

  Serial.println("Initializing OLED...");
  if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println(F("SSD1306 allocation failed"));
    for(;;);
  }
  display.clearDisplay();
  display.setTextColor(WHITE);
  
  Serial.println("Initializing MLX90614...");
  if (!mlx.begin()) {
    Serial.println("Error connecting to MLX sensor.");
    for(;;);
  }

  Serial.println("Initializing MAX30102...");
  if (!particleSensor.begin(Wire, I2C_SPEED_FAST)) {
    Serial.println("MAX30102 was not found.");
    for(;;);
  }
  
  byte ledBrightness = 60; 
  byte sampleAverage = 4; 
  byte ledMode = 2; 
  int sampleRate = 100; 
  int pulseWidth = 411; 
  int adcRange = 4096; 
  particleSensor.setup(ledBrightness, sampleAverage, ledMode, sampleRate, pulseWidth, adcRange);

  setup_wifi();
  client.setServer(mqtt_server, 1883);

  Serial.println("Initializing I2S Microphone...");
  i2s_config_t i2s_config = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
    .sample_rate = 16000,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_32BIT,
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = I2S_COMM_FORMAT_I2S,
    .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
    .dma_buf_count = 4,
    .dma_buf_len = 1024,
    .use_apll = false,
    .tx_desc_auto_clear = false,
    .fixed_mclk = 0
  };
  i2s_pin_config_t pin_config = {
    .bck_io_num = I2S_SCK,
    .ws_io_num = I2S_WS,
    .data_out_num = I2S_PIN_NO_CHANGE,
    .data_in_num = I2S_SD
  };
  i2s_driver_install(I2S_NUM_0, &i2s_config, 0, NULL);
  i2s_set_pin(I2S_NUM_0, &pin_config);

  Serial.println("Hardware Init Complete. Entering STANDBY.");
  drawStandbyScreen();
}

void setup_wifi() {
  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    yield();
  }
  Serial.println("\nWiFi Connected!");
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection to: ");
    Serial.println(mqtt_server);
    if (client.connect("SmediKit_EdgeNode")) {
      Serial.println("MQTT Connected!");
    } else {
      Serial.print("Failed, rc=");
      Serial.print(client.state());
      Serial.println(" - Retrying in 5 seconds...");
      delay(5000);
      yield();
    }
  }
}

float calculateRMS(int32_t *samples, int num_samples) {
  float sum_squares = 0;
  for (int i = 0; i < num_samples; i++) {
    int32_t sample = samples[i] >> 14; 
    sum_squares += (float)(sample * sample);
  }
  return sqrt(sum_squares / num_samples);
}

void drawStandbyScreen() {
  display.clearDisplay();
  display.setTextSize(1);
  display.setCursor(10, 20);
  display.println("STANDBY MODE");
  display.setCursor(10, 40);
  display.println("Say 'START' Loudly!");
  display.display();
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
  yield(); // Prevent Watchdog Crash

  if (currentState == STANDBY) {
    size_t bytes_read;
    int32_t i2s_data[256];
    i2s_read(I2S_NUM_0, &i2s_data, sizeof(i2s_data), &bytes_read, portMAX_DELAY);
    
    int samples_read = bytes_read / sizeof(int32_t);
    float rms = calculateRMS(i2s_data, samples_read);

    // WAKE TRIGGER WITH DEBOUNCE
    if (rms > ACOUSTIC_THRESHOLD && (millis() - lastAcousticTrigger > ACOUSTIC_COOLDOWN)) { 
      lastAcousticTrigger = millis(); // Lock out the mic for 2 seconds
      currentState = ACTIVE;
      activeStartTime = millis();
      
      // HARD RESET ALL BIOMETRICS ON WAKE
      beatAvg = 0;
      spo2 = 0;
      rateSpot = 0;
      lastBeat = millis();
      for (byte x = 0 ; x < RATE_SIZE ; x++) rates[x] = 0;
      particleSensor.clearFIFO(); 
      
      display.clearDisplay();
      display.setCursor(10, 20);
      display.println("SmediKit ACTIVE");
      display.display();
    }
  } 
  else if (currentState == ACTIVE) {
    unsigned long timeElapsed = millis() - activeStartTime;
    
    // 1. Time-based Stop Trigger
    if (timeElapsed >= DIAGNOSTIC_DURATION) {
      currentState = STANDBY;
      client.publish(mqtt_topic, "{\"bpm\":0, \"spo2\":0, \"temp\":0.00}"); // Reset Dashboard
      drawStandbyScreen();
      return;
    }

    // 2. Non-Blocking Acoustic "STOP" Trigger WITH DEBOUNCE
    size_t bytes_read;
    int32_t i2s_data[256];
    // 0 delay allows the loop to check the mic without pausing the heart monitor
    i2s_read(I2S_NUM_0, &i2s_data, sizeof(i2s_data), &bytes_read, 0); 
    
    if (bytes_read > 0) {
      int samples_read = bytes_read / sizeof(int32_t);
      float rms = calculateRMS(i2s_data, samples_read);
      
      if (rms > ACOUSTIC_THRESHOLD && (millis() - lastAcousticTrigger > ACOUSTIC_COOLDOWN)) { 
        lastAcousticTrigger = millis(); // Lock out the mic for 2 seconds
        currentState = STANDBY;
        client.publish(mqtt_topic, "{\"bpm\":0, \"spo2\":0, \"temp\":0.00}"); // Reset Dashboard
        drawStandbyScreen();
        return; 
      }
    }

    // 3. Read Wrist Temp 
    float objTemp = mlx.readObjectTempC(); 

    // 4. Process MAX30102 FIFO Buffer
    particleSensor.check(); 
    
    while (particleSensor.available()) {
      long irValue = particleSensor.getFIFOIR();
      long redValue = particleSensor.getFIFORed();
      particleSensor.nextSample(); 

      // THE PROXIMITY GATE (Fixes phantom beats and SpO2 latching)
      if (irValue < 50000) {
        beatAvg = 0;
        spo2 = 0;
        rateSpot = 0;
        for (byte x = 0 ; x < RATE_SIZE ; x++) rates[x] = 0;
      } 
      else {
        // Finger IS present. Run the algorithms.
        if (checkForBeat(irValue) == true) {
          long delta = millis() - lastBeat;
          lastBeat = millis();

          if (delta > 300 && delta < 2000) {
            beatsPerMinute = 60 / (delta / 1000.0);
            rates[rateSpot++] = (byte)beatsPerMinute;
            rateSpot %= RATE_SIZE;

            beatAvg = 0;
            byte validBeats = 0;
            for (byte x = 0 ; x < RATE_SIZE ; x++) {
              if (rates[x] > 0) {
                beatAvg += rates[x];
                validBeats++;
              }
            }
            if (validBeats > 0) {
              beatAvg /= validBeats; 
            }
          }
        }
        
        if (irValue > 50000 && redValue > 50000) {
          float ratio = (float)redValue / (float)irValue;
          spo2 = 110 - (15 * ratio); 
          if (spo2 > 100) spo2 = 100;
          if (spo2 < 80) spo2 = 80;
        }
      }
    }

    // 5. Update OLED (500ms) - REDESIGNED FOR LARGE FONT
    static unsigned long lastOLEDUpdate = 0;
    if (millis() - lastOLEDUpdate > 500) {
      lastOLEDUpdate = millis();
      display.clearDisplay();
      
      // Top Status Bar: Time & Stop Instruction (Size 1)
      display.setTextSize(1);
      display.setCursor(0, 0);
      display.print("Time: ");
      display.print((DIAGNOSTIC_DURATION - timeElapsed) / 1000);
      display.print("s | Say STOP");

      // Vitals: Large Font (Size 2)
      display.setTextSize(2);
      
      display.setCursor(0, 16);
      display.print("BPM:"); display.println(beatAvg);
      
      display.setCursor(0, 32);
      display.print("SpO2 :"); display.print(spo2); display.println("%");
      
      display.setCursor(0, 48);
      display.print("Tmp:"); display.print(objTemp, 1); // 1 decimal place saves space
      display.write(247); 
      display.println("C");
      
      display.display();
    }

    // 6. Publish MQTT (1000ms)
    static unsigned long lastMsg = 0;
    if (millis() - lastMsg > 1000) {
      lastMsg = millis();
      char payload[100];
      snprintf(payload, sizeof(payload), "{\"bpm\":%d, \"spo2\":%d, \"temp\":%.2f}", beatAvg, spo2, objTemp);
      client.publish(mqtt_topic, payload);
    }
  }
}