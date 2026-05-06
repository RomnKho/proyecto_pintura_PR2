#include <WiFi.h>
#include <PubSubClient.h>

// --- CONFIGURACIÓN DE PINES (LEDS) ---
// He puesto estos pines por poner algo, porque como aun no se cuales vamos a usar
const int LED_PER = 25; // Línea de Personalizados
const int LED_EXT = 26; // Línea de Exterior
const int LED_INT = 27; // Línea de Interior

// WIFI, sin doxearme las credenciales
const char* ssid = "*";
const char* password = "*";

// Aqui esta todo lo del Broker y MQTT
const char* mqtt_broker = "broker.emqx.io";
const int mqtt_port = 1883;
const char* mqtt_username = "emqx";
const char* mqtt_password = "public";

// Los tres topics de los contadores
const char* topic_per = "emqx/ESP32_R/pub/palet_per";
const char* topic_ext = "emqx/ESP32_R/pub/palet_ext";
const char* topic_int = "emqx/ESP32_R/pub/palet_int";

WiFiClient espClient;
PubSubClient client(espClient);

// Declaración de funciones
void setup_wifi();
void reconnect();
void callback(char* topic, byte* payload, unsigned int length);

void setup() {
  Serial.begin(115200);

  pinMode(LED_PER, OUTPUT);
  pinMode(LED_EXT, OUTPUT);
  pinMode(LED_INT, OUTPUT);
  digitalWrite(LED_PER, LOW);
  digitalWrite(LED_EXT, LOW);
  digitalWrite(LED_INT, LOW);

  setup_wifi();
  client.setServer(mqtt_broker, mqtt_port);
  client.setCallback(callback);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
}

void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Conectando a ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi conectada");
  Serial.println("Dirección IP: ");
  Serial.println(WiFi.localIP());
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Intentando conexión MQTT...");
    
    // Crear un ID de cliente aleatorio
    String clientId = "ESP32Client-AvisoPalets-";
    clientId += String(random(0, 0xffff), HEX);
    
    if (client.connect(clientId.c_str(), mqtt_username, mqtt_password)) {
      Serial.println("conectado");
      
      client.subscribe(topic_per);
      client.subscribe(topic_ext);
      client.subscribe(topic_int);
    } else {
      Serial.print("falló, rc=");
      Serial.print(client.state());
      Serial.println(" intentando de nuevo en 5 segundos");
      delay(5000);
    }
  }
}

// Callback que se ejecutara cada vez que se reciba un mensaje en cualquiera de los topics
void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Aviso recibido en el topic: ");
  Serial.println(topic);

  
  if (strcmp(topic, topic_per) == 0) {
    Serial.println("-> ATENCIÓN: Palet PERSONALIZADO al límite de capacidad.");
    digitalWrite(LED_PER, HIGH);
  } 
  else if (strcmp(topic, topic_ext) == 0) {
    Serial.println("-> ATENCIÓN: Palet EXTERNO al límite de capacidad.");
    digitalWrite(LED_EXT, HIGH);
  } 
  else if (strcmp(topic, topic_int) == 0) {
    Serial.println("-> ATENCIÓN: Palet INTERNO al límite de capacidad.");
    digitalWrite(LED_INT, HIGH);
  }
}