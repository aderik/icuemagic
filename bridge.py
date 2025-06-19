import json
import time
import logging
import threading
from cuesdk import CueSdk, CorsairDeviceFilter, CorsairDeviceType, CorsairLedColor, CorsairSessionState, CorsairError
from flux_led import WifiLedBulb, BulbScanner
from colorutils import Color

# Configureer logging
logger = logging.getLogger('icuemagic')
logger.setLevel(logging.DEBUG)  # Laat de handlers het level bepalen

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)  # Standaard level
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

# File handler
file_handler = logging.FileHandler('icuemagic.log')
file_handler.setLevel(logging.DEBUG)  # Log alles naar bestand
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

def icue_device_wizard(sdk):
    """Wizard for iCUE device selection"""
    print("No valid iCUE device ID found. Scanning for iCUE devices...")
    print("Connecting to iCUE SDK...")
    
    def on_state_changed(evt):
        if evt.state == CorsairSessionState.CSS_Connected:
            print("iCUE SDK is connected!")
        elif evt.state == CorsairSessionState.CSS_Timeout:
            print("iCUE SDK connection timeout, trying again...")
    
    if not sdk.connect(on_state_changed):
        raise RuntimeError("Could not connect to iCUE SDK")
    
    # Wait for SDK to connect
    time.sleep(1)
    
    devices, err = sdk.get_devices(CorsairDeviceFilter(device_type_mask=CorsairDeviceType.CDT_All))
    if not devices:
        raise RuntimeError("No iCUE devices found")
    
    print(f"\nFound iCUE devices:")
    for i, device in enumerate(devices):
        print(f"[{i}] Model: {device.model}")
        print(f"    ID: {device.device_id}")
        print(f"    Type: {device.type}")
    
    # Automatically choose first device
    device = devices[0]
    print(f"\nAutomatically selected: {device.model}")
    return device.device_id

def magichome_ip_wizard():
    """Wizard for Magic Home controller selection"""
    print("No valid Magic Home IP found. Scanning for Magic Home controllers on the network...")
    
    try:
        # Scan for controllers
        scanner = BulbScanner()
        scanner.scan(timeout=5)  # timeout in seconds
        devices = scanner.getBulbInfo()
        
        if not devices:
            raise RuntimeError("No Magic Home controllers found")
        
        print(f"\nFound Magic Home controllers:")
        for i, device in enumerate(devices):
            print(f"[{i}] IP: {device['ipaddr']}")
        
        # If there's only one device, choose it automatically
        if len(devices) == 1:
            print(f"\nAutomatically selected: {devices[0]['ipaddr']}")
            return devices[0]['ipaddr']
            
        # Otherwise let the user choose
        while True:
            choice = input(f"Choose a controller [0-{len(devices)-1}]: ")
            try:
                choice = int(choice)
                if 0 <= choice < len(devices):
                    return devices[choice]['ipaddr']
            except Exception:
                pass
            print("Invalid choice. Try again.")
            
    except Exception as e:
        logger.error(f"Error scanning for Magic Home controllers: {e}")
        raise RuntimeError("No Magic Home controllers found. Make sure your controller is powered on and on the same network.")

class iCueController:
    def __init__(self, device_id, sdk=None):
        self.device_id = device_id
        self.sdk = sdk or CueSdk()  # Gebruik bestaande SDK of maak nieuwe
        self._connected_event = threading.Event()
        self.last_colors = None
        
        # Altijd verbinden, ook met bestaande SDK
        if not self.sdk.connect(lambda e: None):
            raise RuntimeError("Could not connect to iCUE SDK")
        
        # Wacht even tot de SDK verbonden is
        time.sleep(1)
        
        # Zoek het device
        self.device = self._find_device()
        if not self.device:
            raise RuntimeError(f"Device not found: {self.device_id}")
            
        self.led_ids = self._find_all_led_ids()
        logger.info(f"iCUE controller initialized with device: {self.device.model}")

    def _find_device(self):
        devices, err = self.sdk.get_devices(CorsairDeviceFilter(device_type_mask=CorsairDeviceType.CDT_All))
        if devices:
            for device in devices:
                if getattr(device, 'device_id', None) == self.device_id:
                    return device
        return None

    def _find_all_led_ids(self):
        if not self.device:
            return []
        led_positions, err = self.sdk.get_led_positions(self.device.device_id)
        if not led_positions:
            logger.error("No LED positions found")
            return []
        led_ids = [led.id for led in led_positions]
        logger.info(f"All LEDs found: {led_ids}")
        return led_ids

    def get_average_color(self):
        if not self.device or not self.led_ids:
            logger.warning("No device or LEDs found, trying to reconnect...")
            self.reconnect()
            return None

        try:
            led_colors = [CorsairLedColor(led_id, 0, 0, 0, 255) for led_id in self.led_ids]
            led_colors, err = self.sdk.get_led_colors(self.device.device_id, led_colors)
            
            if not led_colors:
                logger.warning("No LED colors received, trying to reconnect...")
                self.reconnect()
                return None

            current_colors = tuple((led.r, led.g, led.b) for led in led_colors)
            if current_colors == self.last_colors:
                return None
            
            self.last_colors = current_colors
            
            total_r = sum(led.r for led in led_colors)
            total_g = sum(led.g for led in led_colors)
            total_b = sum(led.b for led in led_colors)
            count = len(led_colors)
            avg_r = int(total_r / count)
            avg_g = int(total_g / count)
            avg_b = int(total_b / count)
            logger.info(f"New average color: R={avg_r}, G={avg_g}, B={avg_b}")
            return (avg_r, avg_g, avg_b)
        except Exception as e:
            logger.error(f"Error getting LED colors: {e}")
            self.reconnect()
            return None

    def reconnect(self):
        """Probeer opnieuw te verbinden met de SDK"""
        try:
            self.sdk.disconnect()
            time.sleep(2)  # Wacht wat langer voor reconnectie
            if not self.sdk.connect(lambda e: None):
                raise RuntimeError("Could not connect to iCUE SDK")
            time.sleep(1)
            self.device = self._find_device()
            if not self.device:
                raise RuntimeError(f"Device not found: {self.device_id}")
            self.led_ids = self._find_all_led_ids()
            logger.info(f"iCUE controller reconnected with device: {self.device.model}")
        except Exception as e:
            logger.error(f"Error reconnecting to iCUE: {e}")
            raise

