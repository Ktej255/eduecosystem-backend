# Monitoring Integration Guide

## Overview
This guide provides instructions for integrating the Eduecosystem backend health check endpoint with various monitoring and alerting systems.

---

## 1. AWS CloudWatch

### Health Check Alarm
```python
import boto3

cloudwatch = boto3.client('cloudwatch')

# Create alarm for health check failures
cloudwatch.put_metric_alarm(
    AlarmName='eduecosystem-health-check-failed',
    ComparisonOperator='LessThanThreshold',
    EvaluationPeriods=2,
    MetricName='HealthyHostCount',
    Namespace='AWS/ApplicationELB',
    Period=60,
    Statistic='Average',
    Threshold=1.0,
    ActionsEnabled=True,
    AlarmActions=['arn:aws:sns:region:account:topic-name'],
    AlarmDescriptions='Health check is failing for Eduecosystem backend'
)
```

### Custom Metric from Health Endpoint
```python
import requests
import boto3
import time

def publish_health_metrics():
    cloudwatch = boto3.client('cloudwatch')
    
    # Call health endpoint
    response = requests.get('https://yourdomain.com/health')
    health_data = response.json()
    
    # Publish metrics
    metrics = []
    
    # Overall health status (1=healthy, 0.5=degraded, 0=unhealthy)
    status_value = {
        'healthy': 1.0,
        'degraded': 0.5,
        'unhealthy': 0.0
    }.get(health_data['status'], 0.0)
    
    metrics.append({
        'MetricName': 'HealthStatus',
        'Value': status_value,
        'Unit': 'None',
        'Timestamp': time.time()
    })
    
    # Database health (1=healthy, 0=unhealthy)
    db_health = 1.0 if health_data['checks']['database']['status'] == 'healthy' else 0.0
    metrics.append({
        'MetricName': 'DatabaseHealth',
        'Value': db_health,
        'Unit': 'None',
        'Timestamp': time.time()
    })
    
    # Cache health (1=healthy, 0.5=degraded, 0=unhealthy)
    cache_status = health_data['checks']['cache']['status']
    cache_health = 1.0 if cache_status == 'healthy' else (0.5 if cache_status == 'degraded' else 0.0)
    metrics.append({
        'MetricName': 'CacheHealth',
        'Value': cache_health,
        'Unit': 'None',
        'Timestamp': time.time()
    })
    
    # Publish all metrics
    cloudwatch.put_metric_data(
        Namespace='Eduecosystem',
        MetricData=metrics
    )

# Run every minute
if __name__ == '__main__':
    while True:
        try:
            publish_health_metrics()
        except Exception as e:
            print(f"Error publishing metrics: {e}")
        time.sleep(60)
```

---

## 2. Prometheus

### Metrics Exporter
Add to `main.py`:

```python
from prometheus_client import Gauge, generate_latest
from fastapi import Response

# Define metrics
health_status_gauge = Gauge('eduecosystem_health_status', 'Overall health status', ['environment'])
database_health_gauge = Gauge('eduecosystem_database_health', 'Database health status', ['environment'])
cache_health_gauge = Gauge('eduecosystem_cache_health', 'Cache health status', ['environment'])

@app.get("/metrics")
def metrics():
    """Prometheus metrics endpoint"""
    from app.core.config import settings
    import requests
    
    # Get health data
    health_response = requests.get("http://localhost:8000/health")
    health_data = health_response.json()
    
    # Update gauges
    status_value = {
        'healthy': 1.0,
        'degraded': 0.5,
        'unhealthy': 0.0
    }.get(health_data['status'], 0.0)
    
    health_status_gauge.labels(environment=settings.ENVIRONMENT).set(status_value)
    
    db_health = 1.0 if health_data['checks']['database']['status'] == 'healthy' else 0.0
    database_health_gauge.labels(environment=settings.ENVIRONMENT).set(db_health)
    
    cache_status = health_data['checks']['cache']['status']
    cache_health = 1.0 if cache_status == 'healthy' else (0.5 if cache_status == 'degraded' else 0.0)
    cache_health_gauge.labels(environment=settings.ENVIRONMENT).set(cache_health)
    
    # Return metrics
    return Response(content=generate_latest(), media_type="text/plain")
```

### Prometheus Configuration
Add to `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'eduecosystem'
    scrape_interval: 30s
    static_configs:
      - targets: ['yourdomain.com:443']
    scheme: https
    metrics_path: '/metrics'
```

### Alert Rules
Create `eduecosystem_alerts.yml`:

