#include <SPI.h>
#include <RH_RF95.h>

#define RFM95_CS 8
#define RFM95_RST 4
#define RFM95_INT 3
#define RF_FREQUENCY 868.0

RH_RF95 rf95(RFM95_CS, RFM95_INT);

void setup() {
  pinMode(RFM95_RST, OUTPUT);
  digitalWrite(RFM95_RST, HIGH);
  Serial.begin(9600);
  delay(100);

  digitalWrite(RFM95_RST, LOW);
  delay(10);
  digitalWrite(RFM95_RST, HIGH);
  delay(10);

  Serial.println("Demarrage CARTE A...");

  if (!rf95.init()) {
    Serial.println("ERREUR init LoRa");
    while (1);
  }
  Serial.println("OK LoRa initialise");

  if (!rf95.setFrequency(RF_FREQUENCY)) {
    Serial.println("ERREUR frequence");
    while (1);
  }

  // ✅ Puissance réduite à 5 dBm
  rf95.setTxPower(5, false);
  Serial.println("OK Puissance TX 5 dBm");
  Serial.println("--- Debut emission ---");
}

void loop() {
  const char *msg = "CARTE_A";
  Serial.print("Envoi : ");
  Serial.println(msg);
  rf95.send((uint8_t *)msg, strlen(msg));
  rf95.waitPacketSent();
  Serial.println("Envoye OK");
  delay(1000);
}