class MagicHomeController:
    def __init__(self, ip_address):
        self.ip_address = ip_address
        self.bulb = None
        self.last_color = None
        self.transition_steps = 10  # Number of steps for color transition
        self.transition_delay = 0.02  # Delay between steps in seconds
        
    def connect(self):
        try:
            self.bulb = WifiLedBulb(self.ip_address)
            self.bulb.connect()
            logger.info(f"Magic Home controller connected with {self.ip_address}")
        except Exception as e:
            logger.error(f"Error connecting to Magic Home: {e}")
            self.bulb = None

    def interpolate_color(self, start_color, end_color, progress):
        """Interpolate between two RGB colors"""
        r = int(start_color[0] + (end_color[0] - start_color[0]) * progress)
        g = int(start_color[1] + (end_color[1] - start_color[1]) * progress)
        b = int(start_color[2] + (end_color[2] - start_color[2]) * progress)
        return (r, g, b)

    def set_color(self, color):
        if not self.bulb:
            self.connect()
            if not self.bulb:
                return

        r, g, b = color
        
        # If we have a last color, create a smooth transition
        if self.last_color:
            # Interpolate between colors
            for step in range(1, self.transition_steps + 1):
                # Calculate intermediate color
                progress = step / self.transition_steps
                current_color = self.interpolate_color(self.last_color, (r, g, b), progress)
                
                # Set the intermediate color
                try:
                    self.bulb.setRgb(current_color[0], current_color[1], current_color[2])
                    time.sleep(self.transition_delay)
                except Exception as e:
                    logger.warning(f"Error during color transition: {e}")
                    self.bulb = None
                    return
        else:
            # First color, set it directly
            try:
                self.bulb.setRgb(r, g, b)
            except Exception as e:
                logger.warning(f"Error setting initial color: {e}")
                self.bulb = None
                return
        
        # Store the new color as last color
        self.last_color = (r, g, b)
        logger.info(f"Set new color: R={r}, G={g}, B={b}")

    def turn_off(self):
        """Turn off the LED strip"""
        if not self.bulb:
            self.connect()
            if not self.bulb:
                return

        try:
            # Turn off the LED strip
            self.bulb.turnOff()
            logger.info("LED strip turned off")
        except Exception as e:
            logger.warning(f"Error turning off LED strip: {e}")
            self.bulb = None

def load_config():
    """Load configuration from config.json or use wizard for setup"""
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
            logger.info("Configuration loaded from config.json")
            
            # Configure logging level for all handlers
            log_level = config.get('log_level', 'ERROR').upper()  # Default to ERROR
            level = getattr(logging, log_level)
            logger.setLevel(level)
            for handler in logger.handlers:
                handler.setLevel(level)
            
            return config
    except FileNotFoundError:
        logger.warning("config.json not found, using wizard for setup")
        return run_wizard()

def run_wizard():
    """Wizard for first-time setup"""
    print("Welcome to the iCUE Magic Home Bridge setup wizard!")
    
    # iCUE device selection
    device_id = icue_device_wizard(CueSdk())
    
    # Magic Home controller selection
    magichome_ip = magichome_ip_wizard()
    
    # Save configuration
    config = {
        # The ID of your iCUE device (e.g. keyboard, mouse, etc.)
        'icue_device_id': device_id,
        
        # The IP address of your Magic Home controller
        'magichome_ip': magichome_ip,
        
        # Logging level (ERROR, WARNING, INFO, DEBUG)
        # ERROR: Only show errors
        # WARNING: Show errors and warnings
        # INFO: Show normal information
        # DEBUG: Show detailed debug information
        'log_level': 'ERROR'
    }
    
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=2)
    print("Configuration saved to config.json")
    
    return config

def start_bridge(sdk, config):
    # Initialize controllers
    try:
        print("Initializing controllers...")
        icue = iCueController(config['icue_device_id'], sdk)
        magic_home = MagicHomeController(config['magichome_ip'])
    except Exception as e:
        logger.error(f"Error initializing controllers: {e}")
        return

    print("\nBridge started. Press Ctrl+C to stop.")
    
    try:
        while True:
            color = icue.get_average_color()
            if color:
                magic_home.set_color(color)
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nBridge stopped.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print("\nBridge stopped due to error.")
    finally:
        # Always turn off the LED strip when the bridge stops
        try:
            magic_home.turn_off()
            print("LED strip turned off.")
        except Exception as e:
            logger.error(f"Error turning off LED strip: {e}")

def main():
    # Initialize iCUE SDK
    sdk = CueSdk()
    logger.setLevel(logging.ERROR)  # Zet logging level op ERROR voordat we de SDK initialiseren
    
    # Laad configuratie
    config = load_config()
    
    # Start de bridge
    start_bridge(sdk, config)

if __name__ == "__main__":
    main() 