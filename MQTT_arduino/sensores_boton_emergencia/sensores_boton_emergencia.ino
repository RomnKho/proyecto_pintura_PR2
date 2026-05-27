/*
 *  Se configura la wifi y el mqtt y se asegura su conexión
 *  Callback es una función que recibe el mensaje y determina que hacer con el 
 *  Se crea una tarea para que lea activamente el botón y publicaro en el broker necesario
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <NewPing.h>

/* ULTRASOUND SENSOR */
static const gpio_num_t TRIGGER_PIN = GPIO_NUM_45;
static const gpio_num_t ECHO_PIN = GPIO_NUM_48;
static const uint16_t MAX_DISTANCE = 35;

NewPing sonar(TRIGGER_PIN, ECHO_PIN, MAX_DISTANCE);


/* RGB LED */
static const gpio_num_t rgb_pinout[] = { GPIO_NUM_8, GPIO_NUM_18, GPIO_NUM_17 };
static const uint8_t SZ_RGB_ARRAY = sizeof(rgb_pinout) / sizeof(rgb_pinout[0]);
static const uint32_t FREQ = 1000;
static const uint8_t RESOLUTION = 8;
static const uint8_t CHANNELS[] = { 0, 1, 2 };

static uint8_t rgb_values[SZ_RGB_ARRAY];

/* BUTTON */
static const gpio_num_t button_pin = GPIO_NUM_4;

/* LEDS */
static const gpio_num_t LED_EXT = GPIO_NUM_21;  // Línea de Exterior
static const gpio_num_t LED_INT = GPIO_NUM_20;  // Línea de Interior

/* CONFIG WIFI */
static const char *ssid = "POCO_X8_PRO";
static const char *password = "chacho_guagua";

/* CONFIG MQTT BROKER */
static const char *mqtt_broker = "broker.emqx.io";
static const char *mqtt_username = "emqx";
static const char *mqtt_password = "public";
static const int mqtt_port = 1883;
static String client_id;

/* TOPICS */
static const char *topic_button = "emqx/ESP32_R/arduino/button";
static const char *topic_led = "emqx/ESP32_R/roboDK/led";
static const char *topic_palet = "emqx/ESP32_R/pub/avisos/palet_per";
static const char *topic_sensor = "emqx/ESP32_A/arduino/PID";

static WiFiClient espClient;
static PubSubClient client(espClient);

/* BUTTON TASK */
static const uint16_t BUTTON_TASK_DELAY = 50;
static const uint8_t BUTTON_TASK_PRIORITY = 3;
static const uint16_t BUTTON_TASK_STACK_SZ = 4096;
static TaskHandle_t button_task_handle = NULL;

/* ULTRASOUND SENSOR TASK */
static const uint16_t SENSOR_TASK_DELAY = 100;
static const uint8_t SENSOR_TASK_PRIORITY = 4;
static const uint16_t SENSOR_TASK_STACK_SZ = 4096;
static TaskHandle_t sensor_task_handle = NULL;


/* PID */
static int16_t distancia_cm = 0;
static int32_t current_time = 0;
static int32_t previous_time = 0;
static int32_t elapsed_time = 0;
static int32_t error = 0;
static int32_t last_error = 0;
static int32_t cum_error = 0;
static int32_t rate_error = 0;

static const uint16_t setpoint = 12;  // cm

/* FUNCTIONS */
void callback(char *topic, byte *payload, unsigned int length);
void button_task(void *pvParameters);
void sensor_task(void *pvParameters);

void setup() {
  Serial.begin(115200);
  delay(2000);
  // WiFi config
  WiFi.begin(ssid, password);
  Serial.printf("\nConnecting to Wifi");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.printf(".");
  }

  Serial.printf("\nConnected to WiFi!\n");

  // MQTT broker config
  client.setServer(mqtt_broker, mqtt_port);
  client.setCallback(callback);

  while (!client.connected()) {
    client_id = "esp32-client-";
    client_id += String(WiFi.macAddress());

    Serial.printf("The client %s is connecting to the public MQTT broker\n", client_id.c_str());

    if (client.connect(client_id.c_str(), mqtt_username, mqtt_password)) {
      Serial.println("Public EMQX MQTT broker connected");
    } else {
      Serial.print("Failed with state ");
      Serial.print(client.state());
      Serial.println();
      delay(2000);
    }
  }

  /* Config el la led rgb de emergencia */
  for (int i = 0; i < SZ_RGB_ARRAY; i++) {
    ledcAttachChannel(rgb_pinout[i], FREQ, RESOLUTION, CHANNELS[i]);
  }

  ledcWrite(rgb_pinout[0], 0);  // Empieza rojo

  /* Config el boton de emergencia */
  pinMode(button_pin, INPUT_PULLUP);

  /* Config las led de cada linea y paletizado */
  pinMode(LED_EXT, OUTPUT);
  pinMode(LED_INT, OUTPUT);
  digitalWrite(LED_EXT, LOW);
  digitalWrite(LED_INT, LOW);

  Serial.begin(115200);
  delay(1000);

  delay(500);

  client.publish("emqx/ESP32_R/pub", "Hi, I'm Roman's ESP32");
  client.subscribe(topic_led);
  client.subscribe(topic_palet);

  xTaskCreate(
    button_task,
    "button_task",
    BUTTON_TASK_STACK_SZ,
    NULL,
    BUTTON_TASK_PRIORITY,
    &button_task_handle);

  xTaskCreate(
    sensor_task,
    "sensor_task",
    SENSOR_TASK_STACK_SZ,
    NULL,
    SENSOR_TASK_PRIORITY,
    &sensor_task_handle);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
}

