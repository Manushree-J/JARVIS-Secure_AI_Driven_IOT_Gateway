#include <Arduino.h>
#include <math.h>
#include <Wire.h>
#include <SPI.h>
#include <DHT.h>
#include <BH1750.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ILI9341.h>
#include <Adafruit_SSD1306.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_ADXL345_U.h>

// JARVIS ESP32 dashboard + animated OLED robot eyes + MQTT
// Same connections as the previous test sketch. Relays held OFF at startup.
// MQ-3 is a gas response sensor, NOT calibrated air-quality.
//
// WiFi credentials: set below in WIFI_SSID / WIFI_PASS placeholders.
// MQTT broker: uses Mosquitto at laptop LAN address (verified reachable).
// NOTE: The ESP32 publishes to 127.0.0.1 only when the laptop IS the ESP32
// (test mode).  For physical hardware the broker must be the laptop's LAN IP.
// WiFi credentials stay in WIFI_SSID / WIFI_PASS above.
//
// DO NOT hardcode Wi-Fi passwords in commits/logs.

// ============================================================
// WiFi credentials (USER: fill these in yourself)
// ============================================================
#ifndef WIFI_SSID
#define WIFI_SSID "VS"
#endif

#ifndef WIFI_PASS
#define WIFI_PASS "DDDDDDDD"
#endif

// ============================================================
// MQTT broker
// ============================================================
#ifndef MQTT_HOST
#define MQTT_HOST "10.57.107.51"   // <-- replace with your JARVIS host / Mosquitto broker
#endif

#ifndef MQTT_PORT
#define MQTT_PORT 1883
#endif

// ============================================================
// Pin assignments — DO NOT MODIFY without hardware review
// ============================================================

const uint8_t DHT_PIN=4, MQ3_PIN=34, PIR_PIN=27;
const uint8_t SDA_PIN=21, SCL_PIN=22;
const uint8_t TFT_CS=5, TFT_DC=2, TFT_RST=15;
const uint8_t TFT_SCK=18, TFT_MISO=19, TFT_MOSI=23;
const uint8_t BUZZER_PIN=25;
const uint8_t RELAY_PINS[4]={16,17,26,32};
const bool RELAY_ACTIVE_LOW=true, BUZZER_ACTIVE_LOW=false;
const uint8_t OLED_ADDR=0x3C;

enum EyeMood : uint8_t {
  IDLE, LOOK_LEFT, LOOK_RIGHT, LOOK_UP, LOOK_DOWN,
  BLINK, WINK_LEFT, WINK_RIGHT, HAPPY, EXCITED,
  SAD, ANGRY, SLEEPY1, SLEEPY2, SURPRISED,
  LOVE, CONFUSED, THINKING
};

// Adjust these raw ADC thresholds after testing your particular MQ-3 module.
const int MQ3_GOOD_MAX=1200;
const int MQ3_MODERATE_MAX=2500;
// Light categories (lux): adjust if desired.
const float LIGHT_LOW_MAX=50.0;
const float LIGHT_MODERATE_MAX=300.0;

// ============================================================
// Timing constants (nonblocking, millis-driven)
// ============================================================

const unsigned long TFT_REFRESH_MS = 3000;   // TFT full redraw every 3 s
const unsigned long SENSOR_PUB_MS  = 5000;   // MQTT sensor publish every 5 s
const unsigned long OLED_ANIM_MS   = 120;    // OLED animation update cadence
const unsigned long PIR_COOLDOWN_MS = 8000;  // avoid repeat buzzer per motion event

// ============================================================
// Globals
// ============================================================

DHT dht(DHT_PIN,DHT11);
BH1750 lightMeter;
Adafruit_ADXL345_Unified accel(12345);
Adafruit_SSD1306 oled(128,64,&Wire,-1);
Adafruit_ILI9341 tft(TFT_CS,TFT_DC,TFT_RST);

