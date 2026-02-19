# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.0.x   | ✅ Yes    |

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please **do NOT open a public GitHub issue**.

Instead, report it privately by emailing:
📧 **security@ai-employee-hackathon.dev**

### What to Include
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### What to Expect
- **Acknowledgement** within 48 hours
- **Status update** within 7 days
- **Fix or patch** within 30 days for confirmed vulnerabilities

## Security Best Practices for This Project

### Secrets & Credentials
- Never commit `.env` files to Git
- Rotate the default Grafana password (`hackathon123`) in production
- Use Kubernetes Secrets for sensitive values, never ConfigMaps

### Container Security
- All containers run as non-root users
- Images are built from official `python:3.11-slim` base
- No unnecessary capabilities granted

### Network Security
- Services communicate within the Kubernetes cluster only
- External access is only via port-forwarding (local dev) or Ingress (production)
- NGINX Ingress handles all inbound traffic

### Dependency Security
- Regularly update Python dependencies in `requirements.txt`
- Run `pip audit` to check for known vulnerabilities:
  ```bash
  pip install pip-audit
  pip-audit -r requirements.txt
  ```

## Disclosure Policy

This project follows responsible disclosure. We appreciate security researchers who report issues privately and give us time to fix them before public disclosure.
