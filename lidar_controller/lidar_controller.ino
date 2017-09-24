#include <Wire.h>
#include <LIDARLite.h>

LIDARLite lidar;

void setup()
{
  Serial.begin(115200); // Initialize serial connection to display distance readings

  lidar.begin(0, true); // Set configuration to default and I2C to 400 kHz
  lidar.configure(0); // Change this number to try out alternate configurations
}

void loop()
{
  Serial.println(lidar.distance());
}