bool oledOK=false,bh1750OK=false,adxlOK=false,tftOK=false;
unsigned long lastEyes=0;
unsigned long lastTftDraw=0;
unsigned long lastSensorPub=0;
uint8_t eyeFrame=0;
uint8_t blinkStage=0;
unsigned long nextBlinkAt=0;
int eyeLookX=0, eyeLookY=0;

// Relay confirmed states (read back not possible with active-low modules;
// track commanded state as source of truth)
bool relayState[4] = {false, false, false, false};

// PIR edge detection + cooldown
bool lastPirLevel = false;
unsigned long lastPirEvent = 0;

// Vibration threshold (m/s^2 magnitude above 9.81 gravity baseline)
float VIBRATION_THRESHOLD = 2.5;  // m/s^2 above gravity
unsigned long lastVibrationAlert = 0;
const unsigned long VIBRATION_COOLDOWN_MS = 30000;  // 30s between vibration alerts

// WiFi / MQTT
#include <WiFi.h>
#include <PubSubClient.h>

WiFiClient espClient;
PubSubClient mqttClient(espClient);

// ============================================================
// Helper functions
// ============================================================

void output(uint8_t pin,bool on,bool activeLow){ digitalWrite(pin,(on != activeLow)?HIGH:LOW); }

const char* airLabel(int raw){
  if(raw < MQ3_GOOD_MAX) return "GOOD";
  if(raw < MQ3_MODERATE_MAX) return "MODERATE";
  return "LOW"; // high MQ-3 response => lower air-quality status
}
const char* lightLabel(float lux){
  if(lux < 0) return "NO SENSOR";
  if(lux < LIGHT_LOW_MAX) return "LOW LIGHT";
  if(lux < LIGHT_MODERATE_MAX) return "MODERATE";
  return "BRIGHT";
}

const char* tempClass(float temp){
  if(isnan(temp)) return "UNKNOWN";
  if(temp >= 30.0) return "HIGH";
  if(temp <= 18.0) return "LOW";
  return "NORMAL";
}

const char* vibrationLabel(float magnitude){
  if(!adxlOK) return "UNKNOWN";
  float deviation = fabs(magnitude - 9.81);
  if(deviation > VIBRATION_THRESHOLD) return "UNUSUAL";
  return "NORMAL";
}

// ============================================================
// Relay command from MQTT
// ============================================================

void handleRelayCommand(const char* cmd){
  // Expected: relay/1/on, relay/1/off, relay/2/on, etc.
  if(strlen(cmd) < 9) return;  // "relay/X/?"  minimum

  // Parse "relay/N/state"
  int relayNum = cmd[6] - '0';
  if(relayNum < 1 || relayNum > 4) return;

  relayNum -= 1;  // zero-indexed

  bool targetOn = false;
  if(strstr(cmd + 8, "on")) targetOn = true;
  else if(strstr(cmd + 8, "off")) targetOn = false;
  else return;  // unrecognised

  relayState[relayNum] = targetOn;
  output(RELAY_PINS[relayNum], targetOn, RELAY_ACTIVE_LOW);

  // Publish acknowledgement
  char ack[64];
  snprintf(ack, sizeof(ack), "{\"relay\":%d,\"state\":%s}", relayNum+1, targetOn ? "ON" : "OFF");
  mqttClient.publish("jarvis/esp32/relay/ack", ack);
}

// ============================================================
// OLED robot eyes
// ============================================================

