#!/usr/bin/env python3

from flask import Flask, redirect, url_for

app = Flask(__name__)

@app.route('/')
def main():
    return redirect(url_for('static', filename='nl/index.html'))
