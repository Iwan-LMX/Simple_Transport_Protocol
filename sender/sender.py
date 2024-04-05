#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import random
import socket
import sys
import threading
import time
from dataclasses import dataclass

NUM_ARGS  = 7  # Number of command-line arguments
BUF_SIZE  = 3  # Size of buffer for receiving messages
MAX_SLEEP = 2  # Max seconds to sleep before sending the next message
