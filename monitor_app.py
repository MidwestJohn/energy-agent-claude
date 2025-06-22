#!/usr/bin/env python3
"""
App Monitoring Script for Energy Agent Streamlit Cloud Deployment
Monitors app health, performance, and generates usage reports
"""

import requests
import time
import json
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

class AppMonitor:
    def __init__(self, app_url, config_file='monitor_config.json'):
        self.app_url = app_url.rstrip('/')
        self.config_file = config_file
        self.log_file = f"monitor_log_{datetime.now().strftime('%Y%m%d')}.json"
        self.alerts_file = f"alerts_{datetime.now().strftime('%Y%m%d')}.json"
        self.load_config()
        
    def load_config(self):
        """Load monitoring configuration"""
        default_config = {
            'check_interval': 300,  # 5 minutes
            'timeout': 10,
            'performance_threshold': 3.0,  # seconds
            'error_threshold': 3,  # consecutive errors
            'alert_email': None,
            'alert_webhook': None,
            'retention_days': 7
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    self.config = {**default_config, **json.load(f)}
            except Exception as e:
                print(f"⚠️ Could not load config file: {e}")
                self.config = default_config
        else:
            self.config = default_config
            self.save_config()
    
    def save_config(self):
        """Save monitoring configuration"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"⚠️ Could not save config file: {e}")
    
    def check_app_health(self):
        """Check app health and performance"""
        try:
            start_time = time.time()
            response = requests.get(self.app_url, timeout=self.config['timeout'])
            end_time = time.time()
            
            response_time = end_time - start_time
            
            health_data = {
                'timestamp': datetime.now().isoformat(),
                'status_code': response.status_code,
                'response_time': response_time,
                'is_healthy': response.status_code == 200,
                'performance_ok': response_time < self.config['performance_threshold']
            }
            
            return health_data
            
        except requests.exceptions.Timeout:
            return {
                'timestamp': datetime.now().isoformat(),
                'status_code': None,
                'response_time': None,
                'is_healthy': False,
                'performance_ok': False,
                'error': 'Timeout'
            }
        except requests.exceptions.ConnectionError:
            return {
                'timestamp': datetime.now().isoformat(),
                'status_code': None,
                'response_time': None,
                'is_healthy': False,
                'performance_ok': False,
                'error': 'Connection Error'
            }
        except Exception as e:
            return {
                'timestamp': datetime.now().isoformat(),
                'status_code': None,
                'response_time': None,
                'is_healthy': False,
                'performance_ok': False,
                'error': str(e)
            }
    
    def log_health_check(self, health_data):
        """Log health check results"""
        try:
            # Load existing log
            log_data = []
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r') as f:
                    log_data = json.load(f)
            
            # Add new entry
            log_data.append(health_data)
            
            # Keep only recent entries (based on retention_days)
            cutoff_date = datetime.now() - timedelta(days=self.config['retention_days'])
            log_data = [entry for entry in log_data 
                       if datetime.fromisoformat(entry['timestamp']) > cutoff_date]
            
            # Save updated log
            with open(self.log_file, 'w') as f:
                json.dump(log_data, f, indent=2)
                
        except Exception as e:
            print(f"⚠️ Could not log health check: {e}")
    
    def check_for_alerts(self, health_data):
        """Check if alerts should be triggered"""
        alerts = []
        
        # Check recent health data for patterns
        try:
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r') as f:
                    recent_checks = json.load(f)
                
                # Check for consecutive errors
                recent_errors = [check for check in recent_checks[-self.config['error_threshold']:] 
                               if not check.get('is_healthy', True)]
                
                if len(recent_errors) >= self.config['error_threshold']:
                    alerts.append({
                        'type': 'consecutive_errors',
                        'message': f'App has been down for {len(recent_errors)} consecutive checks',
                        'timestamp': datetime.now().isoformat(),
                        'severity': 'high'
                    })
                
                # Check for performance issues
                recent_slow = [check for check in recent_checks[-5:] 
                             if check.get('response_time', 0) > self.config['performance_threshold']]
                
                if len(recent_slow) >= 3:
                    alerts.append({
                        'type': 'performance_degradation',
                        'message': f'App performance degraded for {len(recent_slow)} recent checks',
                        'timestamp': datetime.now().isoformat(),
                        'severity': 'medium'
                    })
                    
        except Exception as e:
            print(f"⚠️ Could not check for alerts: {e}")
        
        # Check current health data
        if not health_data.get('is_healthy', True):
            alerts.append({
                'type': 'app_down',
                'message': f'App is currently down (Status: {health_data.get("status_code", "Unknown")})',
                'timestamp': datetime.now().isoformat(),
                'severity': 'high'
            })
        
        if not health_data.get('performance_ok', True):
            alerts.append({
                'type': 'slow_response',
                'message': f'App response time is slow ({health_data.get("response_time", 0):.2f}s)',
                'timestamp': datetime.now().isoformat(),
                'severity': 'medium'
            })
        
        return alerts
    
    def log_alerts(self, alerts):
        """Log alerts"""
        if not alerts:
            return
        
        try:
            # Load existing alerts
            alert_data = []
            if os.path.exists(self.alerts_file):
                with open(self.alerts_file, 'r') as f:
                    alert_data = json.load(f)
            
            # Add new alerts
            alert_data.extend(alerts)
            
            # Save updated alerts
            with open(self.alerts_file, 'w') as f:
                json.dump(alert_data, f, indent=2)
                
        except Exception as e:
            print(f"⚠️ Could not log alerts: {e}")
    
    def send_alert(self, alert):
        """Send alert via configured method"""
        print(f"🚨 ALERT: {alert['message']}")
        
        # Here you could implement email, Slack, or webhook notifications
        # For now, just print to console
        if self.config.get('alert_webhook'):
            try:
                requests.post(self.config['alert_webhook'], json=alert, timeout=5)
                print(f"✅ Alert sent to webhook")
            except Exception as e:
                print(f"⚠️ Could not send webhook alert: {e}")
    
    def generate_usage_report(self):
        """Generate usage and performance report"""
        try:
            if not os.path.exists(self.log_file):
                return "No monitoring data available"
            
            with open(self.log_file, 'r') as f:
                log_data = json.load(f)
            
            if not log_data:
                return "No monitoring data available"
            
            # Calculate statistics
            total_checks = len(log_data)
            healthy_checks = len([check for check in log_data if check.get('is_healthy', False)])
            uptime_percentage = (healthy_checks / total_checks) * 100 if total_checks > 0 else 0
            
            response_times = [check.get('response_time', 0) for check in log_data 
                            if check.get('response_time') is not None]
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            max_response_time = max(response_times) if response_times else 0
            
            # Recent activity (last 24 hours)
            cutoff_24h = datetime.now() - timedelta(hours=24)
            recent_checks = [check for check in log_data 
                           if datetime.fromisoformat(check['timestamp']) > cutoff_24h]
            
            report = f"""
# App Monitoring Report

## Summary (Last {self.config['retention_days']} days)
- **Total Checks:** {total_checks}
- **Healthy Checks:** {healthy_checks}
- **Uptime:** {uptime_percentage:.1f}%
- **Average Response Time:** {avg_response_time:.2f}s
- **Maximum Response Time:** {max_response_time:.2f}s

## Recent Activity (Last 24 hours)
- **Checks:** {len(recent_checks)}
- **Healthy:** {len([c for c in recent_checks if c.get('is_healthy', False)])}
- **Errors:** {len([c for c in recent_checks if not c.get('is_healthy', True)])}

## Performance Thresholds
- **Target Response Time:** < {self.config['performance_threshold']}s
- **Error Threshold:** {self.config['error_threshold']} consecutive errors

## App Information
- **URL:** {self.app_url}
- **Last Check:** {log_data[-1]['timestamp'] if log_data else 'Never'}
- **Status:** {'🟢 Healthy' if log_data[-1].get('is_healthy', False) else '🔴 Unhealthy' if log_data else '❓ Unknown'}
"""
            
            return report
            
        except Exception as e:
            return f"Error generating report: {e}"
    
    def run_single_check(self):
        """Run a single health check"""
        print(f"🔍 Checking app health: {self.app_url}")
        
        health_data = self.check_app_health()
        self.log_health_check(health_data)
        
        # Display results
        status_icon = "✅" if health_data.get('is_healthy', False) else "❌"
        print(f"{status_icon} Status: {'Healthy' if health_data.get('is_healthy', False) else 'Unhealthy'}")
        
        if health_data.get('response_time'):
            print(f"⏱️ Response Time: {health_data['response_time']:.2f}s")
        
        if health_data.get('status_code'):
            print(f"📊 Status Code: {health_data['status_code']}")
        
        if health_data.get('error'):
            print(f"🚨 Error: {health_data['error']}")
        
        # Check for alerts
        alerts = self.check_for_alerts(health_data)
        if alerts:
            print(f"\n🚨 {len(alerts)} alert(s) triggered:")
            for alert in alerts:
                print(f"   - {alert['message']}")
                self.send_alert(alert)
        
        self.log_alerts(alerts)
        
        return health_data.get('is_healthy', False)
    
    def run_continuous_monitoring(self):
        """Run continuous monitoring"""
        print(f"🔄 Starting continuous monitoring for: {self.app_url}")
        print(f"⏰ Check interval: {self.config['check_interval']} seconds")
        print("Press Ctrl+C to stop monitoring")
        print("="*60)
        
        try:
            while True:
                self.run_single_check()
                print(f"⏳ Next check in {self.config['check_interval']} seconds...")
                time.sleep(self.config['check_interval'])
                
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped by user")
            print("📊 Generating final report...")
            print(self.generate_usage_report())

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python monitor_app.py <app_url> [check|monitor|report]")
        print("")
        print("Commands:")
        print("  check   - Run a single health check")
        print("  monitor - Run continuous monitoring")
        print("  report  - Generate usage report")
        print("")
        print("Examples:")
        print("  python monitor_app.py https://your-app.streamlit.app check")
        print("  python monitor_app.py https://your-app.streamlit.app monitor")
        print("  python monitor_app.py https://your-app.streamlit.app report")
        return 1
    
    app_url = sys.argv[1]
    command = sys.argv[2] if len(sys.argv) > 2 else 'check'
    
    print("📊 Energy Agent App Monitor")
    print("="*40)
    
    monitor = AppMonitor(app_url)
    
    if command == 'check':
        monitor.run_single_check()
    elif command == 'monitor':
        monitor.run_continuous_monitoring()
    elif command == 'report':
        print(monitor.generate_usage_report())
    else:
        print(f"❌ Unknown command: {command}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 