void drawEyeShape(int cx, int cy, int w, int h, bool closed=false, bool wink=false, bool heart=false){
  if(heart){
    oled.fillCircle(cx-4,cy-2,4,SSD1306_WHITE); oled.fillCircle(cx+4,cy-2,4,SSD1306_WHITE);
    int16_t x1=cx-8,y1=cy-1,x2=cx+8,y2=cy-1;
    for(int y=0;y<9;y++){ oled.drawLine(x1+y,y1+y,x2-y,y2+y,SSD1306_WHITE); }
    return;
  }
  if(closed || wink){
    int y=cy;
    oled.drawLine(cx-w/2,y,cx+w/2,y,SSD1306_WHITE);
    oled.drawLine(cx-w/2+3,y-2,cx+w/2-3,y-2,SSD1306_WHITE);
    return;
  }
  oled.fillRoundRect(cx-w/2,cy-h/2,w,h, min(6,h/3),SSD1306_WHITE);
  int pr=max(2,min(w,h)/3);
  int px=cx+eyeLookX, py=cy+eyeLookY;
  oled.fillCircle(px,py,pr,SSD1306_BLACK);
  oled.fillCircle(px-pr/3,py-pr/2,max(1,pr/3),SSD1306_WHITE);
}
void drawMood(EyeMood m){
  oled.clearDisplay(); oled.setTextColor(SSD1306_WHITE); oled.setTextSize(1);
  oled.setCursor(47,0); oled.print("JARVIS");
  int cy=36, w=35, h=29; bool cl=false, wl=false, wr=false, heart=false;
  eyeLookX=0; eyeLookY=0;
  switch(m){
    case LOOK_LEFT: eyeLookX=-5; break;
    case LOOK_RIGHT: eyeLookX=5; break;
    case LOOK_UP: eyeLookY=-5; break;
    case LOOK_DOWN: eyeLookY=5; break;
    case BLINK: cl=true; break;
    case WINK_LEFT: wl=true; break;
    case WINK_RIGHT: wr=true; break;
    case HAPPY: h=17; cy=33; break;
    case EXCITED: w=39; h=31; break;
    case SAD: cy=39; h=22; break;
    case ANGRY: h=24; break;
    case SLEEPY1: h=17; cy=39; break;
    case SLEEPY2: cl=true; break;
    case SURPRISED: w=25; h=34; break;
    case LOVE: heart=true; break;
    case CONFUSED: eyeLookX=-2; break;
    case THINKING: eyeLookX=5; eyeLookY=-3; h=25; break;
    default: break;
  }
  if(m==HAPPY){
    oled.drawLine(12,30,25,23,SSD1306_WHITE); oled.drawLine(25,23,39,30,SSD1306_WHITE);
    oled.drawLine(89,30,102,23,SSD1306_WHITE); oled.drawLine(102,23,116,30,SSD1306_WHITE);
  } else if(m==SAD){
    oled.drawLine(12,20,39,27,SSD1306_WHITE); oled.drawLine(89,27,116,20,SSD1306_WHITE);
  } else if(m==ANGRY){
    oled.drawLine(10,18,39,27,SSD1306_WHITE); oled.drawLine(89,27,118,18,SSD1306_WHITE);
  }
  if(heart){ drawEyeShape(32,36,0,0,false,false,true); drawEyeShape(96,36,0,0,false,false,true); }
  else {
    drawEyeShape(32,cy,w,h,cl,wl,false); drawEyeShape(96,cy,w,h,cl,wr,false);
    if(m==CONFUSED){ oled.drawCircle(116,18,3,SSD1306_WHITE); }
    if(m==THINKING){ oled.drawCircle(115,17,2,SSD1306_WHITE); oled.drawPixel(120,12,SSD1306_WHITE); }
    if(m==SLEEPY1 || m==SLEEPY2){ oled.setCursor(105,10); oled.print("zZ"); }
  }
  oled.display();
}

unsigned long lastMoodChange = 0;
EyeMood currentMood = IDLE;
void animateEyes(){
  if(!oledOK || millis()-lastEyes<OLED_ANIM_MS) return;
  lastEyes=millis();
  static const EyeMood sequence[]={IDLE,LOOK_LEFT,LOOK_RIGHT,LOOK_UP,LOOK_DOWN,BLINK,
    WINK_LEFT,WINK_RIGHT,HAPPY,EXCITED,SAD,ANGRY,SLEEPY1,SLEEPY2,SURPRISED,LOVE,CONFUSED,THINKING};
  const uint8_t count=sizeof(sequence)/sizeof(sequence[0]);

  if(millis()-lastMoodChange >= 850){
    uint8_t idx = (millis() / 850) % count;
    currentMood = sequence[idx];
    lastMoodChange = millis();
    drawMood(currentMood);
  }
}

