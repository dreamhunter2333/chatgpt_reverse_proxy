FROM mcr.microsoft.com/playwright/python:v1.32.1-focal
USER root
RUN apt-get update && apt-get install -y supervisor wget
RUN mkdir -p /var/log/supervisor
#==============
# Xvfb
#==============
RUN apt-get update -qqy \
    && apt-get -qqy install \
    xvfb \
    pulseaudio \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/*

#==============================
# Locale and encoding settings
#==============================
ENV LANG_WHICH en
ENV LANG_WHERE US
ENV ENCODING UTF-8
ENV LANGUAGE ${LANG_WHICH}_${LANG_WHERE}.${ENCODING}
ENV LANG ${LANGUAGE}
# Layer size: small: ~9 MB
# Layer size: small: ~9 MB MB (with --no-install-recommends)
RUN apt-get -qqy update \
    && apt-get -qqy --no-install-recommends install \
    language-pack-en \
    tzdata \
    locales \
    && locale-gen ${LANGUAGE} \
    && dpkg-reconfigure --frontend noninteractive locales \
    && apt-get -qyy autoremove \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get -qyy clean

#=====
# VNC
#=====
RUN apt-get update -qqy \
    && apt-get -qqy install \
    x11vnc \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/*

#=========
# fluxbox
# A fast, lightweight and responsive window manager
#=========
RUN apt-get update -qqy \
    && apt-get -qqy install \
    fluxbox \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/*

#================
# Font libraries
#================
# libfontconfig            ~1 MB
# libfreetype6             ~1 MB
# xfonts-cyrillic          ~2 MB
# xfonts-scalable          ~2 MB
# fonts-liberation         ~3 MB
# fonts-ipafont-gothic     ~13 MB
# fonts-wqy-zenhei         ~17 MB
# fonts-tlwg-loma-otf      ~300 KB
# ttf-ubuntu-font-family   ~5 MB
#   Ubuntu Font Family, sans-serif typeface hinted for clarity
# Removed packages:
# xfonts-100dpi            ~6 MB
# xfonts-75dpi             ~6 MB
# fonts-noto-color-emoji   ~10 MB
# Regarding fonts-liberation see:
#  https://github.com/SeleniumHQ/docker-selenium/issues/383#issuecomment-278367069
# Layer size: small: 50.3 MB (with --no-install-recommends)
# Layer size: small: 50.3 MB
RUN apt-get -qqy update \
    && apt-get -qqy --no-install-recommends install \
    libfontconfig \
    libfreetype6 \
    xfonts-cyrillic \
    xfonts-scalable \
    fonts-liberation \
    fonts-ipafont-gothic \
    fonts-wqy-zenhei \
    fonts-tlwg-loma-otf \
    ttf-ubuntu-font-family \
    fonts-noto-color-emoji \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get -qyy clean
########################################
# noVNC exposes VNC through a web page #
########################################
RUN apt-get update -qqy \
    && apt-get -qqy install \
    unzip \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/*
COPY docker /opt/bin/
ENV NOVNC_VERSION="1.4.0" \
    WEBSOCKIFY_VERSION="0.11.0"
RUN wget -nv -O noVNC.zip \
    "https://github.com/novnc/noVNC/archive/refs/tags/v${NOVNC_VERSION}.zip" \
    && unzip -x noVNC.zip \
    && ls -la \
    && mv noVNC-${NOVNC_VERSION} /opt/bin/noVNC \
    && cp /opt/bin/noVNC/vnc.html /opt/bin/noVNC/index.html \
    && rm noVNC.zip \
    && wget -nv -O websockify.zip \
    "https://github.com/novnc/websockify/archive/refs/tags/v${WEBSOCKIFY_VERSION}.zip" \
    && unzip -x websockify.zip \
    && rm websockify.zip \
    && rm -rf websockify-${WEBSOCKIFY_VERSION}/tests \
    && mv websockify-${WEBSOCKIFY_VERSION} /opt/bin/noVNC/utils/websockify
# Creating base directory for Xvfb
RUN mkdir -p /tmp/.X11-unix &&  chmod 1777 /tmp/.X11-unix
# Following line fixes https://github.com/SeleniumHQ/docker-selenium/issues/87
ENV DBUS_SESSION_BUS_ADDRESS=/dev/null
#============================
# Some configuration options
#============================
ENV SE_SCREEN_WIDTH 1360
ENV SE_SCREEN_HEIGHT 1020
ENV SE_SCREEN_DEPTH 24
ENV SE_SCREEN_DPI 96
ENV SE_START_XVFB true
ENV SE_START_VNC true
ENV SE_START_NO_VNC true
ENV SE_NO_VNC_PORT 7900
ENV SE_VNC_PORT 5900
ENV DISPLAY :99.0
ENV DISPLAY_NUM 99

COPY . /app
WORKDIR /app
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
RUN python3 -m pip install -r requirements.txt
EXPOSE 8000
EXPOSE 9222
CMD ["/usr/bin/supervisord"]
