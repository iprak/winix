---
name: Bug report
about: Create a report to help us improve
title: ''
labels: ''
assignees: ''

---

**Describe the bug**
 - A clear and concise description of what the bug is.
 - HomeAssistant and integration versions.
 - If applicable, add screenshots to help explain your problem.


**Expected behavior**
A clear and concise description of what you expected to happen.


**Debug log**
- Include debug mode logs for the integration or HomeAssistant (if applicable).
- You can enable debug logging for the integration from `Settings > Developer tools > Actions`. The integration log will include `[custom_components.winix]` in it.

```
action: logger.set_level
data:
  custom_components.winix: debug
```

**Additional context**
Add any other context about the problem here.
