# iCUE Magic Home Bridge

A Python bridge that synchronizes your iCUE RGB devices (keyboard, mouse, etc.) with Magic Home LED strips, creating a unified ambient lighting experience.

## 🌟 Features

- **Real-time synchronization**: Instantly mirrors your iCUE device colors to Magic Home LED strips
- **Smooth color transitions**: Gradual color changes for a more natural lighting experience
- **Automatic device detection**: Wizard-based setup for easy configuration
- **Automatic shutdown**: LED strips turn off when the bridge stops
- **Robust error handling**: Automatic reconnection and error recovery
- **Configurable logging**: Adjustable log levels for debugging

## 📋 Requirements

### Hardware
- **iCUE-compatible device**: Corsair keyboard, mouse, headset, or other RGB device
- **Magic Home LED controller**: WiFi-enabled LED strip controller (e.g., Magic Home Pro, Flux LED)
- **Network**: Both devices must be on the same network

### Software
- **Python 3.7+**
- **iCUE Software**: Latest version installed and running
- **Magic Home App**: For initial LED strip setup (optional)

## 🚀 Installation

### 1. Clone the repository
```bash
git clone https://github.com/aderik/icuemagic.git
cd icuemagic
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the setup wizard
```bash
python bridge.py
```

The wizard will automatically:
- Detect and connect to your iCUE devices
- Scan your network for Magic Home controllers
- Create a `config.json` file with your settings

## ⚙️ Configuration

The bridge creates a `config.json` file with the following settings:

```json
{
  "icue_device_id": "your_device_id",
  "magichome_ip": "192.168.1.100",
  "log_level": "ERROR"
}
```

### Log Levels
- `ERROR`: Only show errors (default)
- `WARNING`: Show errors and warnings
- `INFO`: Show normal information
- `DEBUG`: Show detailed debug information

## 🎮 Usage

### Starting the bridge
```bash
python bridge.py
```

The bridge will:
1. Connect to your iCUE device
2. Connect to your Magic Home LED strip
3. Start synchronizing colors in real-time
4. Display status messages

### Stopping the bridge
Press `Ctrl+C` to stop the bridge. The LED strip will automatically turn off.

## 🔧 Troubleshooting

### Common Issues

**"No iCUE devices found"**
- Make sure iCUE software is running
- Ensure your device is connected and recognized by iCUE
- Try restarting the iCUE software

**"No Magic Home controllers found"**
- Verify your LED controller is powered on
- Ensure both devices are on the same network
- Check if the controller is connected to WiFi
- Try using the Magic Home app to verify connectivity

**"Connection timeout"**
- Check your network connection
- Verify the IP address in `config.json`
- Try restarting your router if needed

**"Import errors"**
- Make sure all dependencies are installed: `pip install -r requirements.txt`
- Verify you're using Python 3.7 or higher

### Debug Mode
To get more detailed information, change the log level in `config.json`:
```json
{
  "log_level": "DEBUG"
}
```

## 📁 Project Structure

```
icuemagic/
├── bridge.py          # Main bridge application
├── requirements.txt   # Python dependencies
├── config.json        # Configuration file (auto-generated)
├── icuemagic.log     # Log file (auto-generated)
└── README.md         # This file
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup
1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Test thoroughly
5. Commit your changes: `git commit -am 'Add feature'`
6. Push to the branch: `git push origin feature-name`
7. Submit a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Corsair** for the iCUE SDK
- **Magic Home** for the LED controller technology
- **flux_led** Python library contributors

## 📞 Support

If you encounter any issues or have questions:

1. Check the [troubleshooting section](#troubleshooting)
2. Search existing [issues](../../issues)
3. Create a new issue with detailed information about your problem

## 🔄 Version History

- **v1.0.0**: Initial release with basic iCUE to Magic Home synchronization
- **v1.1.0**: Added automatic LED strip shutdown and improved error handling

---

**Note**: This project is not affiliated with Corsair or Magic Home. Use at your own risk. 
