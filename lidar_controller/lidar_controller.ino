#include <LIDARLite.h>

typedef enum
{
  Stopped = 0,
  Running
} State;

State state = Stopped;
String input;
LIDARLite lidar;

void setup()
{
  Serial.begin(115200);
  input.reserve(128);

  return;
}

void handleCommand(String & cmd)
{
  if(state == Stopped && cmd == "start")
  {
    lidar.begin(0, true);
    lidar.configure(0);

    state = Running;
  }
  else if(state == Running && cmd == "stop")
  {
    lidar.reset();

    state = Stopped;
  }
  
  return;
}

void readInput(void)
{
  while(Serial.available())
  {
    input += (char)Serial.read();

    if(input.endsWith("\n"))
    {
      input.trim();
      handleCommand(input);
      input = "";
    }
  }
  
  return;
}

void loop()
{
  int dist;
  unsigned long timestamp;

  readInput();

  if(state == Running)
  {
    dist = lidar.distance();
    timestamp = millis();
    
    Serial.print(timestamp);
    Serial.print(",");
    Serial.println(dist);
  }

  return;
}

