/*
 *  Se configura la wifi y el mqtt y se asegura su conexión
 *  Callback es una función que recibe el mensaje y determina que hacer con el 
 *  Se crea una tarea para que lea activamente el botón y publicaro en el broker necesario
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

/* RGB LED */
static const gpio_num_t   rgb_pinout[]  = {GPIO_NUM_27, GPIO_NUM_26, GPIO_NUM_32};
static const uint8_t      SZ_RGB_ARRAY  = sizeof(rgb_pinout) / sizeof(rgb_pinout[0]);
static const uint32_t     FREQ          = 1000;
static const uint8_t      RESOLUTION    = 8;
static const uint8_t      CHANNELS[]    = {0, 1, 2};

static uint8_t            rgb_values[SZ_RGB_ARRAY];

/* BUTTON */
static const gpio_num_t   button_pin     = GPIO_NUM_4;

/* LEDS */

static const gpio_num_t LED_PER = GPIO_NUM_5;  // Línea de Personalizados
static const gpio_num_t LED_EXT = GPIO_NUM_18; // Línea de Exterior
static const gpio_num_t LED_INT = GPIO_NUM_19; // Línea de Interior

/* CONFIG WIFI */
static const char *ssid          = "*";
static const char *password      = "*";

/* CONFIG MQTT BROKER */
static const char   *mqtt_broker   = "broker.emqx.io";
static const char   *mqtt_username = "emqx";
static const char   *mqtt_password = "public";
static const int    mqtt_port      = 1883;
static String       client_id;

/* TOPICS */
static const char   *topic_button  = "emqx/ESP32_R/arduino/button";
static const char   *topic_led     = "emqx/ESP32_R/roboDK/led";
static const char   *topic_per     = "emqx/ESP32_R/pub/palet_per";
static const char   *topic_ext     = "emqx/ESP32_R/pub/palet_ext";
static const char   *topic_int     = "emqx/ESP32_R/pub/palet_int";


static WiFiClient espClient;
static PubSubClient client(espClient);

/* TASK */
static const int16_t      BUTTON_TASK_DELAY        = 50;
static const int8_t       BUTTON_TASK_PRIORITY     = 3;
static const int16_t      BUTTON_TASK_STACK_SZ     = 4096;
static TaskHandle_t       button_task_handle       = NULL;

/* FUNCTIONS */
void callback  (char *topic, byte *payload, unsigned int length);
void button_task  (void *pvParameters);

void setup() 
{
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
  for(int i = 0; i < SZ_RGB_ARRAY; i++ )
  {
    ledcAttachChannel(rgb_pinout[i], FREQ, RESOLUTION, CHANNELS[i]);
  }

  ledcWrite(rgb_pinout[0], 0); // Empieza rojo

  /* Config el boton de emergencia */
  pinMode(button_pin, INPUT_PULLUP);

  /* Config las led de cada linea y paletizado */
  pinMode(LED_PER, OUTPUT);
  pinMode(LED_EXT, OUTPUT);
  pinMode(LED_INT, OUTPUT);
  digitalWrite(LED_PER, LOW);
  digitalWrite(LED_EXT, LOW);
  digitalWrite(LED_INT, LOW);

  Serial.begin(115200);
  delay(1000);

  delay(500);

  client.publish("emqx/ESP32_R/pub", "Hi, I'm Roman's ESP32");
  client.subscribe(topic_led);
  client.subscribe(topic_per);
  client.subscribe(topic_ext);
  client.subscribe(topic_int);

  xTaskCreate(
    button_task,
    "button_task",
    BUTTON_TASK_STACK_SZ,
    NULL,
    BUTTON_TASK_PRIORITY,
    &button_task_handle
  );
}

void loop() 
{
  if(!client.connected())
  {
    reconnect();
  }
  client.loop();
}

void callback(char *topic, byte *payload, unsigned int length) 
{
  JsonDocument doc_deserialize;

  Serial.print("Message arrived in topic: ");
  Serial.println(topic);

  if (strcmp(topic, topic_per) == 0) 
  {
    Serial.println("-> ATENCIÓN: Palet PERSONALIZADO al límite de capacidad.");
    digitalWrite(LED_PER, HIGH);
  } 
  else if (strcmp(topic, topic_ext) == 0) 
  {
    Serial.println("-> ATENCIÓN: Palet EXTERNO al límite de capacidad.");
    digitalWrite(LED_EXT, HIGH);
  } 
  else if (strcmp(topic, topic_int) == 0) 
  {
    Serial.println("-> ATENCIÓN: Palet INTERNO al límite de capacidad.");
    digitalWrite(LED_INT, HIGH);
  }
  else 
  {
    deserializeJson(doc_deserialize, payload, length);
    const char *actuador = doc_deserialize["actuador"];
    const char *color = doc_deserialize["color"];

    Serial.println();
    Serial.println("-----------------------");

    if (strcmp(actuador,"LED") == 0)
    {
      if (strcmp(color,"GREEN") == 0)
      {
        ledcWrite(rgb_pinout[0], 255);
        ledcWrite(rgb_pinout[1], 0);    // Verde al maximo
        ledcWrite(rgb_pinout[2], 255);
      }

      if (strcmp(color,"RED") == 0)
      {
        ledcWrite(rgb_pinout[0], 0);    // Rojo al maximo
        ledcWrite(rgb_pinout[1], 255);    
        ledcWrite(rgb_pinout[2], 255);
      }
    }
  }
}

void button_task(void *pvParameters)
{
  static bool stop = true;
  char output[256];
  JsonDocument doc_serialize;

  for(;;)
  {
      if((digitalRead(button_pin) == LOW) && (stop == true))
      {
        doc_serialize["sensor"] = "boton_emergencia";
        doc_serialize["estado"] = "STOP";
        serializeJson(doc_serialize, output);

        client.publish(topic_button, output);
        stop = !stop;

        while(digitalRead(button_pin) == LOW)
        {
          vTaskDelay(pdMS_TO_TICKS(10));
        }
      }

      if((digitalRead(button_pin) == LOW) && (stop == false))
      {
        doc_serialize["sensor"] = "boton_emergencia";
        doc_serialize["estado"] = "CONTINUE";
        serializeJson(doc_serialize, output);

        client.publish(topic_button, output);
        stop = !stop;

        while(digitalRead(button_pin) == LOW)
        {
          vTaskDelay(pdMS_TO_TICKS(10));
        }
      }

      vTaskDelay(pdMS_TO_TICKS(BUTTON_TASK_DELAY));
  }
}

void reconnect() 
{
  while (!client.connected()) 
  {
    Serial.print("Intentando conexión MQTT...");

    // Crear un ID de cliente aleatorio
    String clientId = "ESP32Client-";
    clientId += String(random(0, 0xffff), HEX);

    if (client.connect(client_id.c_str(), mqtt_username, mqtt_password)) 
    {
      Serial.println("conectado");
      client.subscribe(topic_led);
      client.subscribe(topic_per);
      client.subscribe(topic_ext);
      client.subscribe(topic_int); 
    } 
    else 
    {
      Serial.printf("falló, rc=%d. Reintentando en 2s\n", client.state());
      delay(2000);
    }
  }
}