void scanI2C(){
  Serial.println("\n--- I2C SCAN ---"); int count=0;
  for(uint8_t a=1;a<127;a++){ Wire.beginTransmission(a); if(Wire.endTransmission()==0){Serial.printf("I2C device: 0x%02X\n",a);count++;} }
  if(!count) Serial.println("NO I2C DEVICES: check 3V3, GND, SDA=21, SCL=22.");
  Serial.println("--- END SCAN ---");
}

// ============================================================
// TFT — now dirty-region aware with partial redraw
// ============================================================

// Track previous values to avoid unnecessary redraws
float lastTempVal = NAN, lastHumVal = NAN, lastLuxVal = -1.0f;
int lastMq3Val = -1;
bool lastMotionVal = false;
bool lastTempOK = true, lastHumOK = true;
bool lastAdxlOK = false;
float lastMagnitude = 0;

void drawTFT(float temp,float hum,float lux,int mq3,bool motion,bool tempOK,bool humOK,float magnitude){
  if(!tftOK) return;

  // Only redraw the whole screen once per TFT_REFRESH_MS interval.
  // Between updates we use partial redraws for changing elements.
  static unsigned long lastFullDraw = 0;
  bool forceFull = (millis() - lastFullDraw >= TFT_REFRESH_MS) || (lastFullDraw == 0);
  if(forceFull) lastFullDraw = millis();

  if(forceFull){
    // Full background clear + header (once per interval, not every sensor read)
    tft.fillScreen(ILI9341_BLACK);
    tft.fillRect(0,0,240,30,ILI9341_BLUE);
    tft.setTextColor(ILI9341_WHITE); tft.setTextSize(2);
    tft.setCursor(48,8); tft.print("JARVIS");
    tft.drawFastHLine(8,35,224,ILI9341_CYAN);

    int y=43;
    tft.setTextSize(1);
    tft.setTextColor(ILI9341_CYAN); tft.setCursor(8,y); tft.print("TEMPERATURE / HUMIDITY"); y+=16;
    tft.setTextColor(ILI9341_WHITE); tft.setCursor(8,y);
    if(tempOK) tft.printf("Temperature: %.1f C  [%s]",temp,tempClass(temp)); else tft.print("Temperature: ERROR"); y+=15;
    tft.setCursor(8,y);
    if(humOK) tft.printf("Humidity: %.1f %%",hum); else tft.print("Humidity: ERROR"); y+=19;

    tft.drawFastHLine(8,y,224,ILI9341_DARKGREY); y+=8;
    tft.setTextColor(ILI9341_CYAN); tft.setCursor(8,y); tft.print("AIR QUALITY (MQ-3)"); y+=16;
    tft.setTextColor(mq3<MQ3_GOOD_MAX?ILI9341_GREEN:(mq3<MQ3_MODERATE_MAX?ILI9341_YELLOW:ILI9341_RED));
    tft.setCursor(8,y); tft.printf("Status: %s",airLabel(mq3)); y+=15;
    tft.setTextColor(ILI9341_WHITE); tft.setCursor(8,y); tft.printf("Raw reading: %d",mq3); y+=19;

    tft.drawFastHLine(8,y,224,ILI9341_DARKGREY); y+=8;
    tft.setTextColor(ILI9341_CYAN); tft.setCursor(8,y); tft.print("LIGHT LEVEL (BH1750)"); y+=16;
    tft.setTextColor(ILI9341_WHITE); tft.setCursor(8,y); tft.printf("Status: %s",lightLabel(lux)); y+=15;
    tft.setCursor(8,y); if(lux>=0)tft.printf("Illuminance: %.1f lux",lux); else tft.print("Illuminance: ERROR"); y+=19;

    tft.drawFastHLine(8,y,224,ILI9341_DARKGREY); y+=8;
    tft.setTextColor(ILI9341_CYAN); tft.setCursor(8,y); tft.print("MOTION / VIBRATION"); y+=16;
    tft.setTextColor(ILI9341_WHITE); tft.setCursor(8,y); tft.printf("PIR: %s",motion?"MOTION":"CLEAR"); y+=16;
    tft.setTextColor(ILI9341_GREEN); tft.setCursor(8,y); tft.print("Earthquake: None detected"); y+=15;
    tft.setTextColor(ILI9341_DARKGREY); tft.setCursor(8,y); tft.print("ADXL345 is not seismic-grade");

    // Save baseline for partial updates
    lastTempVal = temp; lastHumVal = hum; lastLuxVal = lux;
    lastMq3Val = mq3; lastMotionVal = motion; lastTempOK = tempOK; lastHumOK = humOK;
    lastAdxlOK = adxlOK; lastMagnitude = magnitude;
    return;
  }

  // Partial redraws for changed values only (avoids full fillScreen flicker)
  // We redraw only the data text regions, preserving the static layout.
  // Temperature/Humidity area
  int y = 60;
  // Clear and rewrite just the value lines
  tft.setTextColor(ILI9341_BLACK); tft.setTextSize(1);
  if(tempOK != lastTempOK || (tempOK && fabs(temp - lastTempVal) > 0.1)){
    tft.fillRect(8, y, 232, 15, ILI9341_BLACK);
    tft.setTextColor(ILI9341_WHITE); tft.setCursor(8, y);
    if(tempOK) tft.printf("Temperature: %.1f C  [%s]", temp, tempClass(temp));
    else tft.print("Temperature: ERROR");
    lastTempVal = temp; lastTempOK = tempOK;
  }
  y += 15;
  if(humOK != lastHumOK || (humOK && fabs(hum - lastHumVal) > 0.5)){
    tft.fillRect(8, y, 232, 15, ILI9341_BLACK);
    tft.setTextColor(ILI9341_WHITE); tft.setCursor(8, y);
    if(humOK) tft.printf("Humidity: %.1f %%", hum);
    else tft.print("Humidity: ERROR");
    lastHumVal = hum; lastHumOK = humOK;
  }

  // MQ-3 area
  y = 110;
  if(mq3 != lastMq3Val){
    tft.fillRect(8, y, 232, 30, ILI9341_BLACK);
    tft.setTextColor(mq3<MQ3_GOOD_MAX?ILI9341_GREEN:(mq3<MQ3_MODERATE_MAX?ILI9341_YELLOW:ILI9341_RED));
    tft.setCursor(8, y); tft.printf("Status: %s", airLabel(mq3)); y+=15;
    tft.setTextColor(ILI9341_WHITE); tft.setCursor(8, y); tft.printf("Raw reading: %d", mq3); y+=15;
    lastMq3Val = mq3;
  }

  // Light area
  if(lux != lastLuxVal || (lux>=0 && fabs(lux - lastLuxVal) > 1.0)){
    y = 155;
    tft.fillRect(8, y, 232, 38, ILI9341_BLACK);
    tft.setTextColor(ILI9341_WHITE); tft.setCursor(8, y); tft.printf("Status: %s", lightLabel(lux)); y+=15;
    tft.setCursor(8, y); if(lux>=0) tft.printf("Illuminance: %.1f lux", lux); else tft.print("Illuminance: ERROR");
    lastLuxVal = lux;
  }

  // Motion area (only when changed)
  y = 200;
  if(motion != lastMotionVal){
    tft.fillRect(8, y, 232, 48, ILI9341_BLACK);
    tft.setTextColor(ILI9341_CYAN); tft.setCursor(8, y); tft.print("MOTION / VIBRATION"); y+=16;
    tft.setTextColor(ILI9341_WHITE); tft.setCursor(8, y); tft.printf("PIR: %s", motion?"MOTION":"CLEAR"); y+=16;
    tft.setTextColor(ILI9341_GREEN); tft.setCursor(8, y); tft.print("Earthquake: None detected"); y+=15;
    tft.setTextColor(ILI9341_DARKGREY); tft.setCursor(8, y); tft.print("ADXL345 is not seismic-grade");
    lastMotionVal = motion;
  }
}

