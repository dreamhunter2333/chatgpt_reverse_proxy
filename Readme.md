# Chatgpt reverse proxy based on Browser

**TODO**

- [ ] vnc password

## RUN docker

```yaml
services:
  chatgpt_reverse_proxy:
    image: ghcr.io/dreamhunter2333/chatgpt_reverse_proxy:latest
    container_name: chatgpt_reverse_proxy
    restart: always
    ports:
      - "8000:8000"
      - "7900:7900"
    volumes:
      - ./tmp:/app/tmp
    environment:
      - VNC_NO_PASSWORD=1
      - user_data_dir=/app/tmp
```

## RUN local

```bash
python3 -m venv ./venv
./venv/bin/python -m pip install -r requirements.txt
./venv/bin/playwright install
./venv/bin/python server.py
./venv/bin/python main.py
```