```yaml
groups:
  - name: eduecosystem
    interval: 30s
    rules:
      - alert: HealthCheckUnhealthy
        expr: eduecosystem_health_status < 1
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Eduecosystem health check is unhealthy"
          description: "Health status is {{ $value }} (1=healthy, 0.5=degraded, 0=unhealthy)"
      
      - alert: DatabaseConnectionFailed
        expr: eduecosystem_database_health == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Database connection failed"
          description: "Unable to connect to database"
      
      - alert: CacheDegraded
        expr: eduecosystem_cache_health < 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Cache is degraded or unavailable"
          description: "Cache health is {{ $value }} (1=healthy, 0.5=degraded)"
```

---

## 3. Datadog

### Agent Configuration
Create `/etc/datadog-agent/conf.d/eduecosystem.d/conf.yaml`:

```yaml
init_config:

instances:
  - url: https://yourdomain.com/health
    name: eduecosystem_production
    check_certificate_expiration: true
    timeout: 10
    content_match: '"status":"healthy"'
    http_response_status_code: 200
    tags:
      - env:production
      - service:eduecosystem
    headers:
      User-Agent: Datadog-Agent
```

### Custom Check
Create `/etc/datadog-agent/checks.d/eduecosystem_health.py`:

```python
from datadog_checks.base import AgentCheck
import requests

class HealthCheck(AgentCheck):
    def check(self, instance):
        url = instance.get('url')
        tags = instance.get('tags', [])
        
        try:
            response = requests.get(url, timeout=10)
            health_data = response.json()
            
            # Overall health
            status_value = {
                'healthy': 1,
                'degraded': 0.5,
                'unhealthy': 0
            }.get(health_data['status'], 0)
            
            self.gauge('eduecosystem.health.status', status_value, tags=tags)
            
            # Database health
            db_health = 1 if health_data['checks']['database']['status'] == 'healthy' else 0
            self.gauge('eduecosystem.health.database', db_health, tags=tags)
            
            # Cache health
            cache_status = health_data['checks']['cache']['status']
            cache_health = 1 if cache_status == 'healthy' else (0.5 if cache_status == 'degraded' else 0)
            self.gauge('eduecosystem.health.cache', cache_health, tags=tags)
            
            # Service check
            if health_data['status'] == 'healthy':
                self.service_check('eduecosystem.health', AgentCheck.OK, tags=tags)
            elif health_data['status'] == 'degraded':
                self.service_check('eduecosystem.health', AgentCheck.WARNING, tags=tags)
            else:
                self.service_check('eduecosystem.health', AgentCheck.CRITICAL, tags=tags)
                
        except Exception as e:
            self.service_check('eduecosystem.health', AgentCheck.CRITICAL, 
                             message=str(e), tags=tags)
```

### Monitor Configuration
```json
{
  "name": "Eduecosystem Health Check",
  "type": "service check",
  "query": "\"eduecosystem.health\".over(\"env:production\").last(2).count_by_status()",
  "message": "{{#is_alert}}Eduecosystem health check is failing!{{/is_alert}}\n{{#is_warning}}Eduecosystem is degraded{{/is_warning}}\n@pagerduty-eduecosystem",
  "tags": ["service:eduecosystem", "env:production"],
  "options": {
    "thresholds": {
      "critical": 1,
      "warning": 1
    },
    "notify_no_data": true,
    "no_data_timeframe": 10
  }
}
```

---

## 4. New Relic

### Synthetics Monitor
```javascript
// New Relic Synthetics Script
var assert = require('assert');

$http.get('https://yourdomain.com/health', function(err, response, body) {
  // Check status code
  assert.equal(response.statusCode, 200, 'Expected 200 OK response');
  
  // Parse response
  var health = JSON.parse(body);
  
  // Check overall health
  assert.equal(health.status, 'healthy', 'Expected healthy status');
  
  // Check database
  assert.equal(health.checks.database.status, 'healthy', 'Database should be healthy');
  
  // Custom metrics
  $util.insights.set('healthStatus', health.status === 'healthy' ? 1 : 0);
  $util.insights.set('databaseHealth', health.checks.database.status === 'healthy' ? 1 : 0);
  $util.insights.set('cacheHealth', health.checks.cache.status === 'healthy' ? 1 : 0);
});
```

---

## 5. Uptime Robot

### HTTP(s) Monitor Setup
1. **Monitor Type:** HTTP(s)
2. **URL:** `https://yourdomain.com/health`
3. **Monitoring Interval:** 5 minutes
4. **Monitor Timeout:** 30 seconds
5. **Keyword Check:** `"status":"healthy"`
6. **Alert Contacts:** Your email/SMS/Slack

