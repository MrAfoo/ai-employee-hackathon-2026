# Weekly Report - Week {{ week_number }}, {{ year }}

**Generated**: {{ timestamp }}  
**Period**: {{ start_date }} to {{ end_date }}

---

## Executive Summary

{{ executive_summary }}

---

## Week at a Glance

### Key Metrics
| Metric | This Week | Last Week | Change |
|--------|-----------|-----------|--------|
| Tasks Completed | {{ metrics.tasks_completed.current }} | {{ metrics.tasks_completed.previous }} | {{ metrics.tasks_completed.change }} |
| Tasks Created | {{ metrics.tasks_created.current }} | {{ metrics.tasks_created.previous }} | {{ metrics.tasks_created.change }} |
| Workflows Executed | {{ metrics.workflows_executed.current }} | {{ metrics.workflows_executed.previous }} | {{ metrics.workflows_executed.change }} |
| Success Rate | {{ metrics.success_rate.current }}% | {{ metrics.success_rate.previous }}% | {{ metrics.success_rate.change }} |

---

## Task Manager Analysis

### Weekly Task Summary
- **Total Tasks**: {{ tasks.total }}
- **Completed**: {{ tasks.completed }} ({{ tasks.completion_rate }}%)
- **In Progress**: {{ tasks.in_progress }}
- **Overdue**: {{ tasks.overdue }}
- **Cancelled**: {{ tasks.cancelled }}

### Daily Breakdown
| Day | Created | Completed | Overdue |
|-----|---------|-----------|---------|
{% for day in tasks.daily_breakdown %}
| {{ day.date }} | {{ day.created }} | {{ day.completed }} | {{ day.overdue }} |
{% endfor %}

### Category Analysis
{% for category in tasks.by_category %}
- **{{ category.name }}**: {{ category.total }} tasks ({{ category.completion_rate }}% completed)
{% endfor %}

### Top Contributors
| Team Member | Tasks Completed | Completion Rate | Avg Time |
|-------------|-----------------|-----------------|----------|
{% for member in tasks.top_contributors %}
| {{ member.name }} | {{ member.completed }} | {{ member.rate }}% | {{ member.avg_time }} |
{% endfor %}

---

## Workflow Automation Analysis

### Weekly Workflow Summary
- **Total Executions**: {{ workflows.total }}
- **Success Rate**: {{ workflows.success_rate }}%
- **Failed Executions**: {{ workflows.failed }}
- **Total Duration**: {{ workflows.total_duration }}
- **Average Duration**: {{ workflows.avg_duration }}

### Workflow Performance Trends
{% for workflow in workflows.trends %}
#### {{ workflow.name }}
- Executions: {{ workflow.executions }}
- Success Rate: {{ workflow.success_rate }}%
- Trend: {{ workflow.trend }}
- Key Issues: {% if workflow.issues %}{{ workflow.issues }}{% else %}None{% endif %}

{% endfor %}

### Failed Workflows Analysis
{% if workflows.failures %}
| Workflow | Failed Count | Error Type | Last Failure |
|----------|--------------|------------|--------------|
{% for failure in workflows.failures %}
| {{ failure.name }} | {{ failure.count }} | {{ failure.error_type }} | {{ failure.last_failure }} |
{% endfor %}
{% else %}
✅ No workflow failures this week!
{% endif %}

---

## Anomalies and Alerts

### Critical Issues
{% if anomalies.critical %}
{% for anomaly in anomalies.critical %}
- 🔴 **{{ anomaly.title }}**  
  Detected: {{ anomaly.timestamp }}  
  Impact: {{ anomaly.impact }}  
  Status: {{ anomaly.status }}
{% endfor %}
{% else %}
✅ No critical issues detected.
{% endif %}

### Warnings
{% if anomalies.warnings %}
{% for warning in anomalies.warnings %}
- 🟡 **{{ warning.title }}**  
  {{ warning.description }}
{% endfor %}
{% else %}
✅ No warnings.
{% endif %}

### Patterns Detected
{% for pattern in patterns %}
- {{ pattern.description }}
  - Frequency: {{ pattern.frequency }}
  - Recommendation: {{ pattern.recommendation }}
{% endfor %}

---

## Performance Analysis

### System Health
- **Average Response Time**: {{ performance.avg_response_time }}
- **System Uptime**: {{ performance.uptime }}%
- **Error Rate**: {{ performance.error_rate }}%

### Productivity Trends
{{ productivity_chart }}

### Completion Rate Trends
{{ completion_rate_chart }}

---

## AI-Generated Insights

{{ ai_insights }}

### Key Observations
{% for observation in ai_observations %}
{{ loop.index }}. {{ observation }}
{% endfor %}

---

## Achievements This Week 🎉

{% for achievement in achievements %}
- ✨ **{{ achievement.title }}**  
  {{ achievement.description }}
{% endfor %}

---

## Challenges and Blockers

{% if challenges %}
{% for challenge in challenges %}
### {{ challenge.title }}
**Severity**: {{ challenge.severity }}  
**Description**: {{ challenge.description }}  
**Impact**: {{ challenge.impact }}  
**Recommended Action**: {{ challenge.recommendation }}

---
{% endfor %}
{% else %}
✅ No significant blockers reported this week.
{% endif %}

---

## Recommendations for Next Week

{% for rec in recommendations %}
{{ loop.index }}. **{{ rec.category }}**: {{ rec.description }}
   - Priority: {{ rec.priority }}
   - Expected Impact: {{ rec.impact }}
{% endfor %}

---

## Goals for Next Week

{% for goal in next_week_goals %}
- [ ] {{ goal }}
{% endfor %}

---

## Appendix

### Data Sources
- Task Manager API: {{ data_sources.task_manager }}
- Workflow Automation API: {{ data_sources.workflow_automation }}
- Analysis Period: {{ analysis_period }}

### Report Metadata
- Report Version: {{ report_version }}
- Generated By: Reporting Agent AI Employee
- Generation Time: {{ generation_time }}
- Next Weekly Report: {{ next_report_date }}

---

**Questions or feedback?** Contact your team administrator.
