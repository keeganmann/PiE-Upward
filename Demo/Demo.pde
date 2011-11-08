void setup() {
  Serial.begin(9600); 
}

void loop() {
  for(int i = 0; i < 4; i++){
    Serial.print(analogRead(i));
    //Serial.print(millis()%1024);
    Serial.print(" ");
  }
  Serial.println();
  delay(10);                     
}
