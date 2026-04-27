#include <SPI.h>
#include <RH_RF95.h>

#define RFM95_CS 8
#define RFM95_RST 4
#define RFM95_INT 3
#define RF_FREQUENCY 868.0

RH_RF95 rf95(RFM95_CS, RFM95_INT);

// Les 3 largeurs de canal
int bandwidths[] = {125000, 250000, 500000};
String bw_names[] = {"BW125", "BW250", "BW500"};
int bw_index = 0;

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

  rf95.setTxPower(5, false);
  Serial.println("CARTE A prete");
}

void loop() {
  // Change de BW à chaque envoi
  rf95.setSignalBandwidth(bandwidths[bw_index]);

  String msg = "CARTE_A_" + bw_names[bw_index];
  Serial.println("Envoi : " + msg);

  rf95.send((uint8_t*)msg.c_str(), msg.length());
  rf95.waitPacketSent();
  Serial.println("Envoye OK - " + bw_names[bw_index]);

  // Change de BW pour le prochain envoi
  bw_index = (bw_index + 1) % 3;
  delay(2000);
}
