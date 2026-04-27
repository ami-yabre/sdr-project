#include <SPI.h>
#include <RH_RF95.h>

#define RFM95_CS 8
#define RFM95_RST 4
#define RFM95_INT 3
#define RF_FREQUENCY 868.5

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

  if (!rf95.init()) {
    Serial.println("ERREUR init LoRa");
    while (1);
  }

  if (!rf95.setFrequency(RF_FREQUENCY)) {
    Serial.println("ERREUR frequence");
    while (1);
  }

  // BW fixe 250 kHz
  rf95.setSignalBandwidth(250000);
  rf95.setTxPower(5, false);
  Serial.println("CARTE B prete - BW 250kHz");
}

void loop() {
  const char *msg = "CARTE_B_BW250";
  Serial.println("Envoi : CARTE_B_BW250");
  rf95.send((uint8_t*)msg, strlen(msg));
  rf95.waitPacketSent();
  Serial.println("Envoye OK");
  delay(1200);
}