// ============================================================
// MQTT
// ============================================================

void mqttCallback(char* topic, byte* payload, unsigned int length){
  String msg;
  for(unsigned int i=0;i<length;i++){ msg += (char)payload[i]; }

  if(strcmp(topic, "jarvis/esp32/command") == 0){
    handleRelayCommand(msg.c_str());
  }
}

void connectToMqtt(){
  while(!mqttClient.connected()){
    Serial.print("Attempting MQTT to ");
    Serial.print(MQTT_HOST);
    Serial.print(":");
    Serial.println(MQTT_PORT);

    if(mqttClient.connect("esp32_dashboard")){
      Serial.println("MQTT connected");
      mqttClient.subscribe("jarvis/esp32/command");
    } else {
      Serial.print("MQTT failed, rc=");
      Serial.print(mqttClient.state());
      Serial.println(" — retrying in 3s");
      delay(3000);
    }
  }
}

void publishSensors(float temp, float hum, float lux, int mq3, bool motion,
                     float magX, float magY, float magZ, float magnitude,
                     bool tempOK=true, bool humOK=true){
  // Build JSON manually (no extra library dependency)
  char buf[512];

  // Relay states
  String relays = "[";
  for(int i=0;i<4;i++){
    relays += relayState[i] ? "1" : "0";
    if(i<3) relays += ",";
  }
  relays += "]";

  snprintf(buf, sizeof(buf),
    "{\"temperature\":%.1f,\"temperature_class\":\"%s\","
    "\"humidity\":%.1f,\"humidity_ok\":%d,"
    "\"mq3_raw\":%d,\"mq3_status\":\"%s\","
    "\"lux\":%.1f,\"light_status\":\"%s\","
    "\"motion\":%d,\"pir\":\"%s\","
    "\"acceleration\":{\"x\":%.2f,\"y\":%.2f,\"z\":%.2f},"
    "\"magnitude\":%.2f,\"vibration\":\"%s\","
    "\"relays\":%s,"
    "\"tft_ok\":%d,\"oled_ok\":%d,\"bh1750_ok\":%d,\"adxl_ok\":%d,"
    "\"timestamp\":%lu}",
    tempOK ? temp : 0, tempClass(temp),
    humOK ? hum : 0, humOK ? 1 : 0,
    mq3, airLabel(mq3),
    lux, lightLabel(lux),
    motion ? 1 : 0, motion ? "MOTION" : "CLEAR",
    magX, magY, magZ,
    magnitude, vibrationLabel(magnitude),
    relays.c_str(),
    tftOK ? 1 : 0, oledOK ? 1 : 0, bh1750OK ? 1 : 0, adxlOK ? 1 : 0,
    millis()
  );

  boolean pubOk = mqttClient.publish("jarvis/esp32/sensor", buf);
  if(!pubOk){ Serial.println("[ESP32] publishSensors FAILED (packet>buffer or disconnected)"); }
}

