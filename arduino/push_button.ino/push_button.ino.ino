#define BUTTON_PIN 2

void buttonPushedInterrupt() {
  Serial.println("Pushed");
}

void setup() {
	Serial.begin(115200); 
	Serial.setTimeout(1); // Do we need this?
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(BUTTON_PIN),
                  buttonPushedInterrupt,
                  FALLING);
}
void loop() {
  // Nothing to do
}