void callback(char *topic, byte *payload, unsigned int length) {
  JsonDocument doc_deserialize_button;
  JsonDocument doc_deserialize_palet;

  Serial.print("Message arrived in topic: ");
  Serial.println(topic);

  if (strcmp(topic, topic_palet) == 0) {
    deserializeJson(doc_deserialize_palet, payload, length);
    const char *linea = doc_deserialize_palet["linea"];
    uint8_t estado = doc_deserialize_palet["estado"];

    if (strcmp(linea, "int") == 0) {
      digitalWrite(LED_INT, estado);
    } else {
      digitalWrite(LED_EXT, estado);
    }
  } else {
    deserializeJson(doc_deserialize_button, payload, length);
    const char *actuador = doc_deserialize_button["actuador"];
    const char *color = doc_deserialize_button["color"];

    Serial.println();
    Serial.println("-----------------------");

    if (strcmp(actuador, "LED") == 0) {
      if (strcmp(color, "GREEN") == 0) {
        ledcWrite(rgb_pinout[0], 255);
        ledcWrite(rgb_pinout[1], 0);  // Verde al maximo
        ledcWrite(rgb_pinout[2], 255);
      }

      if (strcmp(color, "RED") == 0) {
        ledcWrite(rgb_pinout[0], 0);  // Rojo al maximo
        ledcWrite(rgb_pinout[1], 255);
        ledcWrite(rgb_pinout[2], 255);
      }
    }
  }
}

void button_task(void *pvParameters) {
  static bool stop = true;
  char output[256];
  JsonDocument doc_serialize;

  for (;;) {
    if ((digitalRead(button_pin) == LOW) && (stop == true)) {
      doc_serialize["sensor"] = "boton_emergencia";
      doc_serialize["estado"] = "STOP";
      serializeJson(doc_serialize, output);

      client.publish(topic_button, output);
      stop = !stop;

      while (digitalRead(button_pin) == LOW) {
        vTaskDelay(pdMS_TO_TICKS(10));
      }
    }

    if ((digitalRead(button_pin) == LOW) && (stop == false)) {
      doc_serialize["sensor"] = "boton_emergencia";
      doc_serialize["estado"] = "CONTINUE";
      serializeJson(doc_serialize, output);

      client.publish(topic_button, output);
      stop = !stop;

      while (digitalRead(button_pin) == LOW) {
        vTaskDelay(pdMS_TO_TICKS(10));
      }
    }

    vTaskDelay(pdMS_TO_TICKS(BUTTON_TASK_DELAY));
  }
}

void sensor_task(void *pvParameters) {
  static const int8_t Kp = 2;
  static const int8_t Ki = 1;
  static const int8_t Kd = 1;

  static int32_t output = 0;

  char output_msg[256];
  JsonDocument doc_serialize;

  for (;;) {

    distancia_cm = sonar.ping_cm();
    Serial.println(distancia_cm);

    current_time = millis();
    elapsed_time = (uint64_t)(current_time - previous_time);

    error = distancia_cm - setpoint;

    cum_error += error * elapsed_time;
    rate_error = (error - last_error) / elapsed_time;
    last_error = error;

    output = (Kp * error) + (Ki * cum_error) + (Kd * rate_error);
    Serial.println(output);

    doc_serialize["sensor"] = "ultrasonido";
    doc_serialize["PID"] = output;
    serializeJson(doc_serialize, output_msg);
    client.publish(topic_sensor, output_msg);

    last_error = error;
    previous_time = current_time;

    vTaskDelay(pdMS_TO_TICKS(SENSOR_TASK_DELAY));
  }
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Intentando conexión MQTT...");

    // Crear un ID de cliente aleatorio
    String clientId = "ESP32Client-";
    clientId += String(random(0, 0xffff), HEX);

    if (client.connect(client_id.c_str(), mqtt_username, mqtt_password)) {
      Serial.println("conectado");
      client.subscribe(topic_led);
      client.subscribe(topic_palet);
    } else {
      Serial.printf("falló, rc=%d. Reintentando en 2s\n", client.state());
      delay(2000);
    }
  }
}