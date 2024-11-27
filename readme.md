

# Screenshot-Stealer

```
 __________                  __             __     ________             .___ 
 \______   \  ____    ____  |  | __  ____ _/  |_  /  _____/   ____    __| _/ 
  |       _/ /  _ \ _/ ___\ |  |/ /_/ __ \\   __\/   \  ___  /  _ \  / __ |  
  |    |   \(  <_> )\  \___ |    < \  ___/ |  |  \    \_\  \(  <_> )/ /_/ |  
  |____|_  / \____/  \___  >|__|_ \ \___  >|__|   \______  / \____/ \____ |  
         \/              \/      \/     \/               \/              \/
                                                          & NeedNotApply 🙃  
```

Created by [RocketGod](https://github.com/RocketGod-git)  
Modified for Matrix use by [NeedNotApply](https://github.com/neednotapply)  

**Disclaimer**: This repository is meant for educational purposes only. It demonstrates how a brute-force URL generator might work. Using such scripts for unauthorized access, data scraping, or any malicious intent is illegal and unethical. Always seek permission before testing and never misuse the knowledge.

## Description
This script demonstrates the generation of URLs in a brute-force manner. It's a theoretical exploration to understand the mechanism and develop countermeasures against potential misuse. This example would bruteforce URLs at prnt.sc taken with Lightshot and stream them to a Matrix Room.

## Installation & Use

1. **Clone the repository**
   ```
   git clone https://github.com/neednotapply/screenshot-stealer
   ```

2. **Install the requirements**
   ```
   pip install matrix-nio aiohttp selenium webdriver-manager
   ```

3. **Configuration**  
   Edit the config.json file, replace @your_bot_username:matrix.org with your Matrix bot's username, replace your_bot_password with your Matrix bot's password and adjust the homeserver_url appropriately if the bot will not belong to the default https://matrix.org federation. (for demonstration purposes)  

4. **Run the script**
   ```
   python runme.py
   ```

## Note
Please ensure you have proper authorization before testing on any platform or service. Unauthorized use can result in legal action and banning from platforms.

![rocketgod_logo](https://github.com/RocketGod-git/screenshot-stealer/assets/57732082/35fd7604-eee4-4e77-bd0d-d16c71b33ef7)
