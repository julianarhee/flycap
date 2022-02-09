byte serialByte;
//byte pixel_state[1];
//byte acq_trigger_state[1]; 
byte frame_trigger_state[1];
//byte registerD_state[1];
byte timer_bytes[4];

int trigger_pin = 5;

unsigned long start_time;
unsigned long last_refresh = 0;
unsigned long time_stamp = 0;
unsigned long time_stamp_internal = 0;

unsigned long target_interval = 1000;// 1 ms interval between writes
unsigned long this_interval;
unsigned long write_count = 0;

int write_flag = 0;

// the setup routine runs once when you press reset:
void setup() { 
  // port B maps to Arduino pins 8-13
  //DDRB = DDRB | B00000000;// setting pins 8 to 13 as inputs
  // port D maps to Arduino pins 0-7
  //DDRD = DDRD | B00110000; // setting pins 6, 7 as inputs
                            //setting pins 4, 5 as output to camera
                      // NOTE: make sure to leave last 2 bits to 0
                          // these are piins 0 & 1, which are RX & TX. 
                          //changing will lead to problems with serial communication  
  //PORTD = B00000000;//set pin 5 to low
  pinMode(trigger_pin, OUTPUT);
  Serial.begin (115200);  //start serial connection
}

// the loop routine runs over and over again forever:
void loop() {
    while (Serial.available()>0){  
      serialByte=Serial.read();
      if (serialByte=='S'){
        write_flag=1;
        while(write_flag==1){
          //start recording pixel clock status
          start_time = micros();
          //PORTD = B00110000;//set pin 5 to high 
          digitalWrite(trigger_pin, HIGH); 
          //write_flag = 1; //start streaming data from first time you get acquisition trigger
        
          // check for finish trigger
          if (Serial.available()>0){ //Experiment finished - stop recording pixel clock
          serialByte=Serial.read();
          if (serialByte=='F'){
          //PORTD = B00000000;//set pin 5 to low
          digitalWrite(trigger_pin, LOW);
          write_flag = 0;
          //break;
          }
        }
      }
    }
  }
}
