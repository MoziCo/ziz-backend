# Lightweight Python base
FROM python:3.12-slim

# Build args for mapping host user
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=1000

# Install packages and create matching user
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        sudo \
        git \
        curl \
        build-essential \
        openssh-client \
        man \
        less \
        nano \
        vim \
        net-tools \
        iputils-ping \
        procps \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - \
    && apt-get install -y nodejs \
    && npm install -g @anthropic-ai/claude-code
# create group & user with same GID/UID as host
RUN groupadd --gid $USER_GID $USERNAME
RUN useradd --uid $USER_UID --gid $USER_GID -m $USERNAME

# give passwordless sudo to that user
    # ensure sudoers.d exists
RUN install -d -m 0755 /etc/sudoers.d
RUN echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/$USERNAME
RUN chmod 0440 /etc/sudoers.d/$USERNAME

# switch to non-root user
USER $USERNAME

# set workdir
WORKDIR /workspace

# Install Poetry as the non-root user
RUN curl -sSL https://install.python-poetry.org | python3 - \
    && sudo ln -s /home/$USERNAME/.local/bin/poetry /usr/local/bin/poetry
