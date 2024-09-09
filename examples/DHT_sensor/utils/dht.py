import time
import sys
import RPi.GPIO as GPIO


class ErrorCode:
    SUCCESS = 0
    DATA_MISSING = 1
    CRC_ERROR = 2
    NOT_FOUND = 3
    INVALID_INPUT = 4

class Result:
    
    err_code = ErrorCode.SUCCESS
    temperature = -1
    humidity = -1     

    def __init__(self, err_code, temperature, humidity):
        self.err_code = err_code
        self.temperature = temperature
        self.humidity = humidity
                                
    def is_valid(self):
        return self.err_code == ErrorCode.SUCCESS
        
class DHT_SENSOR:
    
    __pin = 0
    __isDht11 = True
    __Dht_model = "sensor"

    def __init__(self, pin, dht_model):
        self.__pin = pin
        self.__Dht_model = dht_model

    def read(self):
       
        sensor = self.__Dht_model
        if sensor not in ("11", "22"):
            print('Sensor "{}" is not valid. Use 11, 22 '.format(sensor))
            return Result(ErrorCode.INVALID_INPUT, 0, 0)
        self.__isDht11 = sensor == "11"
        
        pin = int(self.__pin)
        if (pin < 2 or pin > 27):
            print('Gpio {} is not valid'.format(pin))
            return Result(ErrorCode.INVALID_INPUT, 0, 0)

        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)

        MAX_ATTEMPTS = 15
        MAX_NOT_FOUND_ATTEMPTS = 3
        result = self.get()
        not_found_attempts = 0

        for x in range(0, MAX_ATTEMPTS):
            if result.is_valid() or not_found_attempts == MAX_NOT_FOUND_ATTEMPTS:
                break
            else:
                time.sleep(2)
                result = self.get()
                if result.err_code == ErrorCode.NOT_FOUND:
                    not_found_attempts += 1
                else:
                    not_found_attempts = 0
            
        GPIO.cleanup()
        return result

    def get(self):

        GPIO.setup(self.__pin, GPIO.OUT)

        self.__set_wait(GPIO.HIGH, 0.05)

        self.__set_wait(GPIO.LOW, 0.02)

        GPIO.setup(self.__pin, GPIO.IN, GPIO.PUD_UP)

        data = self.__get_data()

        pullup_length = self.__parse_data(data)
        
        if len(pullup_length) == 0:
            return Result(ErrorCode.NOT_FOUND, 0, 0)

        if len(pullup_length) != 40:
            return Result(ErrorCode.DATA_MISSING, 0, 0)

        bits = self.__get_bits(pullup_length)

        the_bytes = self.__bits_to_bytes(bits)

        checksum = the_bytes[0] + the_bytes[1] + the_bytes[2] + the_bytes[3] & 255

        if the_bytes[4] != checksum:
            return Result(ErrorCode.CRC_ERROR, 0, 0)

        temperature = -1
        humidity = -1
        if(self.__isDht11):
            temperature = the_bytes[2] + float(the_bytes[3]) / 10
            humidity = the_bytes[0] + float(the_bytes[1]) / 10
        else:
            temperature = (the_bytes[2] * 256 + float(the_bytes[3])) / 10
            humidity = (the_bytes[0] * 256 + float(the_bytes[1])) / 10
            c = (float)(((the_bytes[2]&0x7F)<< 8)+the_bytes[3])/10
            
            if ( c > 125 ):
                c = the_bytes[2]
                
            if (the_bytes[2] & 0x80):
                c = -c;
            
            temperature = c
            humidity = ((the_bytes[0]<<8)+the_bytes[1])/10.00

        return Result(ErrorCode.SUCCESS, temperature, humidity)
                                                          

    def __set_wait(self, output, sleep):
        GPIO.output(self.__pin, output)
        time.sleep(sleep)

    def __get_data(self):

        unchanged_count = 0

        max_unchanged_count = 100

        last = -1
        data = []
        while True:
            current = GPIO.input(self.__pin)
            data.append(current)
            if last != current:
                unchanged_count = 0
                last = current
            else:
                unchanged_count += 1
                if unchanged_count > max_unchanged_count:
                    break

        return data

    def __parse_data(self, data):
        STATE_INIT_PULL_DOWN = 1
        STATE_INIT_PULL_UP = 2
        STATE_DATA_FIRST_PULL_DOWN = 3
        STATE_DATA_PULL_UP = 4
        STATE_DATA_PULL_DOWN = 5

        state = STATE_INIT_PULL_DOWN

        lengths = [] 
        current_length = 0 

        for i in range(len(data)):

            current = data[i]
            current_length += 1

            if state == STATE_INIT_PULL_DOWN:
                if current == GPIO.LOW:
                    state = STATE_INIT_PULL_UP
                    continue
                else:
                    continue
            if state == STATE_INIT_PULL_UP:
                if current == GPIO.HIGH:
                    state = STATE_DATA_FIRST_PULL_DOWN
                    continue
                else:
                    continue
            if state == STATE_DATA_FIRST_PULL_DOWN:
                if current == GPIO.LOW:
                    state = STATE_DATA_PULL_UP
                    continue
                else:
                    continue
            if state == STATE_DATA_PULL_UP:
                if current == GPIO.HIGH:
                    current_length = 0
                    state = STATE_DATA_PULL_DOWN
                    continue
                else:
                    continue
            if state == STATE_DATA_PULL_DOWN:
                if current == GPIO.LOW:
                    lengths.append(current_length)
                    state = STATE_DATA_PULL_UP
                    continue
                else:
                    continue

        return lengths

    def __get_bits(self, pullup_length):
        shortest_pull_up = 1000
        longest_pull_up = 0

        for i in range(0, len(pullup_length)):
            length = pullup_length[i]
            if length < shortest_pull_up:
                shortest_pull_up = length
            if length > longest_pull_up:
                longest_pull_up = length

        halfway = shortest_pull_up + (longest_pull_up - shortest_pull_up) / 2
        bits = []

        for i in range(0, len(pullup_length)):
            bit = False
            if pullup_length[i] > halfway:
                bit = True
            bits.append(bit)

        return bits

    def __bits_to_bytes(self, bits):
        the_bytes = []
        byte = 0

        for i in range(0, len(bits)):
            byte = byte << 1
            if (bits[i]):
                byte = byte | 1
            else:
                byte = byte | 0
            if ((i + 1) % 8 == 0):
                the_bytes.append(byte)
                byte = 0

        return the_bytes