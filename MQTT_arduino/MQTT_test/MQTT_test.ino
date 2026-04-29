/*
 *  Se configura la wifi y el mqtt y se asegura su conexión
 *  Callback es una función que recibe el mensaje y determina que hacer con el 
 *  Se crea una tarea para que lea activamente el botón y publicaro en el broker necesario
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

/* RGB LED */
static const uint8_t   rgb_pinout[]  = {27, 26, 32};
static const uint8_t   SZ_RGB_ARRAY  = sizeof(rgb_pinout) / sizeof(rgb_pinout[0]);
static const uint32_t  FREQ          = 1000;
static const uint8_t   RESOLUTION    = 8;
static const uint8_t   CHANNELS[]    = {0, 1, 2};

static uint8_t         rgb_values[SZ_RGB_ARRAY];
static const float     rgb_balance[SZ_RGB_ARRAY] = {0.5, 0.9, 1.0};

/* CONFIG WIFI */
static const char *ssid          = "*";
static const char *password      = "*";

/* CONFIG MQTT BROKER */
static const char   *mqtt_broker   = "broker.emqx.io";
static const char   *topic_pub     = "emqx/ESP32_R/pub";
static const char   *topic_sub     = "emqx/ESP32_R/sub";
static const char   *mqtt_username = "emqx";
static const char   *mqtt_password = "public";
static const int    mqtt_port     = 1883;
static String       client_id;

static WiFiClient espClient;
static PubSubClient client(espClient);

/* TASK */
static const int16_t      RGB_TASK_DELAY        = 50;
static const int16_t      RGB_TASK_RGB_ON_TIME  = 2000;
static const int8_t       RGB_TASK_PRIORITY     = 3;
static const int16_t      RGB_TASK_STACK_SZ     = 2048;
static TaskHandle_t       rgb_task_handle       = NULL;

/* QUEUE */
static QueueHandle_t    xCallback_rgb_queue   = NULL;
static const int8_t     CALLBACK_RGB_QUEUE_SZ = 10;

/* DESERIALIZING JSON DOC */
static JsonDocument          doc;
static DeserializationError  error;

static const char            *rgb_str;
static const char            *sz_str;
static char                  sz_ch;
static int8_t                quantity;

/* FUNCTIONS */
void callback  (char *topic, byte *payload, unsigned int length);
void rgb_task  (void *pvParameters);

void setup() 
{

  for(int i = 0; i < SZ_RGB_ARRAY; i++ )
  {
    ledcAttachChannel(rgb_pinout[i], FREQ, RESOLUTION, CHANNELS[i]);
  }

  for(int i = 0; i < SZ_RGB_ARRAY; i++ )
  {
    ledcWrite(rgb_pinout[i], 255);
  }

  Serial.begin(115200);
  delay(1000);

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

  delay(500);
  // "Subscribe" to publisher and suscriptor channels
  client.publish(topic_pub, "Hi, I'm Roman's ESP32");
  client.subscribe(topic_sub);

  xCallback_rgb_queue = xQueueCreate(CALLBACK_RGB_QUEUE_SZ, sizeof(long)); 

  xTaskCreate(
    rgb_task,
    "rgb_task",
    RGB_TASK_STACK_SZ,
    NULL,
    RGB_TASK_PRIORITY,
    &rgb_task_handle
  );
}

void loop() {
  if(!client.connected())
  {
    reconnect();
  }
  client.loop();
}

void callback(char *topic, byte *payload, unsigned int length) 
{

  Serial.print("Message arrived in topic: ");
  Serial.println(topic);
  Serial.print("Message:");

  for (int i = 0; i < length; i++) {
    Serial.print((char)payload[i]);
  }

  Serial.println();
  Serial.println("-----------------------");

  error = deserializeJson(doc, payload, length);

  if(error)
  {
    Serial.print("deseralizedJson() returned ");
    Serial.println(error.c_str());
    return;
  }

  rgb_str = doc["rgb_hex"] | "000000"; 
  sz_str = doc["tamano"] | "N";
  quantity = doc["cantidad"];
  type = doc["tipo"];

  sz_ch = sz_str[0];
  long rgb_hex_send = strtol(rgb_str, NULL, 16);
  xQueueSend(xCallback_rgb_queue, &rgb_hex_send, 0);
  
  Serial.printf("rgb: %06x; sz: %c; Q: %d\n; Type: %s", rgb_hex_send, sz_ch, quantity, type);
  Serial.println("-----------------------");

}

void rgb_task(void *pvParameters)
{
  for(;;)
  {
    long rgb_hex_received;
    xQueueReceive(xCallback_rgb_queue, &rgb_hex_received, portMAX_DELAY); 

    rgb_values[0] = (rgb_hex_received >> 16) & 0xFF;
    rgb_values[1] = (rgb_hex_received >> 8) & 0xFF;
    rgb_values[2] = rgb_hex_received & 0xFF;

    for(int i = 0; i < SZ_RGB_ARRAY; i++)
    {
      ledcWrite(rgb_pinout[i], 255 - (rgb_values[i] * rgb_balance[i])); // rgb de anodo comun => 0 brillo máximo | 255 no brilla
    }

    delay(RGB_TASK_RGB_ON_TIME / portTICK_PERIOD_MS);

    for(int i = 0; i < SZ_RGB_ARRAY; i++ )
    {
      ledcWrite(rgb_pinout[i], 255);
    }

    delay(RGB_TASK_DELAY / portTICK_PERIOD_MS);

  }
}

void reconnect() 
{
  while (!client.connected()) 
  {
    Serial.print("Intentando conexión MQTT...");

    if (client.connect(client_id.c_str(), mqtt_username, mqtt_password)) 
    {
      Serial.println("conectado");
      client.subscribe(topic_sub); 
    } 
    else 
    {
      Serial.printf("falló, rc=%d. Reintentando en 2s\n", client.state());
      delay(2000);
    }
  }
}