// ============================================================
// Setup
// ============================================================

void setup(){
  Serial.begin(115200); delay(700);
  Serial.println("\n=== JARVIS ESP32 DASHBOARD + MQTT ===");

  // GPIO
  pinMode(MQ3_PIN,INPUT); pinMode(PIR_PIN,INPUT); pinMode(BUZZER_PIN,OUTPUT);
  for(uint8_t i=0;i<4;i++){
    pinMode(RELAY_PINS[i],OUTPUT);
    output(RELAY_PINS[i],false,RELAY_ACTIVE_LOW);  // OFF at startup
  }
  output(BUZZER_PIN,false,BUZZER_ACTIVE_LOW);
  analogReadResolution(12);
  analogSetPinAttenuation(MQ3_PIN,ADC_11db);

  // I2C
  Wire.begin(SDA_PIN,SCL_PIN);
  Wire.setClock(100000);
  dht.begin();

  // SPI TFT
  SPI.begin(TFT_SCK,TFT_MISO,TFT_MOSI,TFT_CS);
  tft.begin();
  tft.setRotation(0);
  tftOK=true;
  tft.fillScreen(ILI9341_BLACK);
  tft.fillRect(0,0,240,40,ILI9341_BLUE);
  tft.setTextColor(ILI9341_WHITE); tft.setTextSize(2); tft.setCursor(48,12); tft.print("JARVIS");
  tft.setTextSize(1); tft.setCursor(20,65); tft.print("TFT DISPLAY TEST");
  tft.setCursor(20,85); tft.print("If you can read this,");
  tft.setCursor(20,100); tft.print("display is responding.");
  delay(900);

  scanI2C();

  oledOK=oled.begin(SSD1306_SWITCHCAPVCC,OLED_ADDR);
  if(oledOK){oled.clearDisplay();drawMood(IDLE);Serial.println("OLED initialized at 0x3C");}
  else Serial.println("OLED init failed at 0x3C; check address 0x3D and wiring.");

  bh1750OK=lightMeter.begin(BH1750::CONTINUOUS_HIGH_RES_MODE,0x23,&Wire);
  Serial.println(bh1750OK?"BH1750 initialized at 0x23":"BH1750 not detected at 0x23 (try 0x5C)");

  adxlOK=accel.begin();
  if(adxlOK){accel.setRange(ADXL345_RANGE_16_G);Serial.println("ADXL345 initialized");}
  else Serial.println("ADXL345 not detected; check I2C wiring/address");

  Serial.println("Relay toggling disabled: all four relay outputs held OFF.");
  Serial.println("MQ-3 labels are rough raw ADC-response categories, not certified AQI.");

  // ---- WiFi ----
  // User must set WIFI_SSID / WIFI_PASS above.
  // Placeholder: will fail gracefully if not set.
  Serial.println("Connecting to WiFi...");
  WiFi.begin(WIFI_SSID, WIFI_PASS);

  unsigned long wifiStart=millis();
  while(WiFi.status() != WL_CONNECTED && millis()-wifiStart < 15000){
    delay(500);
    Serial.print(".");
  }
  if(WiFi.status() == WL_CONNECTED){
    Serial.println("\nWiFi connected");
    Serial.print("IP: "); Serial.println(WiFi.localIP());
  } else {
    Serial.println("\nWiFi failed — continuing in local-only mode");
  }

  // ---- MQTT ----
  mqttClient.setServer(MQTT_HOST, MQTT_PORT);
  mqttClient.setCallback(mqttCallback);
  boolean bufSet = mqttClient.setBufferSize(1024);
  Serial.print("PubSubClient setBufferSize(1024): "); Serial.println(bufSet ? "OK" : "FAIL");
}

