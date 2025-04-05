from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import logging

logger = logging.getLogger(__name__)

def register_web_routes(app: Flask):
    """Register web UI routes with the Flask application"""
    
    @app.route('/')
    def index():
        """Main landing page"""
        return render_template('index.html')
    
    @app.route('/dashboard')
    def dashboard():
        """Dashboard page for overall system status"""
        return render_template('dashboard.html')
    
    @app.route('/containers')
    def containers():
        """Container management page"""
        return render_template('containers.html')
    
    @app.route('/items')
    def items():
        """Item management page"""
        return render_template('items.html')
    
    @app.route('/logs')
    def logs():
        """Action logs page"""
        return render_template('logs.html')
    
    @app.route('/simulation')
    def simulation():
        """Time simulation page"""
        return render_template('simulation.html')
