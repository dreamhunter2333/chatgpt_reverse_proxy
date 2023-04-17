# Chatgpt reverse proxy based on Browser

**TODO**

- [ ] vnc password

## RUN docker

open localhost:7900, your can forward port 7900 to local by ssh, and login to `https://chat.openai.com/`

UI use [chatgpt-web-share](https://github.com/moeakwak/chatgpt-web-share/wiki/%E4%B8%AD%E6%96%87%E6%8C%87%E5%8D%97)

```bash
ssh -L 7900:localhost:7900  azure_vm
```

```yaml
version: "3"

services:
  chatgpt-share:
    image: ghcr.io/moeakwak/chatgpt-web-share:latest
    container_name: chatgpt-web-share
    restart: always
    ports:
      - 80:80
      - 8080:80
      # - 6060:6060
    cpus: 0.2
    depends_on:
      - chatgpt-reverse-proxy
    volumes:
      - ./data:/data
      - ./config.yaml:/app/backend/api/config/config.yaml
      - ./logs:/app/logs

  chatgpt-reverse-proxy:
    image: ghcr.io/dreamhunter2333/chatgpt_reverse_proxy:latest
    container_name: chatgpt-reverse-proxy
    restart: always
    ports:
      - "8000:8000"
      - "7900:7900"
    volumes:
      - ./tmp:/app/tmp
    environment:
      - VNC_NO_PASSWORD=1
      - user_data_dir=/app/tmp
      - timeout=100000
      - navigation_timeout=100000
```


## RUN local

```bash
python3 -m venv ./venv
./venv/bin/python -m pip install -r requirements.txt
./venv/bin/playwright install
./venv/bin/python server.py
./venv/bin/python main.py
```