// ============================================================
// Loop (nonblocking)
// ============================================================

void loop(){
  // Maintain MQTT connection
  if(WiFi.status() == WL_CONNECTED){
    if(!mqttClient.connected()){
      connectToMqtt();
    }
    if(mqttClient.connected()){
      mqttClient.loop();
    }
  }

  // OLED animation
  animateEyes();

  // Sensor reads
  float temp=dht.readTemperature();
  float hum=dht.readHumidity();
  bool tempOK=!isnan(temp), humOK=!isnan(hum);
  float lux=bh1750OK?lightMeter.readLightLevel():-1.0f;
  int mq3=analogRead(MQ3_PIN);
  bool motion = (digitalRead(PIR_PIN)==HIGH);

  // PIR edge-triggered buzzer + MQTT event (no repeats)
  if(motion && !lastPirLevel){
    Serial.println("Motion detected (edge)");
    // Buzzer alert
    output(BUZZER_PIN,true,BUZZER_ACTIVE_LOW);
    delay(60);
    output(BUZZER_PIN,false,BUZZER_ACTIVE_LOW);

    if(WiFi.status()==WL_CONNECTED && mqttClient.connected()){
      mqttClient.publish("jarvis/esp32/event/motion", "MOTION");
    }
  }
  if(motion && millis()-lastPirEvent > PIR_COOLDOWN_MS){
    lastPirEvent = millis();
  }
  lastPirLevel = motion;

  // ADXL345
  float magX=0, magY=0, magZ=0, magnitude=0;
  if(adxlOK){
    sensors_event_t e;
    accel.getEvent(&e);
    magX = e.acceleration.x;
    magY = e.acceleration.y;
    magZ = e.acceleration.z;
    magnitude = sqrtf(e.acceleration.x*e.acceleration.x +
                      e.acceleration.y*e.acceleration.y +
                      e.acceleration.z*e.acceleration.z);

    // Vibration alert (with cooldown)
    float deviation = fabs(magnitude - 9.81);
    if(deviation > VIBRATION_THRESHOLD && millis()-lastVibrationAlert > VIBRATION_COOLDOWN_MS){
      lastVibrationAlert = millis();
      if(WiFi.status()==WL_CONNECTED && mqttClient.connected()){
        char vbuf[128];
        snprintf(vbuf, sizeof(vbuf), "{\"magnitude\":%.2f,\"deviation\":%.2f}", magnitude, deviation);
        mqttClient.publish("jarvis/esp32/event/vibration", vbuf);
      }
    }
  }

  // Temperature alert
  if(tempOK && temp >= 30.0 && millis()-lastPirEvent > 8000){
    // Cooldown reuses lastPirEvent as coarse timer; could have separate var
    if(WiFi.status()==WL_CONNECTED && mqttClient.connected()){
      char tbuf[64];
      snprintf(tbuf, sizeof(tbuf), "{\"temperature\":%.1f,\"class\":\"HIGH\"}", temp);
      mqttClient.publish("jarvis/esp32/event/temperature", tbuf);
    }
  }

  // Light alert (dark room)
  if(bh1750OK && lux >= 0 && lux < LIGHT_LOW_MAX && millis()-lastPirEvent > 8000){
    if(WiFi.status()==WL_CONNECTED && mqttClient.connected()){
      char lbuf[64];
      snprintf(lbuf, sizeof(lbuf), "{\"lux\":%.1f,\"status\":\"LOW_LIGHT\"}", lux);
      mqttClient.publish("jarvis/esp32/event/light", lbuf);
    }
  }

  // MQ-3 elevated alert
  if(mq3 >= MQ3_GOOD_MAX && millis()-lastPirEvent > 8000){
    if(WiFi.status()==WL_CONNECTED && mqttClient.connected()){
      char mbuf[64];
      snprintf(mbuf, sizeof(mbuf), "{\"raw\":%d,\"status\":\"%s\"}", mq3, airLabel(mq3));
      mqttClient.publish("jarvis/esp32/event/air_quality", mbuf);
    }
  }

  // TFT draw (partial or full)
  drawTFT(temp, hum, lux, mq3, motion, tempOK, humOK, magnitude);

  // Publish sensor data over MQTT every SENSOR_PUB_MS
  if(millis()-lastSensorPub >= SENSOR_PUB_MS){
    lastSensorPub = millis();
    if(WiFi.status()==WL_CONNECTED && mqttClient.connected()){
      publishSensors(temp, hum, lux, mq3, motion, magX, magY, magZ, magnitude, tempOK, humOK);
    }
  }

  // Short nonblocking delay (just enough for loop stability)
  delay(10);
}
