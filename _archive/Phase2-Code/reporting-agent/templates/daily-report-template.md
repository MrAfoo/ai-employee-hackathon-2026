# Daily Report - {{ date }}

**Generated**: {{ timestamp }}  
**Period**: {{ start_date }} to {{ end_date }}

---

## Executive Summary

{{ executive_summary }}

---

## Task Manager Summary

### Tasks Overview
- **Total Tasks**: {{ tasks.total }}
- **Completed**: {{ tasks.completed }} ({{ tasks.completion_rate }}%)
- **In Progress**: {{ tasks.in_progress }}
- **Overdue**: {{ tasks.overdue }} ⚠️
- **Pending**: {{ tasks.pending }}

### Priority Breakdown
| Priority | Count | Completed | Completion Rate |
|----------|-------|-----------|-----------------|
| High     | {{ tasks.by_priority.high.total }} | {{ tasks.by_priority.high.completed }} | {{ tasks.by_priority.high.rate }}% |
| Medium   | {{ tasks.by_priority.medium.total }} | {{ tasks.by_priority.medium.completed }} | {{ tasks.by_priority.medium.rate }}% |
| Low      | {{ tasks.by_priority.low.total }} | {{ tasks.by_priority.low.completed }} | {{ tasks.by_priority.low.rate }}% |

### Top Completed Tasks
{% for task in tasks.top_completed %}
- ✅ **{{ task.name }}** - {{ task.completed_at }}
{% endfor %}

### Overdue Tasks ⚠️
{% if tasks.overdue_list %}
{% for task in tasks.overdue_list %}
- ❌ **{{ task.name }}** - Due: {{ task.deadline }} ({{ task.overdue_days }} days overdue)
  - Priority: {{ task.priority }}
  - Assignee: {{ task.assignee }}
{% endfor %}
{% else %}
_No overdue tasks_ ✅
{% endif %}

---

## Workflow Automation Summary

### Workflow Executions
- **Total Executions**: {{ workflows.total }}
- **Successful**: {{ workflows.successful }} ({{ workflows.success_rate }}%)
- **Failed**: {{ workflows.failed }}
- **Running**: {{ workflows.running }}
- **Average Duration**: {{ workflows.avg_duration }}

### Workflow Performance
| Workflow Name | Executions | Success Rate | Avg Duration |
|---------------|------------|--------------|--------------|
{% for workflow in workflows.performance %}
| {{ workflow.name }} | {{ workflow.executions }} | {{ workflow.success_rate }}% | {{ workflow.avg_duration }} |
{% endfor %}

### Recent Workflow Executions
{% for execution in workflows.recent %}
- {% if execution.status == 'completed' %}✅{% elif execution.status == 'failed' %}❌{% else %}⏳{% endif %} **{{ execution.workflow_name }}** - {{ execution.started_at }}
  - Status: {{ execution.status }}
  - Duration: {{ execution.duration }}
{% endfor %}

---

## Anomalies Detected

{% if anomalies %}
{% for anomaly in anomalies %}
### {{ anomaly.type }} - {{ anomaly.severity }}
**Detected**: {{ anomaly.timestamp }}

{{ anomaly.description }}

**Recommendation**: {{ anomaly.recommendation }}

---
{% endfor %}
{% else %}
✅ No anomalies detected today.
{% endif %}

---

## Team Performance Metrics

### Productivity Trends
- **Tasks Created Today**: {{ metrics.tasks_created }}
- **Tasks Completed Today**: {{ metrics.tasks_completed }}
- **Workflows Executed Today**: {{ metrics.workflows_executed }}
- **Average Task Completion Time**: {{ metrics.avg_task_time }}

### Velocity
- **Today**: {{ metrics.velocity.today }} tasks
- **7-Day Average**: {{ metrics.velocity.week_avg }} tasks
- **Trend**: {{ metrics.velocity.trend }}

---

## AI Insights

{{ ai_insights }}

---

## Recommendations

{% for rec in recommendations %}
{{ loop.index }}. **{{ rec.title }}**  
   {{ rec.description }}
{% endfor %}

---

## Next Steps

{% for step in next_steps %}
- [ ] {{ step }}
{% endfor %}

---

**Report Footer**  
_Generated automatically by Reporting Agent AI Employee_  
_Next report: {{ next_report_date }}_