---

## 6. PagerDuty Integration

### Webhook Alert Script
```python
import requests
import json

def send_pagerduty_alert(health_data):
    """Send alert to PagerDuty when health is not optimal"""
    
    if health_data['status'] != 'healthy':
        payload = {
            "routing_key": "YOUR_INTEGRATION_KEY",
            "event_action": "trigger",
            "payload": {
                "summary": f"Eduecosystem health: {health_data['status']}",
                "severity": "critical" if health_data['status'] == 'unhealthy' else "warning",
                "source": "eduecosystem-health-monitor",
                "custom_details": health_data['checks']
            }
        }
        
        response = requests.post(
            'https://events.pagerduty.com/v2/enqueue',
            data=json.dumps(payload),
            headers={'Content-Type': 'application/json'}
        )
        
        return response.status_code == 202

# Monitor continuously
import time

while True:
    response = requests.get('https://yourdomain.com/health')
    health_data = response.json()
    
    send_pagerduty_alert(health_data)
    
    time.sleep(300)  # Check every 5 minutes
```

---

## 7. Grafana Dashboard

### Dashboard JSON
```json
{
  "dashboard": {
    "title": "Eduecosystem Health",
    "panels": [
      {
        "title": "Overall Health Status",
        "type": "stat",
        "targets": [
          {
            "expr": "eduecosystem_health_status",
            "legendFormat": "Health"
          }
        ],
        "options": {
          "colorMode": "background",
          "graphMode": "area",
          "thresholds": [
            {"value": 0, "color": "red"},
            {"value": 0.5, "color": "yellow"},
            {"value": 1, "color": "green"}
          ]
        }
      },
      {
        "title": "Component Health",
        "type": "bargauge",
        "targets": [
          {
            "expr": "eduecosystem_database_health",
            "legendFormat": "Database"
          },
          {
            "expr": "eduecosystem_cache_health",
            "legendFormat": "Cache"
          }
        ]
      },
      {
        "title": "Health Status Over Time",
        "type": "graph",
        "targets": [
          {
            "expr": "eduecosystem_health_status",
            "legendFormat": "Overall"
          },
          {
            "expr": "eduecosystem_database_health",
            "legendFormat": "Database"
          },
          {
            "expr": "eduecosystem_cache_health",
            "legendFormat": "Cache"
          }
        ]
      }
    ]
  }
}
```

---

## 8. Slack Notifications

### Webhook Integration
```python
import requests
import json
import time

SLACK_WEBHOOK = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

def send_slack_alert(health_data):
    """Send Slack notification for health issues"""
    
    status = health_data['status']
    
    # Only alert on degraded or unhealthy
    if status != 'healthy':
        color = "danger" if status == "unhealthy" else "warning"
        
        message = {
            "attachments": [
                {
                    "color": color,
                    "title": f"🚨 Eduecosystem Health: {status.upper()}",
                    "fields": [
                        {
                            "title": "Database",
                            "value": health_data['checks']['database']['message'],
                            "short": True
                        },
                        {
                            "title": "Cache",
                            "value": health_data['checks']['cache']['message'],
                            "short": True
                        }
                    ],
                    "footer": f"Environment: {health_data['environment']}",
                    "ts": int(health_data['timestamp'])
                }
            ]
        }
        
        requests.post(SLACK_WEBHOOK, data=json.dumps(message))

# Monitor
while True:
    try:
        response = requests.get('https://yourdomain.com/health')
        send_slack_alert(response.json())
    except Exception as e:
        print(f"Error: {e}")
    
    time.sleep(300)
```

---

## Summary

### Quick Integration Checklist

- [ ] **AWS CloudWatch** - Custom metrics and alarms
- [ ] **Prometheus** - Metrics scraping and rules
- [ ] **Datadog** - Agent configuration and monitors
- [ ] **New Relic** - Synthetics monitoring
- [ ] **Uptime Robot** - Simple uptime monitoring
- [ ] **PagerDuty** - Incident management
- [ ] **Grafana** - Visualization dashboards
- [ ] **Slack** - Team notifications

### Recommended Setup
For most deployments, we recommend:
1. **Uptime Robot** - Simple external monitoring (free tier available)
2. **Prometheus + Grafana** - Detailed metrics and visualization
3. **Slack/PagerDuty** - Team alerts

This provides comprehensive coverage with minimal overhead.
