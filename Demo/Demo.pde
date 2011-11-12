void setup() {
  Serial.begin(9600); 
  pinMode(13, OUTPUT);
}

long pmillis = 0;

void loop() {
  digitalWrite(13, HIGH);   // set the LED on
  delay(20);              // wait for a second
  digitalWrite(13, LOW);    // set the LED off
  
  for(int i = 0; i < 4; i++){
    Serial.print(analogRead(i));
    //Serial.print(millis()%1024);
    Serial.print(" ");
  }
  Serial.println();  

  while( millis() < pmillis ){
  }
  pmillis = millis() + 50;
}
